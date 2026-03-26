# 竞品智能体原型

这个原型默认优先读取同目录下的 [竞品数据汇总表V36.xlsx](/Users/zzp/Code/Compare/竞品数据汇总表V36.xlsx)，并自动识别汇总页和表头，已经支持：

- 竞品信息搜索
- 数据概览
- 结构化筛选
- 自然语言提问
- `竞品 vs WK/CK` 自动对比
- 本地网页交互

## CLI 运行方式

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py summary
```

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py ask "找出阿克曼菌，来源善恩康，2026年2月送检的竞品"
```

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py compare --query "对比植物乳植杆菌竞品和微康"
```

```bash
python3 /Users/zzp/Code/Compare/competitor_filter_agent.py list --strain "短双歧杆菌" --source "飞鹤"
```

## 网页运行方式

```bash
python3 /Users/zzp/Code/Compare/competitor_agent_web.py --host 127.0.0.1 --port 8765
```

启动后在浏览器打开 `http://127.0.0.1:8765`。

## 当前能力

- `summary`: 输出总记录数、菌株分布、来源分布、字段覆盖率。
- `list`: 结构化筛选，适合精确查询。
- `compare`: 自动按分组对比竞品和内部参考，输出可比指标结论。
- `ask` / `agent`: 智能体入口，会自动识别是概览、筛选还是对比任务。
- `competitor_agent_web.py`: 本地网页服务，页面里可以直接操作上面几种能力。

## 已支持的典型问法

- `找出阿克曼菌，来源善恩康，2026年2月送检的竞品`
- `HN019`
- `M-16V`
- `对比植物乳植杆菌竞品和微康`
- `对比 2 组的飞鹤 B06 和 WK`
- `短双歧杆菌 飞鹤`
- `WGS > 0.99 的竞品`
- `乳糖 < 5 的阿克曼菌`

## 现阶段限制

- 当前只解析汇总页，还没有联动其他明细页。
- 时间字段是半结构化文本，像 `202507前`、`2025/12/14前出` 这类会做尽量匹配，但还不是严格日期模型。
- 总菌体数、稳定性等字段里混有文本和数值，自动对比会尽量抽取首个有效数值，但仍然不能完全替代人工判断。
- 目前网页是本地服务，不带登录、多用户和持久化。

## 下一步适合扩展的方向

- 联动明细页，输出单个菌株的检测进度和缺失项。
- 增加导出功能，把筛选结果导出成 CSV。
- 增加“结论卡片”，把对比结果提炼成适合周报的摘要。
