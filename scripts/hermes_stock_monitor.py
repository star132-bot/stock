#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from stock_analysis_service import (  # noqa: E402
    StockAnalysisError,
    build_capability_answer_template,
    build_stock_analysis,
    build_stock_query,
    get_realtime_monitor_status,
    load_realtime_monitor_state,
    normalize_thresholds,
    process_running,
    realtime_monitor_log_path,
    register_stock_monitor,
    run_registered_monitors,
    save_realtime_monitor_state,
    utc_now_iso,
)


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default))


def _parse_thresholds(values: list[str] | None) -> dict[str, float]:
    thresholds: dict[str, float] = {}
    for item in values or []:
        if "=" not in item:
            raise StockAnalysisError(f"阈值格式错误: {item}，应为 key=value")
        key, raw_value = item.split("=", 1)
        thresholds[key.strip()] = float(raw_value)
    return normalize_thresholds(thresholds, merge_defaults=False)


def _split_symbols(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def command_add(args: argparse.Namespace) -> int:
    thresholds = _parse_thresholds(args.threshold)
    items = [
        register_stock_monitor(
            symbol=symbol,
            interval_minutes=args.interval_minutes,
            hermes_mode=args.hermes_mode,
            note=args.note,
            target=args.target,
            thresholds=thresholds or None,
        )
        for symbol in args.symbols
    ]
    result = None
    if args.run_now:
        result = run_registered_monitors(symbols=[item["symbol"] for item in items], only_due=False, queue_alerts=not args.no_queue_alerts)
    _print_json({"ok": True, "items": items, "run_result": result})
    return 0


def command_run(args: argparse.Namespace) -> int:
    payload = run_registered_monitors(
        symbols=_split_symbols(args.symbols) or None,
        only_due=not args.force,
        hermes_mode=args.hermes_mode,
        queue_alerts=not args.no_queue_alerts,
    )
    _print_json({"ok": True, **payload})
    return 0


def command_loop(args: argparse.Namespace) -> int:
    running_mode = "background-loop" if os.getenv("HERMES_MONITOR_BACKGROUND") == "1" else "foreground-loop"
    save_realtime_monitor_state(
        {
            **load_realtime_monitor_state(),
            "pid": os.getpid(),
            "running_mode": running_mode,
            "symbols": _split_symbols(args.symbols),
            "poll_seconds": max(1, args.poll_seconds),
            "started_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "last_heartbeat_at": utc_now_iso(),
        }
    )
    iterations = 0
    while True:
        payload = run_registered_monitors(
            symbols=_split_symbols(args.symbols) or None,
            only_due=True,
            hermes_mode=args.hermes_mode,
            queue_alerts=not args.no_queue_alerts,
        )
        save_realtime_monitor_state(
                {
                    **load_realtime_monitor_state(),
                    "pid": os.getpid(),
                "running_mode": running_mode,
                "last_heartbeat_at": utc_now_iso(),
                "last_run_result": {
                    "recorded_at": payload.get("recorded_at"),
                    "selected_symbols": payload.get("selected_symbols"),
                    "skipped": payload.get("skipped"),
                    "result_count": len(payload.get("results") or []),
                    "queued_alert_count": len(payload.get("queued_alert_records") or []),
                },
            }
        )
        _print_json({"ok": True, **payload})
        iterations += 1
        if args.max_runs and iterations >= args.max_runs:
            return 0
        time.sleep(max(1, args.poll_seconds))


def command_analyze(args: argparse.Namespace) -> int:
    payload = build_stock_analysis(
        symbol=args.symbol,
        lookback=args.lookback,
        hermes_mode=args.hermes_mode,
        refresh=args.refresh,
    )
    _print_json({"ok": True, **payload})
    return 0


def command_start(args: argparse.Namespace) -> int:
    current = get_realtime_monitor_status()
    if current.get("running"):
        _print_json({"ok": True, "already_running": True, "status": current})
        return 0

    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "loop",
        "--poll-seconds",
        str(args.poll_seconds),
    ]
    if args.symbols:
        command.extend(["--symbols", args.symbols])
    if args.hermes_mode:
        command.extend(["--hermes-mode", args.hermes_mode])
    if args.no_queue_alerts:
        command.append("--no-queue-alerts")

    log_path = realtime_monitor_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("a", encoding="utf-8")
    env = {**os.environ, "HERMES_MONITOR_BACKGROUND": "1"}
    process = subprocess.Popen(
        command,
        cwd=str(ROOT),
        env=env,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
    )
    state = {
        "pid": process.pid,
        "running_mode": "background-loop",
        "symbols": _split_symbols(args.symbols),
        "poll_seconds": max(1, args.poll_seconds),
        "hermes_mode": args.hermes_mode,
        "started_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "command": command,
    }
    save_realtime_monitor_state(state)
    _print_json({"ok": True, "started": True, "status": get_realtime_monitor_status()})
    return 0


def command_status(args: argparse.Namespace) -> int:
    _print_json({"ok": True, "status": get_realtime_monitor_status()})
    return 0


def command_stop(args: argparse.Namespace) -> int:
    status = get_realtime_monitor_status()
    pid = status.get("pid")
    stopped = False
    stop_error = None
    if pid and status.get("running"):
        try:
            os.kill(int(pid), signal.SIGTERM)
            stopped = True
            deadline = time.time() + max(1, args.timeout_seconds)
            while time.time() < deadline and process_running(int(pid)):
                time.sleep(0.2)
            if process_running(int(pid)) and args.kill:
                os.kill(int(pid), signal.SIGKILL)
        except PermissionError as exc:
            stop_error = str(exc)
    save_realtime_monitor_state(
        {
            **load_realtime_monitor_state(),
            "pid": pid,
            "stopped_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
        }
    )
    _print_json({"ok": stop_error is None, "stopped": stopped, "error": stop_error, "status": get_realtime_monitor_status()})
    return 0


def command_query(args: argparse.Namespace) -> int:
    payload = build_stock_query(
        symbol=args.symbol,
        lookback=args.lookback,
        refresh=args.refresh,
        hermes_mode=args.hermes_mode,
    )
    _print_json({"ok": True, **payload})
    return 0


def command_capabilities(args: argparse.Namespace) -> int:
    payload = build_capability_answer_template()
    if args.text:
        print(payload["template"])
    else:
        _print_json({"ok": True, **payload})
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes Stock Sentinel local monitor runner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="登记一个或多个股票监控任务")
    add.add_argument("symbols", nargs="+", help="A股代码，如 688766.SH 或 688766")
    add.add_argument("--interval-minutes", type=int, default=30, help="采集间隔，默认 30 分钟")
    add.add_argument("--hermes-mode", default="normal", choices=["normal", "defensive", "crash"])
    add.add_argument("--note", default="hermes-stock-monitor")
    add.add_argument("--target", default=None, help="告警目标，如 pushplus:token")
    add.add_argument("--threshold", action="append", help="覆盖阈值，格式 key=value")
    add.add_argument("--run-now", action="store_true", help="登记后立即采集一次")
    add.add_argument("--no-queue-alerts", action="store_true", help="不写入 outbox 告警")
    add.set_defaults(func=command_add)

    run = subparsers.add_parser("run", help="运行一次已登记监控任务")
    run.add_argument("--symbols", default=None, help="逗号分隔股票代码；留空运行全部登记任务")
    run.add_argument("--force", action="store_true", help="忽略间隔，强制采集")
    run.add_argument("--hermes-mode", default=None, choices=["normal", "defensive", "crash"])
    run.add_argument("--no-queue-alerts", action="store_true")
    run.set_defaults(func=command_run)

    start = subparsers.add_parser("start", help="后台启动实时监控进程")
    start.add_argument("--symbols", default=None, help="逗号分隔股票代码；留空运行全部登记任务")
    start.add_argument("--poll-seconds", type=int, default=60, help="后台进程检查到期任务的轮询间隔")
    start.add_argument("--hermes-mode", default=None, choices=["normal", "defensive", "crash"])
    start.add_argument("--no-queue-alerts", action="store_true")
    start.set_defaults(func=command_start)

    status = subparsers.add_parser("status", help="查询实时监控进程状态")
    status.set_defaults(func=command_status)

    stop = subparsers.add_parser("stop", help="停止后台实时监控进程")
    stop.add_argument("--timeout-seconds", type=int, default=5)
    stop.add_argument("--kill", action="store_true", help="超时后使用 SIGKILL")
    stop.set_defaults(func=command_stop)

    loop = subparsers.add_parser("loop", help="循环运行到期监控任务，适合本地常驻进程")
    loop.add_argument("--symbols", default=None, help="逗号分隔股票代码；留空运行全部登记任务")
    loop.add_argument("--poll-seconds", type=int, default=60, help="检查到期任务的轮询间隔")
    loop.add_argument("--max-runs", type=int, default=None, help="最多执行多少轮，默认一直运行")
    loop.add_argument("--hermes-mode", default=None, choices=["normal", "defensive", "crash"])
    loop.add_argument("--no-queue-alerts", action="store_true")
    loop.set_defaults(func=command_loop)

    analyze = subparsers.add_parser("analyze", help="基于本地历史生成趋势和买卖分析")
    analyze.add_argument("symbol", help="A股代码")
    analyze.add_argument("--lookback", type=int, default=240)
    analyze.add_argument("--hermes-mode", default="normal", choices=["normal", "defensive", "crash"])
    analyze.add_argument("--refresh", action="store_true", help="分析前先采集一次")
    analyze.set_defaults(func=command_analyze)

    query = subparsers.add_parser("query", help="查询单股最新快照、历史摘要和分析结论")
    query.add_argument("symbol", help="A股代码")
    query.add_argument("--lookback", type=int, default=240)
    query.add_argument("--hermes-mode", default="normal", choices=["normal", "defensive", "crash"])
    query.add_argument("--refresh", action="store_true", help="查询前先采集一次")
    query.set_defaults(func=command_query)

    capabilities = subparsers.add_parser("capabilities", help="输出 Hermes 能力说明和回答模板")
    capabilities.add_argument("--text", action="store_true", help="只输出可直接展示给用户的文本模板")
    capabilities.set_defaults(func=command_capabilities)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except StockAnalysisError as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
