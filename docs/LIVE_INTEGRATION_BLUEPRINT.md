# 实时接入蓝图

## 1. 目标

这个项目的专业版本，不应该让前端直接连接第三方行情商。

正确做法是：

- 前端只连接你自己的市场数据网关
- 网关再连接 Polygon / Alpaca / Tushare 等供应商
- 网关统一输出标准化行情对象和分析结果

这样做的原因：

- 不暴露供应商 API Key
- 不让前端依赖不同供应商的字段命名
- 便于后续切换供应商
- 便于统一风控、缓存、告警和分析

## 2. 推荐接口形态

### REST

页面初始化：

- `GET /api/market/snapshot?symbols=AAPL,NVDA,TSLA`

返回：

```json
{
  "provider": "polygon",
  "as_of": "2026-04-19T10:15:00Z",
  "data": [
    {
      "symbol": "AAPL",
      "market": "US",
      "last_price": 212.48,
      "change_pct": 1.34,
      "open": 210.22,
      "high": 213.14,
      "low": 209.8,
      "prev_close": 209.67,
      "volume": 68420012,
      "turnover": 14530000000,
      "bid": 212.45,
      "ask": 212.49,
      "spread_bps": 1.88,
      "ts_event": "2026-04-19T10:14:59Z"
    }
  ]
}
```

### WebSocket

页面运行中：

- `GET /ws/market`

前端订阅：

```json
{
  "action": "subscribe",
  "symbols": ["AAPL", "NVDA", "TSLA"]
}
```

网关推送：

```json
{
  "event": "quote",
  "symbol": "AAPL",
  "market": "US",
  "last_price": 212.52,
  "bid": 212.49,
  "ask": 212.53,
  "spread_bps": 1.88,
  "change_pct": 1.36,
  "volume": 68510444,
  "ts_event": "2026-04-19T10:15:01Z"
}
```

## 3. 网关内部结构

建议拆成 6 个模块：

1. `Provider Adapter`
2. `Normalizer`
3. `Feature Engine`
4. `Signal Engine`
5. `Alert Engine`
6. `Cache / Session Layer`

### 3.1 Provider Adapter

职责：

- 管理供应商认证
- 拉 snapshot
- 订阅 WebSocket
- 断线重连
- 记录原始事件

### 3.2 Normalizer

职责：

- 统一字段名
- 统一时间戳
- 统一市场代码
- 统一数值精度

## 4. 推荐标准化字段

无论供应商是谁，统一输出这些字段：

- `symbol`
- `market`
- `last_price`
- `change_pct`
- `change_abs`
- `open`
- `high`
- `low`
- `prev_close`
- `volume`
- `turnover`
- `bid`
- `ask`
- `spread_bps`
- `volume_ratio`
- `volatility_pct`
- `bar_1m`
- `trade_count_1m`
- `ts_event`
- `provider`

## 5. 推荐分析输出

前端不应该自己从零算所有指标。

更专业的方式是后端直接输出：

- `momentum_score`
- `liquidity_score`
- `volatility_score`
- `trade_readiness_score`
- `signal_bias`
- `risk_flags`
- `alerts`

示例：

```json
{
  "symbol": "AAPL",
  "analysis": {
    "momentum_score": 78,
    "liquidity_score": 92,
    "volatility_score": 67,
    "trade_readiness_score": 81,
    "signal_bias": "趋势延续",
    "risk_flags": ["spread_normal", "volume_confirmed"],
    "alerts": [
      {
        "level": "high",
        "type": "volume_expansion",
        "message": "量价共振成立"
      }
    ]
  }
}
```

## 6. 专业处理机制

推荐采用：

- `Snapshot + WebSocket + Cache`
- `分钟级聚合`
- `事件驱动告警`
- `多维评分，不直接输出简单买卖结论`

实时处理顺序建议：

1. 收到原始 trade / quote / bar
2. 标准化
3. 更新内存态
4. 计算特征
5. 更新评分
6. 触发告警
7. 推送给前端

## 7. 数据源建议

### 美股专业版

- `Polygon / Massive`
- `Alpaca`

### A 股研究原型

- `Tushare`

## 8. 工程建议

如果要真正可用，建议下一阶段补这些内容：

- 后端市场数据网关
- 统一配置文件
- 观察池持久化
- 告警中心
- 板块联动分析
- VWAP 和分钟级策略评分
