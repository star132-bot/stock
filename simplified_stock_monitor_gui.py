#!/usr/bin/env python3
from __future__ import annotations

import queue
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Callable


APP_TITLE = "简化股票监控"


def _safe_text(value: Any, fallback: str = "-") -> str:
    if value is None or value == "":
        return fallback
    return str(value)


class SimplifiedStockMonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x720")
        self.minsize(960, 620)

        self.result_queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.selected_symbol = tk.StringVar(value="")
        self.hermes_mode = tk.StringVar(value="normal")
        self.core_python = self._detect_core_python()
        self.status_text = tk.StringVar(value=f"就绪 | 核心 {self.core_python}")

        self._build_layout()
        self.refresh_watchlist()
        self.after(120, self._poll_results)

    def _detect_core_python(self) -> str:
        root = Path(__file__).resolve().parent
        candidates = [
            os.getenv("HERMES_CORE_PYTHON", ""),
            os.getenv("HERMES_PYTHON_BIN", ""),
            str(root / ".venv" / "bin" / "python"),
            "/Users/starfeld/.pyenv/versions/3.11.12/bin/python",
            "/opt/homebrew/bin/python3.11",
            "python3.11",
            "python3.10",
        ]
        for candidate in candidates:
            if not candidate:
                continue
            try:
                result = subprocess.run(
                    [candidate, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"],
                    cwd=root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
            except OSError:
                continue
            if result.returncode == 0:
                return candidate
        raise RuntimeError("需要一个 Python 3.10+ 作为股票监控核心。请设置 HERMES_CORE_PYTHON。")

    def _cli(self, *args: str) -> Any:
        command = [self.core_python, "simplified_stock_monitor.py", *args]
        result = subprocess.run(
            command,
            cwd=Path(__file__).resolve().parent,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"命令失败：{' '.join(command)}")
        output = result.stdout.strip()
        if not output:
            return {}
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return {"output": output}

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(self, padding=14)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.columnconfigure(0, weight=1)

        title = ttk.Label(sidebar, text=APP_TITLE, font=("Arial", 18, "bold"))
        title.grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(sidebar, text="股票代码或名称").grid(row=1, column=0, sticky="w")
        self.search_entry = ttk.Entry(sidebar, width=28)
        self.search_entry.grid(row=2, column=0, sticky="ew", pady=(4, 8))
        self.search_entry.insert(0, "688766")
        self.search_entry.bind("<Return>", lambda _event: self.search_and_add())

        ttk.Button(sidebar, text="搜索并加入关注", command=self.search_and_add).grid(row=3, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="分析当前股票", command=self.analyze_selected).grid(row=4, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="刷新行情", command=self.refresh_quote).grid(row=5, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="运行一次监控", command=self.run_monitor).grid(row=6, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="发送告警", command=self.send_alerts).grid(row=7, column=0, sticky="ew", pady=3)
        ttk.Button(sidebar, text="配置告警目标", command=self.configure_alert_target).grid(row=8, column=0, sticky="ew", pady=3)

        mode_box = ttk.LabelFrame(sidebar, text="Hermes 模式", padding=8)
        mode_box.grid(row=9, column=0, sticky="ew", pady=(12, 8))
        for index, (value, label) in enumerate(
            [("normal", "正常"), ("defensive", "防守"), ("crash", "崩坏")]
        ):
            ttk.Radiobutton(mode_box, text=label, value=value, variable=self.hermes_mode).grid(
                row=0, column=index, sticky="w"
            )

        watch_frame = ttk.LabelFrame(sidebar, text="关注池", padding=8)
        watch_frame.grid(row=10, column=0, sticky="nsew", pady=(8, 0))
        sidebar.rowconfigure(10, weight=1)
        self.watchlist_box = tk.Listbox(watch_frame, height=14, activestyle="dotbox")
        self.watchlist_box.grid(row=0, column=0, sticky="nsew")
        watch_frame.rowconfigure(0, weight=1)
        watch_frame.columnconfigure(0, weight=1)
        self.watchlist_box.bind("<<ListboxSelect>>", lambda _event: self.on_watchlist_select())

        ttk.Button(watch_frame, text="刷新关注池", command=self.refresh_watchlist).grid(row=1, column=0, sticky="ew", pady=(8, 0))

        content = ttk.Frame(self, padding=(6, 14, 14, 14))
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        header = ttk.Frame(content)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        self.symbol_label = ttk.Label(header, text="未选择股票", font=("Arial", 20, "bold"))
        self.symbol_label.grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.status_text).grid(row=0, column=1, sticky="e")

        self.summary_var = tk.StringVar(value="搜索或选择一只股票开始。")
        ttk.Label(content, textvariable=self.summary_var, wraplength=820).grid(row=1, column=0, sticky="ew", pady=(8, 10))

        panes = ttk.PanedWindow(content, orient=tk.HORIZONTAL)
        panes.grid(row=2, column=0, sticky="nsew")

        left = ttk.Frame(panes, padding=8)
        right = ttk.Frame(panes, padding=8)
        panes.add(left, weight=1)
        panes.add(right, weight=1)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(left, text="行情 / Hermes / 投资判断", font=("Arial", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.analysis_text = tk.Text(left, height=20, wrap="word")
        self.analysis_text.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        ttk.Label(right, text="简化 K 线", font=("Arial", 13, "bold")).grid(row=0, column=0, sticky="w")
        self.kline_canvas = tk.Canvas(right, bg="#f7fafc", height=330, highlightthickness=1, highlightbackground="#d6e0e6")
        self.kline_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        self.kline_note = tk.StringVar(value="暂无 K 线数据")
        ttk.Label(right, textvariable=self.kline_note, wraplength=420).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _run_async(self, name: str, fn: Callable[[], Any]) -> None:
        self.status_text.set(f"{name}中...")

        def worker() -> None:
            try:
                self.result_queue.put((name, fn()))
            except Exception as exc:
                self.result_queue.put((f"{name}:error", exc))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_results(self) -> None:
        while True:
            try:
                name, payload = self.result_queue.get_nowait()
            except queue.Empty:
                break
            if name.endswith(":error"):
                self.status_text.set("执行失败")
                messagebox.showerror(APP_TITLE, str(payload))
                continue
            self.status_text.set("就绪")
            if name == "搜索":
                self._handle_search_result(payload)
            elif name == "分析":
                self._render_analysis(payload)
            elif name == "行情":
                self._render_quote(payload)
            elif name == "监控":
                self._render_monitor(payload)
            elif name == "告警":
                messagebox.showinfo(APP_TITLE, f"发送完成：成功 {payload.get('sent', 0)}，失败 {payload.get('failed', 0)}")
        self.after(120, self._poll_results)

    def search_and_add(self) -> None:
        query = self.search_entry.get().strip()
        if not query:
            return

        def task() -> dict[str, Any]:
            matches = self._cli("search", query)
            symbol = matches[0]["symbol"] if matches else query
            item = self._cli("add", symbol)
            return {"item": item, "symbol": item["symbol"]}

        self._run_async("搜索", task)

    def _handle_search_result(self, payload: dict[str, Any]) -> None:
        symbol = payload["symbol"]
        self.selected_symbol.set(symbol)
        self.symbol_label.config(text=symbol)
        self.refresh_watchlist()
        self._run_async("分析", lambda: self._cli("analyze", symbol, "--mode", self.hermes_mode.get()))

    def refresh_watchlist(self) -> None:
        self.watchlist_box.delete(0, tk.END)
        try:
            status = self._cli("status")
            items = status.get("watchlist", [])
        except Exception as exc:
            self.status_text.set(f"关注池读取失败：{exc}")
            return
        for item in items:
            if not item.get("enabled", True):
                continue
            label = f"{item.get('symbol')}  {item.get('note') or ''}".strip()
            self.watchlist_box.insert(tk.END, label)

    def on_watchlist_select(self) -> None:
        selection = self.watchlist_box.curselection()
        if not selection:
            return
        raw = self.watchlist_box.get(selection[0])
        symbol = raw.split()[0]
        self.selected_symbol.set(symbol)
        self.symbol_label.config(text=symbol)
        self.analyze_selected()

    def analyze_selected(self) -> None:
        symbol = self.selected_symbol.get() or self.search_entry.get().strip()
        if not symbol:
            messagebox.showinfo(APP_TITLE, "请先输入或选择股票。")
            return
        self.selected_symbol.set(symbol)
        self.symbol_label.config(text=symbol)
        self._run_async("分析", lambda: self._cli("analyze", symbol, "--mode", self.hermes_mode.get()))

    def refresh_quote(self) -> None:
        symbol = self.selected_symbol.get() or self.search_entry.get().strip()
        if not symbol:
            return
        self._run_async("行情", lambda: self._cli("quotes", symbol))

    def run_monitor(self) -> None:
        self._run_async("监控", lambda: self._cli("run-monitor", "--mode", self.hermes_mode.get()))

    def send_alerts(self) -> None:
        self._run_async("告警", lambda: self._cli("send-alerts"))

    def configure_alert_target(self) -> None:
        status = self._cli("status")
        current = (status.get("monitor_config") or {}).get("target") or ""
        target = simpledialog.askstring(
            APP_TITLE,
            "输入告警目标，例如 pushplus:token / serverchan:SCTxxx / wecom_bot:key。留空关闭。",
            initialvalue=current,
            parent=self,
        )
        if target is None:
            return
        self._cli("config-alerts", "--target", target.strip())
        messagebox.showinfo(APP_TITLE, "告警目标已保存。")

    def _render_quote(self, quotes: list[dict[str, Any]]) -> None:
        if not quotes:
            self.summary_var.set("未获取到行情。")
            return
        quote = quotes[0]
        self.summary_var.set(
            f"{quote.get('symbol')} {quote.get('name')} | 最新 {quote.get('last_price')} | "
            f"涨跌 {quote.get('change_pct')}% | 量比 {quote.get('volume_ratio')}"
        )

    def _render_analysis(self, payload: dict[str, Any]) -> None:
        quote = payload.get("quote", {})
        kline = payload.get("kline", {})
        decision = payload.get("decision", {})
        self.symbol_label.config(text=f"{quote.get('symbol')} {quote.get('name', '')}".strip())
        self.summary_var.set(
            f"最新 {quote.get('last_price')} | 涨跌 {quote.get('change_pct')}% | "
            f"保护分 {quote.get('protection_score')} | {quote.get('signal_bias')}"
        )

        lines = [
            "【实时行情】",
            f"股票：{quote.get('symbol')} {quote.get('name')}",
            f"最新价：{quote.get('last_price')}    涨跌幅：{quote.get('change_pct')}%",
            f"开高低：{quote.get('open')} / {quote.get('high')} / {quote.get('low')}",
            f"成交量：{quote.get('volume')}    量比：{quote.get('volume_ratio')}",
            "",
            "【Hermes 风控】",
            f"保护分：{quote.get('protection_score')}    等级：{quote.get('alert_level')}",
            f"信号：{quote.get('signal_bias')}",
            f"风险标签：{', '.join(quote.get('risk_flags') or [])}",
            f"摘要：{quote.get('summary')}",
            "",
            "【K 线与量价】",
            f"趋势：{kline.get('trend_label')}    技术分：{kline.get('technical_score')}",
            f"MA：5={_safe_text((kline.get('ma') or {}).get('ma5'))}  "
            f"10={_safe_text((kline.get('ma') or {}).get('ma10'))}  "
            f"20={_safe_text((kline.get('ma') or {}).get('ma20'))}  "
            f"60={_safe_text((kline.get('ma') or {}).get('ma60'))}",
            f"支撑/压力：{kline.get('support_price')} / {kline.get('resistance_price')}",
            f"量价总结：{kline.get('volume_price_summary')}",
            "",
            "【投资判断】",
            f"结论：{decision.get('decision')}",
            f"理由：{'；'.join(decision.get('reasons') or [])}",
        ]
        if payload.get("kline_error"):
            lines.extend(["", f"K线数据源提示：{payload['kline_error']}"])

        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, "\n".join(lines))
        self._draw_kline(kline.get("bars") or [])

    def _render_monitor(self, payload: dict[str, Any]) -> None:
        lines = [
            "【监控完成】",
            f"行情数量：{len(payload.get('quotes', []))}",
            f"告警数量：{len(payload.get('alerts', []))}",
            f"outbox：{len(payload.get('outbox_records', []))}",
            "",
            "【风险排行】",
        ]
        for item in payload.get("top_risks", [])[:10]:
            lines.append(
                f"{item.get('symbol')} | {item.get('alert_level')} | "
                f"保护分 {item.get('protection_score')} | {item.get('summary')}"
            )
        self.analysis_text.delete("1.0", tk.END)
        self.analysis_text.insert(tk.END, "\n".join(lines))

    def _draw_kline(self, bars: list[dict[str, Any]]) -> None:
        self.kline_canvas.delete("all")
        if not bars:
            self.kline_note.set("暂无 K 线数据")
            return

        self.update_idletasks()
        width = max(self.kline_canvas.winfo_width(), 420)
        height = max(self.kline_canvas.winfo_height(), 300)
        pad = 24
        chart_h = height - pad * 2
        visible = bars[-50:]

        highs = [float(item.get("high") or 0) for item in visible]
        lows = [float(item.get("low") or 0) for item in visible]
        max_price = max(highs)
        min_price = min(lows)
        span = max(max_price - min_price, 1)

        def y_for(price: float) -> float:
            return pad + (max_price - price) / span * chart_h

        gap = (width - pad * 2) / max(len(visible), 1)
        candle_w = max(3, min(9, gap * 0.55))

        for index, bar in enumerate(visible):
            open_price = float(bar.get("open") or 0)
            close_price = float(bar.get("close") or 0)
            high_price = float(bar.get("high") or 0)
            low_price = float(bar.get("low") or 0)
            x = pad + gap * index + gap / 2
            color = "#0e7c66" if close_price >= open_price else "#c4493a"
            self.kline_canvas.create_line(x, y_for(high_price), x, y_for(low_price), fill=color, width=1)
            top = y_for(max(open_price, close_price))
            bottom = y_for(min(open_price, close_price))
            if abs(bottom - top) < 2:
                bottom = top + 2
            self.kline_canvas.create_rectangle(
                x - candle_w / 2,
                top,
                x + candle_w / 2,
                bottom,
                outline=color,
                fill=color,
            )

        latest = visible[-1]
        self.kline_note.set(
            f"{latest.get('date')} | 开 {latest.get('open')} 收 {latest.get('close')} "
            f"高 {latest.get('high')} 低 {latest.get('low')} | 共 {len(visible)} 根"
        )


def main() -> int:
    app = SimplifiedStockMonitorApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
