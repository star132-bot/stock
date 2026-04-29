#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monitor_runtime import (  # noqa: E402
    load_monitor_runs,
    load_monitor_status,
    nightly_summary_path,
    save_monitor_status,
)


def _pick_day(value: str | None) -> date:
    if not value:
        return date.today()
    return datetime.strptime(value, "%Y-%m-%d").date()


def _runs_for_day(target_day: date) -> list[dict]:
    matched = []
    for run in load_monitor_runs():
        recorded_at = run.get("recorded_at")
        if not recorded_at:
            continue
        try:
            dt = datetime.fromisoformat(recorded_at)
        except ValueError:
            continue
        if dt.date() == target_day:
            matched.append(run)
    return matched


def _level_counts(runs: list[dict]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for run in runs:
        for item in run.get("top_risks", []):
            level = str(item.get("alert_level", "low"))
            counts[level] = counts.get(level, 0) + 1
    return counts


def _render_summary(target_day: date, runs: list[dict]) -> str:
    if not runs:
        return (
            f"# Hermes Nightly Summary {target_day.isoformat()}\n\n"
            "## 概要\n\n"
            "- 当天没有监控运行记录。\n"
        )

    latest = runs[-1]
    unique_symbols = sorted({item["symbol"] for run in runs for item in run.get("watchlist", []) if item.get("enabled", True)})
    alerts = [alert for run in runs for alert in run.get("alerts", [])]
    counts = _level_counts(runs)
    latest_pulse = latest.get("market_pulse", {})
    latest_risks = latest.get("top_risks", [])[:5]
    quote_by_symbol = {item.get("symbol"): item for item in latest.get("quotes", [])}

    lines = [
        f"# Hermes Nightly Summary {target_day.isoformat()}",
        "",
        "## 概要",
        "",
        f"- 监控运行次数：{len(runs)}",
        f"- 监控股票数量：{len(unique_symbols)}",
        f"- 当日告警数量：{len(alerts)}",
        f"- 最新市场态势：{latest_pulse.get('label', '暂无')}",
        f"- 高风险记录：{counts.get('high', 0)}",
        f"- 中风险记录：{counts.get('medium', 0)}",
        "",
        "## 当日关注股票",
        "",
    ]

    for symbol in unique_symbols:
        lines.append(f"- {symbol}")

    lines.extend(["", "## 最新高优先级风险", ""])
    if latest_risks:
        for item in latest_risks:
            lines.append(
                f"- {item.get('symbol')} | {item.get('alert_level')} | "
                f"保护分 {item.get('protection_score')} | {item.get('summary')}"
            )
    else:
        lines.append("- 暂无风险摘要。")

    lines.extend(["", "## 最新行情快照", ""])
    if quote_by_symbol:
        for symbol in unique_symbols:
            quote = quote_by_symbol.get(symbol)
            if not quote:
                continue
            lines.append(
                f"- {symbol} | 最新价 {quote.get('last_price')} | 涨跌幅 {quote.get('change_pct')}% | "
                f"量比 {quote.get('volume_ratio')} | 点差 {quote.get('spread_bps')} bps"
            )
    else:
        lines.append("- 暂无可用行情快照。")

    lines.extend(["", "## K线与量价复盘", ""])
    if latest_risks:
        for item in latest_risks:
            lines.append(
                f"- {item.get('symbol')} | 技术偏向 {item.get('signal_bias')} | "
                f"保护分 {item.get('protection_score')} | 量价摘要 {item.get('summary')}"
            )
    else:
        lines.append("- 暂无 K 线与量价复盘数据。")

    lines.extend(["", "## 持仓与投资判断", ""])
    if latest_risks:
        for item in latest_risks:
            action = "继续观察"
            if item.get("protection_score", 0) <= 35:
                action = "卖出/强制复核"
            elif item.get("protection_score", 0) <= 50:
                action = "减仓/防守"
            elif item.get("protection_score", 0) >= 72:
                action = "继续持有"
            lines.append(
                f"- {item.get('symbol')} | 判断 {action} | "
                f"原因：保护分 {item.get('protection_score')}，风险等级 {item.get('alert_level')}"
            )
    else:
        lines.append("- 暂无持仓与投资判断数据。")

    lines.extend(["", "## 当日告警事件", ""])
    if alerts:
        for alert in alerts[-20:]:
            lines.append(
                f"- {alert.get('created_at')} | {alert.get('symbol')} | "
                f"{alert.get('level')} | {alert.get('headline')}"
            )
    else:
        lines.append("- 当日未触发需要发送的告警。")

    lines.extend(
        [
            "",
            "## Hermes 复盘建议",
            "",
            "- 对高风险股票复核跌幅、量比、点差是否同步恶化。",
            "- 对连续多次进入 high 的标的，单独记录支撑位和仓位调整计划。",
            "- 将本日监控结果与后续收益表现对照，用于分析股票投资价值与风险承受区间。",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate nightly Hermes stock summary document.")
    parser.add_argument("--date", default=None, help="Summary date in YYYY-MM-DD, default today")
    args = parser.parse_args()

    target_day = _pick_day(args.date)
    runs = _runs_for_day(target_day)
    content = _render_summary(target_day, runs)
    output_path = nightly_summary_path(target_day.isoformat())
    output_path.write_text(content, encoding="utf-8")

    status = load_monitor_status()
    status["nightly_last_written_for"] = target_day.isoformat()
    save_monitor_status(status)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
