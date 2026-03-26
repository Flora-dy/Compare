from __future__ import annotations

import json
from collections import Counter
from html import escape
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
    ("group_label", "分组"),
    ("category", "类别"),
    ("strain_name", "菌株"),
    ("external_name", "外部编号"),
    ("internal_id", "内部编号"),
    ("source", "来源"),
    ("owner", "对接人"),
    ("time_node", "时间节点"),
    ("remark", "备注"),
]

METRIC_FIELDS = [
    ("cell_count", "总菌体/活菌"),
    ("wgs", "WGS"),
    ("smell", "气味"),
    ("color", "色泽"),
    ("moisture", "水分"),
    ("lactose_ppm", "乳糖"),
]

TABLE_COLUMNS = [
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

SAMPLE_HINTS = ["阿克曼菌", "M-16V", "善恩康", "李瑞"]


st.set_page_config(page_title="竞品数据库", page_icon="🔎", layout="wide")


@st.cache_data(show_spinner=False)
def load_payload() -> dict:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))

    workbook_path = agent.default_workbook_path()
    records = agent.load_records(workbook_path)
    return {"records": records}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');

        :root {
          --bg-start: #f8f4ee;
          --bg-end: #eef3f1;
          --paper: rgba(255, 252, 247, 0.82);
          --paper-strong: rgba(255, 255, 255, 0.88);
          --ink: #243038;
          --muted: #6f7c84;
          --line: rgba(138, 160, 170, 0.18);
          --accent: #8bcfc2;
          --accent-soft: rgba(139, 207, 194, 0.18);
          --warm: #efb08c;
          --violet: #cbbce5;
          --shadow: 0 24px 54px rgba(119, 124, 136, 0.14);
          --radius: 22px;
        }

        .stApp {
          background:
            radial-gradient(circle at top left, rgba(203, 188, 229, 0.28), transparent 26%),
            radial-gradient(circle at top right, rgba(139, 207, 194, 0.24), transparent 22%),
            radial-gradient(circle at bottom right, rgba(239, 176, 140, 0.18), transparent 20%),
            linear-gradient(180deg, var(--bg-start), var(--bg-end));
          color: var(--ink);
          font-family: "Space Grotesk", "Noto Sans SC", sans-serif;
        }

        .block-container {
          padding-top: 1.4rem;
          padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
          background: rgba(247, 243, 237, 0.86);
          border-right: 1px solid rgba(138, 160, 170, 0.12);
          backdrop-filter: blur(18px);
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
          padding-top: 0.4rem;
        }

        h1, h2, h3 {
          color: var(--ink);
          letter-spacing: -0.03em;
        }

        .hero-shell {
          position: relative;
          overflow: hidden;
          margin-bottom: 1.1rem;
          padding: 1.6rem 1.7rem 1.5rem;
          border: 1px solid var(--line);
          border-radius: 28px;
          background:
            linear-gradient(140deg, rgba(255, 252, 247, 0.95), rgba(244, 240, 234, 0.86)),
            radial-gradient(circle at top right, rgba(139, 207, 194, 0.18), transparent 30%);
          box-shadow: var(--shadow);
          backdrop-filter: blur(18px);
        }

        .hero-shell::after {
          content: "";
          position: absolute;
          top: -36px;
          right: -52px;
          width: 180px;
          height: 180px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(203, 188, 229, 0.32), rgba(203, 188, 229, 0));
          filter: blur(4px);
        }

        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          padding: 0.42rem 0.8rem;
          border-radius: 999px;
          background: rgba(139, 207, 194, 0.18);
          border: 1px solid rgba(139, 207, 194, 0.22);
          color: var(--accent);
          font-size: 0.76rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .hero-title {
          margin: 0.9rem 0 0.4rem;
          font-family: "Space Grotesk", "Noto Sans SC", sans-serif;
          font-size: clamp(2rem, 3vw, 3.3rem);
          line-height: 1.06;
          text-transform: none;
        }

        .hero-copy {
          max-width: 760px;
          color: var(--muted);
          font-size: 0.98rem;
          line-height: 1.72;
        }

        .metric-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 0.9rem;
          margin: 1rem 0 0.3rem;
        }

        .metric-card {
          padding: 1rem 1rem 0.95rem;
          border: 1px solid var(--line);
          border-radius: 18px;
          background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(246, 241, 236, 0.82));
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.55);
        }

        .metric-label {
          color: var(--muted);
          font-size: 0.8rem;
        }

        .metric-value {
          margin-top: 0.35rem;
          font-size: 1.9rem;
          font-weight: 700;
          letter-spacing: -0.05em;
          color: var(--ink);
        }

        .panel-shell {
          padding: 1rem 1.05rem 1.05rem;
          border: 1px solid var(--line);
          border-radius: var(--radius);
          background: var(--paper);
          box-shadow: var(--shadow);
          backdrop-filter: blur(16px);
        }

        .section-kicker {
          color: var(--warm);
          font-size: 0.78rem;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .section-title {
          margin: 0.35rem 0 0.15rem;
          font-size: 1.22rem;
          font-weight: 700;
        }

        .section-copy {
          color: var(--muted);
          font-size: 0.9rem;
          line-height: 1.62;
        }

        .summary-bar {
          margin: 0.8rem 0 0.25rem;
          padding: 0.85rem 1rem;
          border-radius: 16px;
          background: linear-gradient(135deg, rgba(139, 207, 194, 0.18), rgba(203, 188, 229, 0.16));
          border: 1px solid rgba(139, 207, 194, 0.16);
          color: #35504c;
          font-size: 0.92rem;
          font-weight: 600;
        }

        .filter-note {
          margin-top: 0.8rem;
          padding: 0.8rem 0.9rem;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.52);
          border: 1px solid rgba(138, 160, 170, 0.12);
          color: var(--muted);
          font-size: 0.84rem;
          line-height: 1.65;
        }

        .chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 0.45rem;
          margin-top: 0.75rem;
        }

        .chip {
          display: inline-flex;
          align-items: center;
          padding: 0.4rem 0.72rem;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.72);
          border: 1px solid var(--line);
          color: #35504c;
          font-size: 0.76rem;
        }

        .record-card {
          padding: 1rem 1.05rem;
          border: 1px solid var(--line);
          border-radius: 18px;
          background: var(--paper-strong);
          margin-bottom: 0.8rem;
          box-shadow: inset 0 1px 0 rgba(255,255,255,0.68);
        }

        .record-title {
          margin: 0.55rem 0 0.35rem;
          font-size: 1.08rem;
          font-weight: 700;
          line-height: 1.45;
        }

        .record-meta,
        .detail-grid {
          display: grid;
          gap: 0.5rem;
        }

        .record-meta {
          grid-template-columns: repeat(2, minmax(0, 1fr));
          margin-top: 0.75rem;
        }

        .meta-item,
        .detail-item {
          padding: 0.72rem 0.82rem;
          border-radius: 14px;
          background: rgba(247, 243, 237, 0.82);
          border: 1px solid rgba(138, 160, 170, 0.10);
        }

        .meta-label,
        .detail-label {
          color: var(--muted);
          font-size: 0.74rem;
        }

        .meta-value,
        .detail-value {
          margin-top: 0.18rem;
          font-size: 0.92rem;
          font-weight: 600;
          overflow-wrap: anywhere;
        }

        .detail-card {
          padding: 1.1rem 1.15rem;
          border: 1px solid var(--line);
          border-radius: 22px;
          background:
            linear-gradient(180deg, rgba(255,255,255,0.94), rgba(244, 239, 233, 0.90)),
            radial-gradient(circle at top right, rgba(203, 188, 229, 0.16), transparent 26%);
        }

        .detail-title {
          margin: 0.6rem 0 0.3rem;
          font-size: 1.3rem;
          font-weight: 700;
          line-height: 1.4;
        }

        .detail-grid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
          margin-top: 0.8rem;
        }

        .empty-card {
          padding: 1.2rem;
          border: 1px dashed rgba(31, 40, 35, 0.18);
          border-radius: 18px;
          background: rgba(255,255,255,0.55);
          color: var(--muted);
          line-height: 1.7;
        }

        .stTextInput label,
        .stSelectbox label,
        .stSlider label {
          font-weight: 600 !important;
        }

        .stTextInput input,
        .stSelectbox [data-baseweb="select"] > div,
        .stSlider {
          border-radius: 14px !important;
        }

        .stTextInput input {
          background: rgba(250, 247, 242, 0.96) !important;
          color: #1c2430 !important;
          caret-color: #1c2430 !important;
          border: 1px solid rgba(180, 196, 214, 0.20) !important;
          -webkit-text-fill-color: #1c2430 !important;
        }

        .stSelectbox [data-baseweb="select"] > div {
          background: rgba(250, 247, 242, 0.94) !important;
          border: 1px solid rgba(180, 196, 214, 0.18) !important;
          color: #1c2430 !important;
        }

        .stSelectbox [data-baseweb="select"] * {
          color: #1c2430 !important;
        }

        .stTextInput input::placeholder {
          color: #758091 !important;
          -webkit-text-fill-color: #758091 !important;
        }

        .stButton > button {
          border-radius: 14px !important;
          border: 1px solid rgba(139, 207, 194, 0.20) !important;
          background: linear-gradient(135deg, #a9ddd3, #d2c5ea) !important;
          color: #18202a !important;
          font-weight: 600 !important;
          box-shadow: 0 10px 24px rgba(183, 188, 201, 0.20) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.4rem;
        }

        .stTabs [data-baseweb="tab"] {
          height: 40px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.68);
          padding: 0 1rem;
        }

        .sample-hint {
          margin: 0.35rem 0 0.75rem;
          color: var(--muted);
          font-size: 0.84rem;
          line-height: 1.7;
        }

        @media (max-width: 900px) {
          .metric-grid,
          .record-meta,
          .detail-grid {
            grid-template-columns: 1fr 1fr;
          }
        }

        @media (max-width: 640px) {
          .metric-grid,
          .record-meta,
          .detail-grid {
            grid-template-columns: 1fr;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


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


def render_metric_cards(stats: dict) -> None:
    cards = [
        ("总记录", stats.get("records", 0)),
        ("分组", stats.get("groups", 0)),
        ("菌株", stats.get("strains", 0)),
        ("来源", stats.get("sources", 0)),
    ]
    html = '<div class="metric-grid">'
    for label, value in cards:
        html += (
            '<div class="metric-card">'
            f'<div class="metric-label">{escape(str(label))}</div>'
            f'<div class="metric-value">{escape(str(value))}</div>'
            "</div>"
        )
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_hero(stats: dict) -> None:
    st.markdown(
        """
        <div class="hero-shell">
          <div class="hero-badge">Competitor Database</div>
          <div class="hero-title">竞品数据库</div>
          <div class="hero-copy">
            这是一个面向业务展示的竞品检索站点。你可以直接搜索菌株、外部编号、来源或对接人，
            快速定位具体竞品，再在右侧查看单条详情与关键指标。
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metric_cards(stats)


def render_summary_bar(filtered: list[dict], keyword: str) -> None:
    strains = Counter(row["strain_name"] for row in filtered if row.get("strain_name"))
    sources = Counter(row["source"] for row in filtered if row.get("source"))
    top_strains = "、".join(name for name, _ in strains.most_common(3)) or "无"
    top_sources = "、".join(name for name, _ in sources.most_common(3)) or "无"
    text = f"当前命中 {len(filtered)} 条"
    if keyword:
        text += f"｜关键词：{keyword}"
    text += f"｜高频菌株：{top_strains}｜高频来源：{top_sources}"
    st.markdown(f'<div class="summary-bar">{escape(text)}</div>', unsafe_allow_html=True)


def render_active_filters(filters: list[str]) -> None:
    if not filters:
        return
    chips = "".join(f'<span class="chip">{escape(item)}</span>' for item in filters)
    st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)


def record_option_label(record: dict) -> str:
    core = record.get("external_name") or record.get("strain_name") or "未命名样品"
    source = record.get("source") or "-"
    return f"{core} | {source}"


def record_card_html(record: dict) -> str:
    chips = []
    for key in ("category", "group_label", "source"):
        value = record.get(key, "")
        if value:
            chips.append(f'<span class="chip">{escape(value)}</span>')

    meta_items = []
    for field_name, label in [
        ("strain_name", "菌株"),
        ("external_name", "外部编号"),
        ("owner", "对接人"),
        ("time_node", "时间节点"),
    ]:
        value = record.get(field_name, "")
        if value:
            meta_items.append(
                '<div class="meta-item">'
                f'<div class="meta-label">{escape(label)}</div>'
                f'<div class="meta-value">{escape(value)}</div>'
                "</div>"
            )

    title = record.get("external_name") or record.get("internal_id") or record.get("strain_name") or "未命名样品"
    subtitle = " / ".join(
        value
        for value in [record.get("strain_name", ""), record.get("source", ""), record.get("owner", "")]
        if value
    )

    return (
        '<div class="record-card">'
        f'<div class="chip-row">{"".join(chips)}</div>'
        f'<div class="record-title">{escape(title)}</div>'
        f'<div class="section-copy">{escape(subtitle or "暂无更多标签信息")}</div>'
        f'<div class="record-meta">{"".join(meta_items)}</div>'
        "</div>"
    )


def render_detail(record: dict | None) -> None:
    st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Record Detail</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">竞品详情</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">聚焦展示这一条记录最关键的信息和指标。</div>', unsafe_allow_html=True)

    if not record:
        st.markdown('<div class="empty-card">先从左侧结果里选择一条记录，再在这里查看详情。</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    chips = []
    for key in ("category", "group_label", "source"):
        value = record.get(key, "")
        if value:
            chips.append(f'<span class="chip">{escape(value)}</span>')

    detail_items = []
    for field_name, label in DETAIL_FIELDS + METRIC_FIELDS:
        value = record.get(field_name, "")
        if not value:
            continue
        detail_items.append(
            '<div class="detail-item">'
            f'<div class="detail-label">{escape(label)}</div>'
            f'<div class="detail-value">{escape(value)}</div>'
            "</div>"
        )

    title = record.get("external_name") or record.get("internal_id") or record.get("strain_name") or "未命名样品"
    st.markdown(f'<div class="chip-row">{"".join(chips)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="detail-title">{escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="detail-grid">{"".join(detail_items)}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


inject_styles()

payload = load_payload()
records = normalize_records(payload.get("records", []))

stats = payload.get("stats") or {
    "records": len(records),
    "groups": len({record["group_label"] for record in records if record["group_label"]}),
    "strains": len({record["strain_name"] for record in records if record["strain_name"]}),
    "sources": len({record["source"] for record in records if record["source"]}),
}

if "keyword" not in st.session_state:
    st.session_state.keyword = ""

render_hero(stats)

st.markdown(
    f'<div class="sample-hint">可试搜：{" / ".join(SAMPLE_HINTS)}</div>',
    unsafe_allow_html=True,
)

keyword = st.text_input(
    "搜索关键词",
    key="keyword",
    placeholder="例如：阿克曼菌、M-16V、善恩康、李瑞",
)

with st.sidebar:
    st.markdown("## 筛选")
    st.markdown("缩小结果范围，只保留你现在想看的竞品。")
    strain = st.selectbox("菌株", ["全部"] + build_options(records, "strain_name"))
    external_name = st.selectbox("外部编号", ["全部"] + build_options(records, "external_name"))
    source = st.selectbox("来源", ["全部"] + build_options(records, "source"))
    owner = st.selectbox("对接人", ["全部"] + build_options(records, "owner"))
    category = st.selectbox("类别", ["全部"] + build_options(records, "category"))
    group_label = st.selectbox("分组", ["全部"] + build_options(records, "group_label"))
    limit = st.slider("最多显示", min_value=12, max_value=120, value=36, step=12)
    st.markdown(
        """
        <div class="filter-note">
          视觉上优先展示“搜索 + 结果 + 详情”。如果结果太多，先限定来源、菌株或外部编号，阅读会更清楚。
        </div>
        """,
        unsafe_allow_html=True,
    )

filtered = search_records(records, keyword)
filtered = filter_exact(filtered, "strain_name", "" if strain == "全部" else strain)
filtered = filter_exact(filtered, "external_name", "" if external_name == "全部" else external_name)
filtered = filter_exact(filtered, "source", "" if source == "全部" else source)
filtered = filter_exact(filtered, "owner", "" if owner == "全部" else owner)
filtered = filter_exact(filtered, "category", "" if category == "全部" else category)
filtered = filter_exact(filtered, "group_label", "" if group_label == "全部" else group_label)

active_filters = []
for label, value in [
    ("搜索", keyword.strip()),
    ("菌株", "" if strain == "全部" else strain),
    ("外部编号", "" if external_name == "全部" else external_name),
    ("来源", "" if source == "全部" else source),
    ("对接人", "" if owner == "全部" else owner),
    ("类别", "" if category == "全部" else category),
    ("分组", "" if group_label == "全部" else group_label),
]:
    if value:
        active_filters.append(f"{label}: {value}")

left, right = st.columns([1.75, 1.05], gap="large")

with left:
    st.markdown('<div class="panel-shell">', unsafe_allow_html=True)
    st.markdown('<div class="section-kicker">Search Result</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">结果列表</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">先看整体，再决定点开哪一条竞品详情。</div>', unsafe_allow_html=True)

    render_summary_bar(filtered, keyword.strip())
    render_active_filters(active_filters)

    if filtered:
        visible_records = filtered[:limit]
        options = {record_option_label(record): index for index, record in enumerate(visible_records)}
        selected_label = st.selectbox("当前查看", list(options.keys()), label_visibility="collapsed")
        selected_record = visible_records[options[selected_label]]

        cards_tab, table_tab = st.tabs(["卡片视图", "表格视图"])

        with cards_tab:
            for record in visible_records[:12]:
                st.markdown(record_card_html(record), unsafe_allow_html=True)

        with table_tab:
            table_rows = [{TABLE_LABELS[key]: row.get(key, "") for key in TABLE_COLUMNS} for row in visible_records]
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        selected_record = None
        st.markdown(
            '<div class="empty-card">没有找到匹配记录。建议换一个关键词，或者放宽左侧筛选条件。</div>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    render_detail(selected_record)
