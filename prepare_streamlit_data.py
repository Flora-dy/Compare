#!/usr/bin/env python3
"""Export competitor records to JSON for Streamlit deployment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import competitor_filter_agent as agent


def main() -> int:
    parser = argparse.ArgumentParser(description="导出竞品 JSON 数据")
    parser.add_argument(
        "--workbook",
        default=str(agent.default_workbook_path()),
        help="Excel 文件路径",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parent / "streamlit_data" / "competitors.json"),
        help="输出 JSON 路径",
    )
    args = parser.parse_args()

    workbook_path = Path(args.workbook).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = agent.load_records(workbook_path)
    payload = {
        "records": records,
        "stats": {
            "records": len(records),
            "groups": len({agent.clean_value(record["group_label"]) for record in records if agent.clean_value(record["group_label"])}),
            "strains": len({agent.clean_value(record["strain_name"]) for record in records if agent.clean_value(record["strain_name"])}),
            "sources": len({agent.clean_value(record["source"]) for record in records if agent.clean_value(record["source"])}),
        },
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已导出 {len(records)} 条记录到 {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
