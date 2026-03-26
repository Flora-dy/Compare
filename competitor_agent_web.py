#!/usr/bin/env python3
"""竞品智能体网页服务。

启动后提供一个本地网页，用于：
1. 数据概览
2. 结构化筛选
3. 竞品 vs WK/CK 自动对比
4. 自然语言智能体入口
"""

from __future__ import annotations

import argparse
import json
import threading
from collections import Counter
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import competitor_filter_agent as agent


HTML_PATH = Path(__file__).resolve().with_name("competitor_agent_web.html")


class WorkbookStore:
    def __init__(self, workbook_path: Path) -> None:
        self.workbook_path = workbook_path
        self._lock = threading.Lock()
        self._records: list[dict[str, str | float | None]] = []
        self._mtime: float | None = None

    def get_records(self, force: bool = False) -> list[dict[str, str | float | None]]:
        current_mtime = self.workbook_path.stat().st_mtime
        with self._lock:
            if force or self._mtime != current_mtime or not self._records:
                self._records = agent.load_records(self.workbook_path)
                self._mtime = current_mtime
            return list(self._records)


def build_stats(records: list[dict[str, str | float | None]]) -> dict[str, int]:
    return {
        "records": len(records),
        "groups": len({agent.clean_value(record["group_label"]) for record in records if agent.clean_value(record["group_label"])}),
        "strains": len({agent.clean_value(record["strain_name"]) for record in records if agent.clean_value(record["strain_name"])}),
        "sources": len({agent.clean_value(record["source"]) for record in records if agent.clean_value(record["source"])}),
        "owners": len({agent.clean_value(record["owner"]) for record in records if agent.clean_value(record["owner"])}),
        "competitors": sum(1 for record in records if agent.is_competitor_record(record)),
        "internal_refs": sum(1 for record in records if agent.is_internal_record(record)),
    }


def build_options(records: list[dict[str, str | float | None]]) -> dict[str, list[str]]:
    def sorted_values(field_name: str) -> list[str]:
        values = {
            agent.clean_value(record[field_name])
            for record in records
            if agent.clean_value(record[field_name]) and agent.clean_value(record[field_name]) != "/"
        }
        return sorted(values, key=agent.group_sort_key)

    return {
        "strain_name": sorted_values("strain_name"),
        "source": sorted_values("source"),
        "owner": sorted_values("owner"),
        "category": sorted_values("category"),
        "group_label": sorted_values("group_label"),
        "external_name": sorted_values("external_name"),
    }


def serialize_records(records: list[dict[str, str | float | None]], limit: int) -> dict[str, Any]:
    columns = [{"field": field_name, "label": label} for field_name, label in agent.DISPLAY_COLUMNS]
    visible = records[:limit]
    rows = []
    for record in visible:
        row = {field_name: agent.clean_value(record[field_name]) for field_name, _ in agent.DISPLAY_COLUMNS}
        rows.append(row)
    return {"columns": columns, "rows": rows}


def payload_to_namespace(payload: dict[str, Any]) -> argparse.Namespace:
    return argparse.Namespace(
        query=payload.get("query"),
        strain=payload.get("strain"),
        source=payload.get("source"),
        owner=payload.get("owner"),
        category=payload.get("category"),
        group=payload.get("group"),
        external_name=payload.get("external_name"),
        date=payload.get("date"),
        keyword=payload.get("keyword"),
        metric=payload.get("metric"),
        op=payload.get("op"),
        value=payload.get("value"),
    )


def parse_request_payload(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def json_response(handler: BaseHTTPRequestHandler, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def text_response(handler: BaseHTTPRequestHandler, body: str, content_type: str = "text/html; charset=utf-8") -> None:
    data = body.encode("utf-8")
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)


def build_handler(store: WorkbookStore) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path == "/":
                text_response(self, HTML_PATH.read_text(encoding="utf-8"))
                return

            if parsed.path == "/api/summary":
                records = store.get_records()
                json_response(
                    self,
                    {
                        "mode": "summary",
                        "stats": build_stats(records),
                        "text": agent.summarize_records(records, store.workbook_path),
                        "workbook": str(store.workbook_path),
                    },
                )
                return

            if parsed.path == "/api/options":
                records = store.get_records()
                json_response(
                    self,
                    {
                        "mode": "options",
                        "options": build_options(records),
                    },
                )
                return

            json_response(self, {"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            try:
                payload = parse_request_payload(self)
                if parsed.path == "/api/refresh":
                    records = store.get_records(force=True)
                    json_response(
                        self,
                        {
                            "mode": "summary",
                            "stats": build_stats(records),
                            "text": agent.summarize_records(records, store.workbook_path),
                            "workbook": str(store.workbook_path),
                        },
                    )
                    return

                if parsed.path == "/api/filter":
                    records = store.get_records()
                    query = agent.build_query_from_args(payload_to_namespace(payload))
                    filtered = agent.filter_records(records, query)
                    result = {
                        "mode": "filter",
                        "parsed": agent.describe_query(query),
                        "count": len(filtered),
                        "text": agent.execute_filter(records, query, int(payload.get("limit", 20))),
                    }
                    result.update(serialize_records(filtered, int(payload.get("limit", 20))))
                    json_response(self, result)
                    return

                if parsed.path == "/api/compare":
                    records = store.get_records()
                    query_text = str(payload.get("query", "") or "").strip()
                    if query_text:
                        aliases = agent.build_dynamic_aliases(records)
                        query = agent.parse_query(query_text, aliases)
                    else:
                        query = agent.build_query_from_args(payload_to_namespace(payload))
                    matched = agent.filter_records(records, query) if agent.has_query_constraints(query) else records
                    groups = sorted(
                        {agent.clean_value(record["group_label"]) for record in matched if agent.clean_value(record["group_label"])},
                        key=agent.group_sort_key,
                    )
                    json_response(
                        self,
                        {
                            "mode": "compare",
                            "parsed": agent.describe_query(query),
                            "group_count": len(groups),
                            "groups": groups,
                            "text": agent.build_compare_report(
                                records,
                                query,
                                max_groups=int(payload.get("max_groups", 5)),
                                max_competitors=int(payload.get("max_competitors", 4)),
                                max_metrics=int(payload.get("max_metrics", 6)),
                            ),
                        },
                    )
                    return

                if parsed.path == "/api/agent":
                    records = store.get_records()
                    query_text = str(payload.get("query", "") or "").strip()
                    limit = int(payload.get("limit", 20))
                    max_groups = int(payload.get("max_groups", 5))
                    max_competitors = int(payload.get("max_competitors", 4))
                    max_metrics = int(payload.get("max_metrics", 6))
                    intent = agent.detect_intent(query_text)
                    response: dict[str, Any] = {
                        "mode": "agent",
                        "intent": intent,
                        "text": agent.execute_agent(
                            records,
                            store.workbook_path,
                            query_text,
                            limit=limit,
                            max_groups=max_groups,
                            max_competitors=max_competitors,
                            max_metrics=max_metrics,
                        ),
                    }
                    if intent == "filter":
                        aliases = agent.build_dynamic_aliases(records)
                        query = agent.parse_query(query_text, aliases)
                        filtered = agent.filter_records(records, query)
                        response["parsed"] = agent.describe_query(query)
                        response["count"] = len(filtered)
                        response.update(serialize_records(filtered, limit))
                    elif intent == "compare":
                        aliases = agent.build_dynamic_aliases(records)
                        query = agent.parse_query(query_text, aliases)
                        matched = agent.filter_records(records, query) if agent.has_query_constraints(query) else records
                        response["parsed"] = agent.describe_query(query)
                        response["group_count"] = len(
                            {agent.clean_value(record["group_label"]) for record in matched if agent.clean_value(record["group_label"])}
                        )
                    else:
                        response["stats"] = build_stats(records)
                    json_response(self, response)
                    return

                json_response(self, {"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            except Exception as exc:  # noqa: BLE001
                json_response(
                    self,
                    {
                        "error": str(exc),
                    },
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="竞品智能体网页服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    parser.add_argument(
        "--workbook",
        default=str(agent.default_workbook_path()),
        help="Excel 文件路径，默认优先读取脚本同目录下最新的竞品数据汇总表",
    )
    args = parser.parse_args()

    workbook_path = Path(args.workbook).expanduser().resolve()
    store = WorkbookStore(workbook_path)
    store.get_records()

    server = ThreadingHTTPServer((args.host, args.port), build_handler(store))
    print(f"竞品智能体网页已启动: http://{args.host}:{args.port}")
    print(f"工作簿: {workbook_path}")
    server.serve_forever()


if __name__ == "__main__":
    main()
