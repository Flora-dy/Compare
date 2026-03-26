from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

import competitor_filter_agent as agent


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "streamlit_data" / "competitors.json"

SEARCH_FIELDS = [
    "group_label",
    "category",
    "strain_name",
    "internal_id",
    "external_name",
    "source",
    "owner",
    "time_node",
    "remark",
]

DETAIL_FIELDS = [
    ("row_number", "行号"),
    ("group_label", "分组"),
    ("category", "类别"),
    ("strain_name", "菌株"),
    ("external_name", "外部编号"),
    ("internal_id", "内部编号"),
    ("source", "来源"),
    ("owner", "对接人"),
    ("time_node", "时间节点"),
    ("remark", "备注"),
    ("cell_count", "总菌体/活菌"),
    ("wgs", "WGS"),
    ("smell", "气味"),
    ("color", "色泽"),
    ("moisture", "水分"),
    ("lactose_ppm", "乳糖"),
]

TABLE_COLUMNS = [
    "row_number",
    "category",
    "strain_name",
    "external_name",
    "internal_id",
    "source",
    "owner",
    "time_node",
    "cell_count",
    "wgs",
    "moisture",
    "lactose_ppm",
]

TABLE_LABELS = {
    "row_number": "行号",
    "category": "类别",
    "strain_name": "菌株",
    "external_name": "外部编号",
    "internal_id": "内部编号",
    "source": "来源",
    "owner": "对接人",
    "time_node": "时间节点",
    "cell_count": "总菌体/活菌",
    "wgs": "WGS",
    "moisture": "水分",
    "lactose_ppm": "乳糖",
}


st.set_page_config(page_title="竞品数据库", page_icon="🔎", layout="wide")


@st.cache_data(show_spinner=False)
def load_payload() -> dict:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))

    workbook_path = agent.default_workbook_path()
    records = agent.load_records(workbook_path)
    return {"records": records}


def normalize_records(records: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for row in records:
        normalized.append({key: agent.clean_value(value) for key, value in row.items()})
    return normalized


def build_options(records: list[dict], field_name: str) -> list[str]:
    values = sorted(
        {
            agent.clean_value(record.get(field_name, ""))
            for record in records
            if agent.clean_value(record.get(field_name, "")) not in {"", "/"}
        },
        key=agent.group_sort_key,
    )
    return values


def search_records(records: list[dict], keyword: str) -> list[dict]:
    keyword = keyword.strip()
    if not keyword:
        return records
    token = agent.simplify(keyword)
    matched = []
    for record in records:
        haystack = " ".join(agent.clean_value(record.get(field, "")) for field in SEARCH_FIELDS)
        if token in agent.simplify(haystack):
            matched.append(record)
    return matched


def filter_exact(records: list[dict], field_name: str, value: str) -> list[dict]:
    if not value:
        return records
    return [record for record in records if agent.clean_value(record.get(field_name, "")) == value]


def render_detail(record: dict) -> None:
    st.subheader("详情")
    for field_name, label in DETAIL_FIELDS:
        value = agent.clean_value(record.get(field_name, ""))
        if not value:
            continue
        st.markdown(f"**{label}**")
        st.write(value)


payload = load_payload()
records = normalize_records(payload.get("records", []))

stats = payload.get("stats") or {
    "records": len(records),
    "groups": len({record["group_label"] for record in records if record["group_label"]}),
    "strains": len({record["strain_name"] for record in records if record["strain_name"]}),
    "sources": len({record["source"] for record in records if record["source"]}),
}

st.title("竞品数据库")
st.caption("输入关键词或用左侧字段筛选，直接找到对应竞品信息。")

top_col1, top_col2, top_col3, top_col4 = st.columns(4)
top_col1.metric("总记录", stats.get("records", 0))
top_col2.metric("分组", stats.get("groups", 0))
top_col3.metric("菌株", stats.get("strains", 0))
top_col4.metric("来源", stats.get("sources", 0))

keyword = st.text_input("搜索", placeholder="例如：阿克曼菌、HN019、M-16V、善恩康")

with st.sidebar:
    st.header("筛选")
    strain = st.selectbox("菌株", ["全部"] + build_options(records, "strain_name"))
    external_name = st.selectbox("外部编号", ["全部"] + build_options(records, "external_name"))
    source = st.selectbox("来源", ["全部"] + build_options(records, "source"))
    owner = st.selectbox("对接人", ["全部"] + build_options(records, "owner"))
    category = st.selectbox("类别", ["全部"] + build_options(records, "category"))
    group_label = st.selectbox("分组", ["全部"] + build_options(records, "group_label"))
    limit = st.slider("最多显示", min_value=10, max_value=200, value=50, step=10)

filtered = search_records(records, keyword)
filtered = filter_exact(filtered, "strain_name", "" if strain == "全部" else strain)
filtered = filter_exact(filtered, "external_name", "" if external_name == "全部" else external_name)
filtered = filter_exact(filtered, "source", "" if source == "全部" else source)
filtered = filter_exact(filtered, "owner", "" if owner == "全部" else owner)
filtered = filter_exact(filtered, "category", "" if category == "全部" else category)
filtered = filter_exact(filtered, "group_label", "" if group_label == "全部" else group_label)

st.markdown(f"### 结果列表")
st.caption(f"当前命中 {len(filtered)} 条")

left, right = st.columns([1.8, 1.1], gap="large")

with left:
    if filtered:
        table_rows = [{TABLE_LABELS[key]: row.get(key, "") for key in TABLE_COLUMNS} for row in filtered[:limit]]
        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        options = {
            f"{row.get('row_number', '')} | {row.get('external_name', '') or row.get('strain_name', '')} | {row.get('source', '')}": index
            for index, row in enumerate(filtered[:limit])
        }
        selected_label = st.selectbox("选择一条记录查看详情", list(options.keys()))
        selected_record = filtered[options[selected_label]]
    else:
        st.info("没有找到匹配记录。")
        selected_record = None

with right:
    if selected_record:
        render_detail(selected_record)
    else:
        st.write("先搜索或筛选出结果。")
