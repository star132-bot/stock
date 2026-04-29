# Hermes Stock Sentinel Overview

## 项目定位

Hermes Stock Sentinel 是一个面向股农群体的单用户股票监控系统。

核心目标：

- 搜索股票
- 自动加入关注池
- 拉取实时行情
- 后端持续监控风险
- 在风险触发时把消息推送到微信用户
- 保存每次分析结果，用于复盘股票投资价值

## 当前主要功能

### 1. 搜索与关注

- 支持 A 股代码和名称搜索
- 支持裸代码输入，例如 `688766`
- 搜索命中后自动加入关注池
- 支持最近搜索记录

### 2. 实时行情

- 支持单只和关注池股票的实时行情刷新
- 当前主数据源为腾讯单股行情接口
- 支持后端 `/api/quotes`

### 3. Hermes 风险分析

- 动量分
- 流动性分
- 波动稳定度
- 收益保护分
- 市场态势判断
- 仅真实行情股票参与风险排行和投资判断

### 4. K线与量价分析

- 日线 K 线
- MA5 / MA10 / MA20 / MA60
- 成交量均线
- 支撑位 / 压力位
- 趋势标签
- 量价关系总结

### 5. 持仓逻辑与投资判断

- 持仓数量
- 成本价
- 止损位
- 目标位
- 持有周期
- 买入逻辑
- 输出继续持有 / 观察 / 减仓 / 卖出

### 6. 风险监控

- `/api/risk-summary`
- `/api/monitor/run-once`
- `/api/monitor/status`
- 告警去重
- 告警 cooldown

### 7. 告警发送

- 后端写入 `.runtime/outbox.json`
- 独立 sender 读取并发送
- 支持：
  - `serverchan`
  - `pushplus`
  - `wecom_bot`

### 8. 数据持久化

所有运行数据都保存在项目内 `.runtime/`：

- `watchlist.json`
- `monitor_config.json`
- `monitor_status.json`
- `alert_state.json`
- `outbox.json`
- `analysis_history.jsonl`
- `monitor_runs.jsonl`
- `a_stock_catalog.json`

### 9. 夜间总结

- `scripts/generate_nightly_summary.py`
- 输出目录：`docs/nightly_summaries/`
- 用于每天 21:00 生成复盘文档

## 数据价值沉淀

每次监控循环结束后，系统会保存：

- 最新行情快照
- 风险分析结果
- 市场态势
- 告警事件

这些数据可以用于：

- 复盘某只股票的风险变化
- 对照后续收益表现
- 分析股票投资价值
- 评估 Hermes 告警规则是否有效
