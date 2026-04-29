# MiniMax 智能股票监控预警系统

> 基于 MiniMax 大模型的全自动 A 股监控 + 分析 + 推送系统。
> 支持：实时行情抓取 → AI 分析 → 异常预警 → 微信推送 → 历史积累 → 每日总结

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据来源                               │
│              腾讯行情接口 qt.gtimg.cn                     │
└──────────────────┬────────────────────────────────────┘
                   │ 每 30 分钟（cron 触发）
                   ▼
┌─────────────────────────────────────────────────────────┐
│           ~/.hermes/scripts/stock_XXXXXX_monitor.py     │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ fetch_quote  │→ │ is_anomaly  │→ │ save_history  │  │
│  │ (行情抓取)   │  │ (异常检测)   │  │ (JSONL历史)   │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
│                          │                              │
│                          ▼                              │
│               /Users/starfeld/hermes/data/             │
│  ┌──────────────────────┴───────────────────────────┐  │
│  │  stock_XXXXXX_latest.json   ← 最新行情+prompt    │  │
│  │  stock_history/XXXXXX_YYYY-MM-DD.jsonl ← 历史    │  │
│  │  daily_summary.json         ← 每日总结素材       │  │
│  └─────────────────────────────────────────────────┘  │
└──────────────────┬────────────────────────────────────┘
                   │ cron job (MiniMax-Text-01)
                   ▼
┌─────────────────────────────────────────────────────────┐
│                    MiniMax 模型                         │
│  读取 latest.json → 分析行情 → 生成投资建议              │
│  温度 0.3 / 300字以内 / 微信友好格式                    │
└──────────────────┬────────────────────────────────────┘
                   │ send_message
                   ▼
┌─────────────────────────────────────────────────────────┐
│                     微信推送                             │
│  o9cq8095_8Bgpl-TUzScVAxx8g9U@im.wechat                │
└─────────────────────────────────────────────────────────┘
```

---

## 核心功能

### 1. 实时监控（每 30 分钟）
- 自动抓取股价、涨跌幅、成交量、量比等数据
- 异常检测规则：
  - **价格异常**：涨跌幅 ≥ 3% 触发
  - **放量异常**：量比 ≥ 3x 触发
  - **缩量异常**：量比 ≤ 0.3x 触发
- 异常时立即发送微信预警
- 正常时发送简短状态更新

### 2. 历史数据积累
- 每次抓取都追加保存到 `stock_history/XXXXXX_YYYY-MM-DD.jsonl`
- 每日一个文件，每行一条行情记录
- 字段包括：symbol, name, last_price, change_pct, open, high, low, volume, turnover, volume_ratio, bid, ask, ts_event, fetched_at

### 3. 每日投资总结（晚 9 点）
- 读取当日所有历史数据
- 计算：开盘/收盘/最高/最低/涨跌幅/总成交量/量比峰值
- MiniMax 综合分析 + 投资建议
- 推送微信

### 4. 投资分析档案
- 历史数据支撑后续复盘和量化分析
- 数据格式标准化，可直接导入分析工具

---

## 监控的股票

| 股票名称 | 代码 | Job ID | 状态 |
|---------|------|--------|------|
| 普冉股份 | 688766.SH | b981ab5a | ✅ 监控中 |
| 张裕A | 000869.SZ | e85b828b | ✅ 监控中 |

---

## 文件结构

```
~/.hermes/
├── scripts/
│   ├── stock_688766_monitor.py   # 688766 监控脚本
│   ├── stock_000869_monitor.py   # 000869 监控脚本
│   └── daily_summary.py          # 晚9点总结脚本
└── data/
    ├── stock_688766_latest.json  # 688766 最新行情
    ├── stock_000869_latest.json  # 000869 最新行情
    ├── daily_summary.json         # 每日总结素材
    └── stock_history/
        ├── 688766_SH_2026-04-26.jsonl
        └── 000869_SZ_2026-04-26.jsonl
```

---

## 添加新股票

### 步骤 1：创建监控脚本
参考 `stock_688766_monitor.py`，新建 `stock_XXXXXX_monitor.py`，修改 `symbol = "新代码.SH"`。

### 步骤 2：创建 cron 任务
```python
cronjob(action='create', name='XXXXXX 股票监控',
        prompt='读取 /Users/starfeld/hermes/data/stock_XXXXXX_latest.json，用MiniMax分析，发送到微信',
        schedule='every 30m',
        script='stock_XXXXXX_monitor.py',
        deliver='origin',
        model={'model': 'MiniMax-Text-01', 'provider': 'minimax'})
```

### 步骤 3：更新晚间总结
修改 `daily_summary.py` 的 `symbols` 列表，加入新代码。

---

## 异常检测规则

| 规则 | 条件 | 动作 |
|------|------|------|
| 大涨 | change_pct ≥ +3% | 立即微信预警 |
| 大跌 | change_pct ≤ -3% | 立即微信预警 |
| 放量 | volume_ratio ≥ 3x | 微信提醒 |
| 缩量 | volume_ratio ≤ 0.3x | 微信提醒 |
| 正常 | 以上皆不满足 | 涨跌幅 >0.5% 时发状态更新 |

---

## Cron 任务列表

| 任务名 | 调度 | Job ID | 说明 |
|--------|------|--------|------|
| 688766 MiniMax 实时监控 | every 30m | b981ab5a | 普冉股份 |
| 000869 张裕A MiniMax 实时监控 | every 30m | e85b828b | 张裕A |
| 每日投资总结 晚9点 | 0 21 * * * | 8b89a503b48f | 生成并推送每日总结 |

查看任务：`cronjob(action='list')`
手动触发：`cronjob(action='run', job_id='...')`
暂停任务：`cronjob(action='pause', job_id='...')`

---

## 数据字段说明

### stock_XXXXXX_latest.json
```json
{
  "symbol": "688766.SH",
  "quote": {
    "symbol": "688766.SH",
    "name": "普冉股份",
    "last_price": 261.58,
    "prev_close": 266.13,
    "open": 264.39,
    "high": 270.54,
    "low": 255.0,
    "change_abs": -4.55,
    "change_pct": -1.71,
    "volume": 4261028,
    "turnover": 111465,
    "volume_ratio": 2.88,
    "bid": 261.56,
    "ask": 261.58,
    "ts_event": "2026-04-24 16:14:35",
    "fetched_at": "2026-04-26T07:30:00+00:00"
  },
  "prompt": "...",
  "anomaly": {"is_anomaly": true, "reason": ["放量 2.88x"]},
  "generated_at": "2026-04-26T07:30:00+00:00"
}
```

### JSONL 历史数据（每日一行）
```json
{"symbol":"688766.SH","name":"普冉股份","last_price":261.58,"change_pct":-1.71,...}
```

---

## 技术细节

- **行情来源**：腾讯行情 `qt.gtimg.cn`（免费、实时）
- **分析模型**：MiniMax-Text-01（温度 0.3）
- **推送渠道**：微信（Home channel）
- **数据存储**：JSON + JSONL（便于后续 Python 分析）
- **Python 版本**：3.9+（系统自带或 pyenv）
- **时区**：所有时间戳均为 UTC，内部显示转换为 CST

---

## 维护命令

```bash
# 查看所有 cron 任务
cronjob(action='list')

# 手动触发监控（测试）
cronjob(action='run', job_id='b981ab5a')

# 暂停/恢复任务
cronjob(action='pause', job_id='b981ab5a')
cronjob(action='resume', job_id='b981ab5a')

# 查看历史数据
ls ~/.hermes/data/stock_history/

# 查看最新数据
cat ~/.hermes/data/stock_688766_latest.json
```

---

*文档更新时间：2026-04-26*
