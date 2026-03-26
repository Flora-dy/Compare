# 竞品对比智能体

基于 [竞品数据汇总表V36.xlsx](/Users/zzp/Code/Compare/竞品数据汇总表V36.xlsx) 的本地竞品分析工具，支持：

- 竞品信息搜索
- 数据概览
- 结构化筛选
- 自然语言问答
- `竞品 vs WK/CK/SC` 自动对比
- 本地网页交互

当前实现会自动识别汇总页和表头，适合做竞品检索、样品筛选、分组对比和阶段性汇报。

## 目录结构

```text
Compare/
├── README.md
├── competitor_filter_agent.py
├── competitor_agent_web.py
├── competitor_agent_web.html
├── prepare_streamlit_data.py
├── requirements.txt
├── streamlit_app.py
├── streamlit_data/competitors.json
└── 竞品数据汇总表V36.xlsx
```

## 核心能力

### 1. 数据概览

读取 Excel 汇总页后，输出：

- 总记录数
- 分组数
- 菌株数
- 来源方数
- 对接人数
- 类别分布
- 高频菌株
- 高频来源方
- 关键字段覆盖率

### 2. 结构化筛选

支持按以下条件筛选：

- 菌株
- 外部编号/名称
- 来源方
- 对接人
- 类别
- 分组
- 时间节点
- 关键词
- 数值阈值，如 `WGS > 0.99`、`乳糖 < 5`

### 3. 自动对比

脚本会按 `group_label` 自动组装对比单元，把同组中的：

- `竞品`
- `WK`
- `CK1 ~ CK6`
- `SC`

视作同一对比组，自动输出：

- 内部参考样本
- 竞品样本
- 可比较指标
- 竞品占优 / 内部占优 / 持平
- 信息不足说明

### 4. 智能体入口

输入一句自然语言，系统会自动识别任务类型：

- 概览：如 `概览一下这份竞品表`
- 筛选：如 `找出阿克曼菌，来源善恩康，2026年2月送检的竞品`
- 对比：如 `对比植物乳植杆菌竞品和微康`

## 环境要求

- Python 3.10+
- `openpyxl`

如果本机还没安装依赖：

```bash
python3 -m pip install openpyxl
```

## CLI 用法

### 1. 查看概览

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py summary
```

### 2. 结构化筛选

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py list \
  --strain "短双歧杆菌" \
  --source "飞鹤"
```

带数值条件的筛选：

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py list \
  --category "竞品" \
  --metric "WGS" \
  --op ">" \
  --value 0.99
```

### 3. 自动对比

按自然语言对比：

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py compare \
  --query "对比植物乳植杆菌竞品和微康"
```

按分组精确对比：

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py compare \
  --group 2
```

### 4. 智能体入口

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py ask \
  "找出阿克曼菌，来源善恩康，2026年2月送检的竞品"
```

或：

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py agent \
  "对比植物乳植杆菌竞品和微康"
```

## 网页用法

启动本地服务：

```bash
python3 /Users/zzp/Code/Compare/competitor_agent_web.py --host 127.0.0.1 --port 8765
```

然后在浏览器打开：

[http://127.0.0.1:8765](http://127.0.0.1:8765)

网页包含三个主要区域：

- 顶部搜索框：直接搜菌株、外部编号、来源或一句话问题
- 结构化筛选区：适合精确查数
- 分组对比区：适合拉竞品 vs 内部参考结论

## Streamlit 部署

如果你要发布到公网，推荐直接用 `GitHub + Streamlit Community Cloud`。

### 1. 本地生成部署数据

```bash
python3 /Users/zzp/Code/Compare/prepare_streamlit_data.py
```

这一步会把 Excel 转成 `streamlit_data/competitors.json`，部署时优先读取这个 JSON，不依赖本地 Excel 路径。

### 2. 本地预览 Streamlit

```bash
streamlit run /Users/zzp/Code/Compare/streamlit_app.py
```

### 3. 推到 GitHub

建议把 `Compare/` 目录单独放进一个仓库。仓库里至少保留这些文件：

- `streamlit_app.py`
- `competitor_filter_agent.py`
- `prepare_streamlit_data.py`
- `requirements.txt`
- `streamlit_data/competitors.json`

### 4. 在 Streamlit Community Cloud 发布

1. 登录 [Streamlit Community Cloud](https://share.streamlit.io/)
2. 连接 GitHub 仓库
3. 选择仓库、分支和入口文件 `streamlit_app.py`
4. 点击 Deploy

官方文档：

- [Connect your GitHub account](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/connect-your-github-account)

## 已支持的典型问题

- `HN019`
- `M-16V`
- `找出阿克曼菌，来源善恩康，2026年2月送检的竞品`
- `WGS > 0.99 的竞品`
- `乳糖 < 5 的阿克曼菌`
- `对比植物乳植杆菌竞品和微康`
- `对比 2 组的飞鹤 B06 和 WK`
- `概览一下这份竞品表`

## API 说明

网页服务启动后，提供以下本地接口：

### `GET /api/summary`

返回全表概览。

### `GET /api/options`

返回筛选表单可用选项。

### `POST /api/filter`

按结构化条件筛选。

示例：

```json
{
  "strain": "短双歧杆菌",
  "source": "飞鹤",
  "limit": 10
}
```

### `POST /api/compare`

生成竞品 vs 内部参考对比报告。

示例：

```json
{
  "query": "对比植物乳植杆菌竞品和微康",
  "max_groups": 3,
  "max_competitors": 4,
  "max_metrics": 6
}
```

### `POST /api/agent`

智能体统一入口，自动识别任务类型。

示例：

```json
{
  "query": "找出阿克曼菌，来源善恩康，2026年2月送检的竞品",
  "limit": 20,
  "max_groups": 5,
  "max_competitors": 4,
  "max_metrics": 6
}
```

## 当前规则说明

### 对比逻辑

- 优先使用同组中的 `WK` 作为内部参考
- 如果没有 `WK`，则回退到 `CK / SC`
- 仅对有可提取数值的字段做自动判断
- `水分`、`水活`、`乳糖` 默认按“越低越优”
- `总菌体/活菌`、`WGS`、感官分、稳定性默认按“越高越优”

### 当前处理方式

- `11000`
- `0.997`
- `2700亿TFU/g`
- `2300-100%`

这类字符串会尽量抽取首个有效数值做比较。

## 当前限制

- 当前只解析 `00 数据汇总表`，还没有联动 5 张明细页
- 时间字段是半结构化文本，暂不是严格日期模型
- 部分字段混合文本和数字，自动比较结果仍需要人工复核
- 本地网页是单用户本地服务，不带登录、权限和持久化

## 后续建议

- 接入 5 张明细页，补齐检测进度和缺失项
- 增加 CSV / Excel 导出
- 把对比结果整理成“汇报卡片”或“周报摘要”
- 加入结论打分，支持优先级排序

## 相关文件

- 智能体核心脚本：[competitor_filter_agent.py](/Users/zzp/Code/Compare/competitor_filter_agent.py)
- 网页服务：[competitor_agent_web.py](/Users/zzp/Code/Compare/competitor_agent_web.py)
- 网页界面：[competitor_agent_web.html](/Users/zzp/Code/Compare/competitor_agent_web.html)
- 原始数据：[竞品数据汇总表0305.xlsx](/Users/zzp/Code/Compare/竞品数据汇总表0305.xlsx)
