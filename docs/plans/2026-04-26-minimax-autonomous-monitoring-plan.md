# MiniMax Autonomous Monitoring Plan

目标：让 MiniMax 负责股票异动后的监控分析、告警文案生成、状态文档沉淀，以及下一轮分析建议输出。

## 方案定位

用户要求：
- 用 MiniMax 做监控分析
- 发现股票不对劲就开始警告
- 自动发送给用户
- 把当前股票状态写进文档
- 为下一次股票变动分析提供连续上下文

## 建议执行架构

### 1. 高频检测层
- 后端 `POST /api/monitor/run-once` 负责拉行情、生成基础风险信号、写入 `.runtime/outbox.json`
- 这一层负责“发现不对劲”
- 输出是结构化事件，而不是最终自然语言结论

### 2. MiniMax 分析层
- 定时任务读取：
  - `watchlist.json`
  - `alert_state.json`
  - `outbox.json`
  - 最近一次状态文档
- 对每个新事件由 MiniMax 生成：
  - 风险解释
  - 当前状态摘要
  - 下一次观察重点
  - 建议动作（观察/减仓/止损复核/等待确认）
  - 用户消息正文

### 3. 文档沉淀层
- 每次监控运行后，MiniMax 更新：
  - `docs/monitoring/current-stock-state.md`
- 文档内容应包含：
  - 更新时间
  - 每个标的当前风险等级
  - 最新异动
  - 本轮建议
  - 下一轮重点验证项
  - 与上一轮相比的变化

### 4. 消息发送层
- MiniMax 生成消息
- Hermes 负责投递到用户聊天渠道
- 发送成功后回写 outbox / monitoring doc

## 文档模板建议

每只股票建议记录：
- 股票代码 / 名称
- 最新价格 / 涨跌幅 / 量比 / 点差 / 波动率
- 当前风险等级
- 当前结论
- 本轮警报原因
- 上一轮到这一轮的变化
- 下一轮观察重点
- 建议动作

## 落地方式

推荐用 cron job，模型固定为 `MiniMax-M2.7-highspeed`：
1. 调用本地监控接口产生事件
2. 读取 runtime 状态
3. 用 MiniMax 生成分析和建议
4. 更新状态文档
5. 给用户发送消息

## 当前缺口

要真正启动，还缺两个必要配置：
1. 监控股票列表
2. 发送目标（当前聊天 / Feishu / Weixin）

## 下一步

在补齐股票列表和发送目标后：
- 写 MiniMax 监控执行 prompt
- 创建定时 cron job
- 增加 monitoring state doc 自动更新
- 验证首次告警与后续连续分析闭环
