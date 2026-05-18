#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import server
from monitor_runtime import (
    load_monitor_config,
    load_monitor_status,
    load_outbox,
    load_position_book,
    load_watchlist,
    save_monitor_config,
    save_position_book,
    utc_now_iso,
)
from scripts.generate_nightly_summary import main as generate_nightly_summary_main
from sender import flush_outbox, retry_failed, sender_env_help


APP_NAME = "简化股票监控"


def _print_title(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"{APP_NAME} | {title}")
    print("=" * 72)


def _print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _prompt(label: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default not in (None, "") else ""
    value = input(f"{label}{suffix}: ").strip()
    return value if value else (default or "")


def _normalize_symbol(raw: str) -> str:
    return server._normalize_watch_symbol(raw)


def search_stock(query: str, limit: int = 8) -> list[dict[str, Any]]:
    return server._search_catalog(query, limit=limit)


def add_watch(symbol: str, note: str | None = None) -> dict[str, Any]:
    return server._upsert_watchlist_item(symbol, note=note)


def remove_watch(symbol: str) -> dict[str, Any]:
    return server._disable_watchlist_item(symbol)


def list_watchlist() -> list[dict[str, Any]]:
    return load_watchlist()


def fetch_quotes(symbols: list[str]) -> list[dict[str, Any]]:
    normalized = [_normalize_symbol(symbol) for symbol in symbols]
    return server._fetch_quotes(normalized)


def analyze_symbol(symbol: str, hermes_mode: str = "normal") -> dict[str, Any]:
    return server._build_symbol_analysis(symbol, hermes_mode=hermes_mode)


def run_monitor(hermes_mode: str = "normal") -> dict[str, Any]:
    return server._run_monitor_cycle(hermes_mode=hermes_mode)


def configure_alert_target(
    target: str | None,
    cooldown_minutes: int | None = None,
    min_level: str | None = None,
    analysis_model: str | None = None,
) -> dict[str, Any]:
    config = load_monitor_config()
    if target is not None:
        config["target"] = target or None
    if cooldown_minutes is not None:
        config["cooldown_minutes"] = cooldown_minutes
    if min_level:
        config["min_level"] = min_level
    if analysis_model:
        config["analysis_model"] = analysis_model
    save_monitor_config(config)
    return config


def upsert_position(
    symbol: str,
    quantity: float | None = None,
    avg_cost: float | None = None,
    stop_loss: float | None = None,
    target_price: float | None = None,
    horizon: str | None = None,
    thesis: str | None = None,
) -> dict[str, Any]:
    normalized = _normalize_symbol(symbol)
    items = [item for item in load_position_book() if item.get("symbol") != normalized]
    existing = next((item for item in load_position_book() if item.get("symbol") == normalized), {})
    payload = {
        **existing,
        "symbol": normalized,
        "updated_at": utc_now_iso(),
    }
    for key, value in {
        "quantity": quantity,
        "avg_cost": avg_cost,
        "stop_loss": stop_loss,
        "target_price": target_price,
        "horizon": horizon,
        "thesis": thesis,
    }.items():
        if value not in (None, ""):
            payload[key] = value
    items.append(payload)
    items.sort(key=lambda item: str(item.get("symbol", "")))
    save_position_book(items)
    return payload


def _float_or_none(value: str) -> float | None:
    if not value:
        return None
    return float(value)


def _print_watchlist() -> None:
    _print_title("关注池")
    items = list_watchlist()
    if not items:
        print("暂无关注股票。")
        return
    for index, item in enumerate(items, start=1):
        status = "启用" if item.get("enabled", True) else "停用"
        note = f" | {item.get('note')}" if item.get("note") else ""
        print(f"{index}. {item.get('symbol')} | {status}{note}")


def _print_quotes(symbols: list[str]) -> None:
    _print_title("实时行情")
    quotes = fetch_quotes(symbols)
    if not quotes:
        print("未获取到行情。")
        return
    for quote in quotes:
        print(
            f"{quote.get('symbol')} {quote.get('name')} | "
            f"最新 {quote.get('last_price')} | "
            f"涨跌 {quote.get('change_pct')}% | "
            f"量比 {quote.get('volume_ratio')} | "
            f"振幅 {quote.get('volatility_pct', '-')}"
        )


def _print_analysis(symbol: str, hermes_mode: str) -> None:
    _print_title("Hermes 分析")
    payload = analyze_symbol(symbol, hermes_mode=hermes_mode)
    quote = payload.get("quote", {})
    kline = payload.get("kline", {})
    decision = payload.get("decision", {})
    print(f"股票：{quote.get('symbol')} {quote.get('name')}")
    print(f"价格：{quote.get('last_price')} | 涨跌幅：{quote.get('change_pct')}%")
    print(
        f"Hermes：保护分 {quote.get('protection_score')} | "
        f"等级 {quote.get('alert_level')} | 判断 {quote.get('signal_bias')}"
    )
    print(f"风险摘要：{quote.get('summary')}")
    print(
        f"K线：{kline.get('trend_label')} | 技术分 {kline.get('technical_score')} | "
        f"{kline.get('volume_price_summary')}"
    )
    if payload.get("kline_error"):
        print(f"K线数据源提示：{payload['kline_error']}")
    print(f"投资判断：{decision.get('decision')} | {'；'.join(decision.get('reasons') or [])}")


def _interactive_search_and_add() -> None:
    _print_title("搜索并加入关注")
    query = _prompt("输入股票代码或名称，例如 688766")
    matches = search_stock(query)
    if not matches:
        print("没有搜索结果。")
        return
    for index, item in enumerate(matches, start=1):
        print(f"{index}. {item['symbol']} | {item['name']}")
    selected_raw = _prompt("选择序号", "1")
    selected = matches[max(0, min(len(matches) - 1, int(selected_raw) - 1))]
    note = _prompt("备注，可留空")
    item = add_watch(selected["symbol"], note=note or None)
    print(f"已加入关注：{item['symbol']} {item.get('name', '')}")


def _interactive_remove_watch() -> None:
    _print_watchlist()
    symbol = _prompt("输入要移出的股票代码")
    item = remove_watch(symbol)
    print(f"已停用：{item['symbol']}")


def _interactive_quotes() -> None:
    enabled = [item["symbol"] for item in list_watchlist() if item.get("enabled", True)]
    raw = _prompt("输入股票代码，多个用逗号分隔；留空则查看关注池", ",".join(enabled))
    symbols = [item.strip() for item in raw.split(",") if item.strip()]
    _print_quotes(symbols)


def _interactive_analysis() -> None:
    symbol = _prompt("输入股票代码")
    mode = _prompt("Hermes 模式 normal/defensive/crash", "normal")
    _print_analysis(symbol, mode)


def _interactive_position() -> None:
    _print_title("录入持仓逻辑")
    symbol = _prompt("股票代码")
    position = upsert_position(
        symbol=symbol,
        quantity=_float_or_none(_prompt("持仓数量，可留空")),
        avg_cost=_float_or_none(_prompt("成本价，可留空")),
        stop_loss=_float_or_none(_prompt("止损价，可留空")),
        target_price=_float_or_none(_prompt("目标价，可留空")),
        horizon=_prompt("持有周期，可留空"),
        thesis=_prompt("买入逻辑，可留空"),
    )
    print("已保存持仓：")
    _print_json(position)


def _interactive_configure_alerts() -> None:
    _print_title("配置 Hermes 告警")
    print("支持目标：")
    _print_json(sender_env_help())
    current = load_monitor_config()
    target = _prompt("告警目标，留空表示关闭", current.get("target") or "")
    cooldown = _float_or_none(_prompt("cooldown 分钟", str(current.get("cooldown_minutes", 15))))
    min_level = _prompt("最低告警等级 low/medium/high", current.get("min_level", "medium"))
    config = configure_alert_target(target, int(cooldown) if cooldown is not None else None, min_level)
    print("已保存配置：")
    _print_json(config)


def _interactive_run_monitor() -> None:
    _print_title("运行 Hermes 监控")
    mode = _prompt("Hermes 模式 normal/defensive/crash", "normal")
    result = run_monitor(hermes_mode=mode)
    print(
        f"完成：行情 {len(result.get('quotes', []))} 条 | "
        f"告警 {len(result.get('alerts', []))} 条 | "
        f"outbox {len(result.get('outbox_records', []))} 条"
    )
    for item in result.get("top_risks", [])[:8]:
        print(
            f"- {item.get('symbol')} | {item.get('alert_level')} | "
            f"保护分 {item.get('protection_score')} | {item.get('summary')}"
        )


def _interactive_send_alerts() -> None:
    _print_title("发送 Hermes 告警")
    retry = _prompt("是否重试失败告警 y/N", "N").lower() == "y"
    result = retry_failed() if retry else flush_outbox()
    _print_json(result)


def _interactive_status() -> None:
    _print_title("运行状态")
    print("监控配置：")
    _print_json(load_monitor_config())
    print("监控状态：")
    _print_json(load_monitor_status())
    print(f"outbox 总数：{len(load_outbox())}")
    print(f"持仓记录：{len(load_position_book())}")


def _interactive_nightly_summary() -> None:
    _print_title("生成夜间总结")
    target_day = _prompt("日期 YYYY-MM-DD，留空为今天", date.today().isoformat())
    generate_nightly_summary(target_day)


def generate_nightly_summary(target_day: str | None = None) -> int:
    old_argv = sys.argv[:]
    try:
        sys.argv = ["generate_nightly_summary.py"]
        if target_day:
            sys.argv.extend(["--date", target_day])
        return generate_nightly_summary_main()
    finally:
        sys.argv = old_argv


def interactive_menu() -> int:
    actions = {
        "1": ("搜索股票并加入关注", _interactive_search_and_add),
        "2": ("查看关注池", _print_watchlist),
        "3": ("移出关注", _interactive_remove_watch),
        "4": ("查看实时行情", _interactive_quotes),
        "5": ("查看 Hermes 分析/K线/投资判断", _interactive_analysis),
        "6": ("录入持仓逻辑", _interactive_position),
        "7": ("配置 Hermes 告警", _interactive_configure_alerts),
        "8": ("运行一次 Hermes 监控", _interactive_run_monitor),
        "9": ("发送 outbox 告警", _interactive_send_alerts),
        "10": ("生成夜间总结", _interactive_nightly_summary),
        "11": ("查看运行状态", _interactive_status),
        "0": ("退出", None),
    }
    while True:
        _print_title("主菜单")
        for key, (label, _) in actions.items():
            print(f"{key}. {label}")
        choice = _prompt("请选择", "1")
        if choice == "0":
            print("已退出。")
            return 0
        action = actions.get(choice)
        if not action:
            print("无效选项。")
            continue
        try:
            action[1]()
        except Exception as exc:
            print(f"执行失败：{exc}")
        input("\n按回车返回主菜单...")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="简化股票监控：纯 Python 股票监控与 Hermes 风控工具。")
    sub = parser.add_subparsers(dest="command")

    search = sub.add_parser("search", help="搜索股票")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=8)

    add = sub.add_parser("add", help="加入关注")
    add.add_argument("symbol")
    add.add_argument("--note", default=None)

    remove = sub.add_parser("remove", help="移出关注")
    remove.add_argument("symbol")

    sub.add_parser("watchlist", help="查看关注池")

    quotes = sub.add_parser("quotes", help="查看行情")
    quotes.add_argument("symbols", nargs="+")

    analyze = sub.add_parser("analyze", help="查看 Hermes 分析")
    analyze.add_argument("symbol")
    analyze.add_argument("--mode", default="normal", choices=["normal", "defensive", "crash"])

    position = sub.add_parser("position", help="保存持仓逻辑")
    position.add_argument("symbol")
    position.add_argument("--quantity", type=float)
    position.add_argument("--avg-cost", type=float)
    position.add_argument("--stop-loss", type=float)
    position.add_argument("--target-price", type=float)
    position.add_argument("--horizon")
    position.add_argument("--thesis")

    config = sub.add_parser("config-alerts", help="配置 Hermes 告警")
    config.add_argument("--target", default=None)
    config.add_argument("--cooldown-minutes", type=int)
    config.add_argument("--min-level", choices=["low", "medium", "high"])
    config.add_argument("--analysis-model")

    monitor = sub.add_parser("run-monitor", help="运行一次 Hermes 监控")
    monitor.add_argument("--mode", default="normal", choices=["normal", "defensive", "crash"])

    send = sub.add_parser("send-alerts", help="发送 outbox 告警")
    send.add_argument("--retry-failed", action="store_true")

    sub.add_parser("status", help="查看状态")
    sub.add_parser("nightly-summary", help="生成夜间总结")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        return interactive_menu()

    if args.command == "search":
        _print_json(search_stock(args.query, args.limit))
    elif args.command == "add":
        _print_json(add_watch(args.symbol, args.note))
    elif args.command == "remove":
        _print_json(remove_watch(args.symbol))
    elif args.command == "watchlist":
        _print_json(list_watchlist())
    elif args.command == "quotes":
        _print_json(fetch_quotes(args.symbols))
    elif args.command == "analyze":
        _print_json(analyze_symbol(args.symbol, args.mode))
    elif args.command == "position":
        _print_json(
            upsert_position(
                symbol=args.symbol,
                quantity=args.quantity,
                avg_cost=args.avg_cost,
                stop_loss=args.stop_loss,
                target_price=args.target_price,
                horizon=args.horizon,
                thesis=args.thesis,
            )
        )
    elif args.command == "config-alerts":
        _print_json(
            configure_alert_target(
                target=args.target,
                cooldown_minutes=args.cooldown_minutes,
                min_level=args.min_level,
                analysis_model=args.analysis_model,
            )
        )
    elif args.command == "run-monitor":
        _print_json(run_monitor(args.mode))
    elif args.command == "send-alerts":
        _print_json(retry_failed() if args.retry_failed else flush_outbox())
    elif args.command == "status":
        _print_json(
            {
                "monitor_config": load_monitor_config(),
                "monitor_status": load_monitor_status(),
                "watchlist": load_watchlist(),
                "positions": load_position_book(),
                "outbox_count": len(load_outbox()),
            }
        )
    elif args.command == "nightly-summary":
        return generate_nightly_summary()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
