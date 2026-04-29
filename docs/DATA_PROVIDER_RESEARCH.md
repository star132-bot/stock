# 实时股票数据源调研

> 核对时间：2026-04-19
> 主要参考官方文档：Massive / Polygon、Alpaca、Tushare

## 1. 目标

这个项目的目标不是“随便接一个行情接口”，而是为专业用户建立一个可长期使用的实时监控网页。

因此数据源必须从以下几个角度评估：

- 是否真正支持实时或准实时
- 是否支持 WebSocket
- 是否支持多标的持续订阅
- 是否能拿到成交、报价、K线、快照
- 是否适合商用
- 是否有清晰的权限和价格结构

## 2. 结论先行

### 如果目标是美股专业实时监控

优先建议：

1. `Polygon / Massive`
2. `Alpaca Market Data`

### 如果目标是 A 股研究和原型验证

可以先用：

1. `Tushare realtime_quote`

但不建议直接把它作为正式商用实时主数据源。

## 3. 数据源调研

### 3.1 Polygon / Massive

官方文档显示，股票 WebSocket 支持：

- 实时 trades
- 实时 quotes
- 每分钟 bars
- 每秒 bars
- LULD
- FMV

官方文档还明确提到其实时流适合：

- live dashboards
- algorithmic trading strategies
- real-time risk management

参考：

- Massive / Polygon Stocks WebSocket Overview  
  https://massive.com/docs/websocket/stocks/overview
- Massive / Polygon Unified Snapshot  
  https://massive.com/docs/rest/stocks/snapshots/unified-snapshot
- Polygon Stocks Pricing  
  https://polygon.io/stocks

关键点：

- `WebSocket` 非常适合实时监控网页
- `Snapshot + WebSocket` 组合很适合页面初始化和增量刷新
- 文档里列出了 `Trades / Quotes / Aggregates / LULD / FMV`
- Snapshot 端点可以一次获取多个标的当前状态

注意：

- 官方定价页显示，不同套餐的数据实时性不同
- 文档里可以看到一些低阶套餐是 `15-minute delayed`
- 真正实时的美股数据要用更高等级套餐

### 3.2 Alpaca Market Data

Alpaca 官方文档明确说明：

- 股票实时数据通过 `WebSocket` 提供
- URL 是 `wss://stream.data.alpaca.markets/{version}/{feed}`
- 支持 `v2/sip`
- 支持 `v2/iex`
- 支持 `v2/delayed_sip`
- 支持 trades、quotes、bars、dailyBars、updatedBars

参考：

- Alpaca Real-time Stock Data  
  https://docs.alpaca.markets/docs/real-time-stock-pricing-data
- Alpaca Data Pricing  
  https://alpaca.markets/data

关键点：

- 非常适合做实时查询网页
- 订阅模型清晰
- WebSocket 数据结构规范
- 适合把 `报价 + 成交 + K线` 做成一个标准前端数据层

注意：

- 不同 feed 对应不同实时性和覆盖范围
- 需要根据订阅等级决定用 `SIP`、`IEX` 还是 `delayed_sip`

### 3.3 Tushare

Tushare 官方文档里 `realtime_quote` 明确写到：

- 这是 A 股实时行情接口
- 数据来自网络
- 不进入 tushare 服务器
- `属于爬虫接口`
- `tushare 不对数据内容和质量负责`
- 主要用于研究和学习使用
- 商业用途要自行解决合规问题

参考：

- Tushare 实时盘口 TICK 快照  
  https://tushare.pro/document/2?doc_id=315

关键点：

- 对 A 股研究原型很方便
- 获取门槛低
- 适合先搭建监控页和验证字段结构

注意：

- 不是严格意义上的专业商用实时主数据源
- 稳定性、合规性、商业使用边界都需要额外评估

## 4. 推荐接入策略

### 4.1 MVP 阶段

如果先做页面和监控逻辑：

- 美股：优先 `Alpaca` 或 `Polygon`
- A股：原型可先接 `Tushare`

### 4.2 生产阶段

如果是专业交易/研究使用：

- 美股：建议 `WebSocket 主流 + Snapshot 初始化`
- A股：建议使用有明确商用授权和稳定 SLA 的数据供应商

## 5. 推荐架构

### 初始化阶段

页面打开时：

- 用 Snapshot 拉取观察池当前价格、涨跌幅、成交量、开高低收

### 实时阶段

页面运行中：

- 用 WebSocket 推送 trades / quotes / minute bars
- 前端只接收后端处理后的标准化事件

### 回补阶段

网络中断或切换页面时：

- 使用 REST snapshot 做状态回补

## 6. 数据层建议

统一标准化字段：

- symbol
- market
- last_price
- bid_1
- ask_1
- spread_bps
- change_pct
- open
- high
- low
- prev_close
- volume
- turnover
- minute_bar
- trade_timestamp
- quote_timestamp

不要让前端直接依赖不同供应商的原始字段名。

## 7. 最终建议

### 如果你现在要最快启动

- 页面原型先做静态版
- 美股先接 `Alpaca` 或 `Polygon`
- A股原型先接 `Tushare`

### 如果你要做专业化可用产品

- 后端做统一市场数据网关
- 前端只消费标准化行情对象
- `Snapshot + WebSocket + 本地缓存` 必须同时具备

## 8. 推荐决策

如果这个股票网页的第一目标用户是专业美股交易/研究用户：

- 优先选 `Polygon / Massive`

如果第一目标是成本更可控、开发更快：

- 优先选 `Alpaca`

如果第一目标是 A 股原型验证：

- 先选 `Tushare`

但正式商用时，不建议把爬虫型接口作为最终核心生产数据源。
