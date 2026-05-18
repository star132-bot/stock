import AppKit
import Foundation

struct Quote {
    let symbol: String
    let name: String
    let lastPrice: Double
    let changePct: Double
    let open: Double
    let high: Double
    let low: Double
    let volumeRatio: Double
    let protectionScore: Double
    let alertLevel: String
    let signalBias: String
    let summary: String
}

struct KlineBar {
    let date: String
    let open: Double
    let close: Double
    let high: Double
    let low: Double
    let volume: Double
}

struct AnalysisPayload {
    let quote: Quote
    let bars: [KlineBar]
    let trendLabel: String
    let technicalScore: Double
    let volumeSummary: String
    let decision: String
    let reasons: [String]
    let rawText: String
}

final class KlineView: NSView {
    var bars: [KlineBar] = [] {
        didSet { needsDisplay = true }
    }

    override func draw(_ dirtyRect: NSRect) {
        super.draw(dirtyRect)
        NSColor(calibratedRed: 0.97, green: 0.99, blue: 1.0, alpha: 1).setFill()
        bounds.fill()

        guard !bars.isEmpty else {
            drawCentered("暂无 K 线数据")
            return
        }

        let visible = Array(bars.suffix(60))
        let maxPrice = visible.map(\.high).max() ?? 1
        let minPrice = visible.map(\.low).min() ?? 0
        let span = max(maxPrice - minPrice, 1)
        let pad: CGFloat = 24
        let chartWidth = bounds.width - pad * 2
        let chartHeight = bounds.height - pad * 2
        let gap = chartWidth / CGFloat(max(visible.count, 1))
        let candleWidth = max(3, min(9, gap * 0.56))

        func y(_ price: Double) -> CGFloat {
            pad + CGFloat((maxPrice - price) / span) * chartHeight
        }

        NSColor(calibratedWhite: 0.86, alpha: 1).setStroke()
        for i in 0...4 {
            let yy = pad + chartHeight * CGFloat(i) / 4
            let path = NSBezierPath()
            path.move(to: NSPoint(x: pad, y: yy))
            path.line(to: NSPoint(x: bounds.width - pad, y: yy))
            path.lineWidth = 0.6
            path.stroke()
        }

        for (index, bar) in visible.enumerated() {
            let x = pad + gap * CGFloat(index) + gap / 2
            let color = bar.close >= bar.open
                ? NSColor(calibratedRed: 0.05, green: 0.49, blue: 0.40, alpha: 1)
                : NSColor(calibratedRed: 0.77, green: 0.29, blue: 0.23, alpha: 1)
            color.setStroke()
            color.setFill()

            let wick = NSBezierPath()
            wick.move(to: NSPoint(x: x, y: y(bar.high)))
            wick.line(to: NSPoint(x: x, y: y(bar.low)))
            wick.lineWidth = 1
            wick.stroke()

            let top = min(y(bar.open), y(bar.close))
            let bottom = max(y(bar.open), y(bar.close))
            let rect = NSRect(
                x: x - candleWidth / 2,
                y: top,
                width: candleWidth,
                height: max(2, bottom - top)
            )
            NSBezierPath(roundedRect: rect, xRadius: 1.5, yRadius: 1.5).fill()
        }
    }

    private func drawCentered(_ text: String) {
        let attrs: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: 14),
            .foregroundColor: NSColor.secondaryLabelColor
        ]
        let size = text.size(withAttributes: attrs)
        text.draw(
            at: NSPoint(x: (bounds.width - size.width) / 2, y: (bounds.height - size.height) / 2),
            withAttributes: attrs
        )
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    private let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    private var corePython = ""
    private var watchlist: [String] = []

    private let window = NSWindow(
        contentRect: NSRect(x: 0, y: 0, width: 1160, height: 760),
        styleMask: [.titled, .closable, .miniaturizable, .resizable],
        backing: .buffered,
        defer: false
    )

    private let symbolField = NSTextField(string: "688766")
    private let modePopup = NSPopUpButton()
    private let watchlistView = NSStackView()
    private let titleLabel = NSTextField(labelWithString: "未选择股票")
    private let statusLabel = NSTextField(labelWithString: "就绪")
    private let priceLabel = NSTextField(labelWithString: "--")
    private let summaryLabel = NSTextField(labelWithString: "搜索或选择一只股票开始。")
    private let metricsLabel = NSTextField(labelWithString: "--")
    private let detailText = NSTextView()
    private let klineView = KlineView()
    private let klineNote = NSTextField(labelWithString: "暂无 K 线")

    func applicationDidFinishLaunching(_ notification: Notification) {
        do {
            corePython = try detectCorePython()
        } catch {
            showError(error.localizedDescription)
            NSApp.terminate(nil)
            return
        }

        buildUI()
        refreshWatchlist()
        window.center()
        window.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    private func buildUI() {
        window.title = "简化股票监控"
        guard let content = window.contentView else { return }

        let rootStack = NSStackView()
        rootStack.orientation = .horizontal
        rootStack.spacing = 16
        rootStack.translatesAutoresizingMaskIntoConstraints = false
        content.addSubview(rootStack)
        NSLayoutConstraint.activate([
            rootStack.leadingAnchor.constraint(equalTo: content.leadingAnchor, constant: 18),
            rootStack.trailingAnchor.constraint(equalTo: content.trailingAnchor, constant: -18),
            rootStack.topAnchor.constraint(equalTo: content.topAnchor, constant: 18),
            rootStack.bottomAnchor.constraint(equalTo: content.bottomAnchor, constant: -18)
        ])

        let sidebar = NSStackView()
        sidebar.orientation = .vertical
        sidebar.spacing = 10
        sidebar.widthAnchor.constraint(equalToConstant: 300).isActive = true
        rootStack.addArrangedSubview(sidebar)

        let appTitle = NSTextField(labelWithString: "简化股票监控")
        appTitle.font = .boldSystemFont(ofSize: 24)
        sidebar.addArrangedSubview(appTitle)

        let hint = NSTextField(wrappingLabelWithString: "本地原生窗口，不启动服务器，不打开网页。")
        hint.textColor = .secondaryLabelColor
        sidebar.addArrangedSubview(hint)

        symbolField.placeholderString = "输入股票代码，如 688766"
        sidebar.addArrangedSubview(symbolField)

        modePopup.addItems(withTitles: ["normal", "defensive", "crash"])
        sidebar.addArrangedSubview(modePopup)

        sidebar.addArrangedSubview(button("搜索并加入关注", #selector(searchAndAdd)))
        sidebar.addArrangedSubview(button("分析当前股票", #selector(analyzeCurrent)))
        sidebar.addArrangedSubview(button("刷新行情", #selector(refreshQuote)))
        sidebar.addArrangedSubview(button("运行一次监控", #selector(runMonitor)))
        sidebar.addArrangedSubview(button("发送 outbox 告警", #selector(sendAlerts)))

        let watchTitle = NSTextField(labelWithString: "关注池")
        watchTitle.font = .boldSystemFont(ofSize: 15)
        sidebar.addArrangedSubview(watchTitle)

        watchlistView.orientation = .vertical
        watchlistView.spacing = 6
        let scroll = NSScrollView()
        scroll.hasVerticalScroller = true
        scroll.documentView = watchlistView
        scroll.heightAnchor.constraint(greaterThanOrEqualToConstant: 220).isActive = true
        sidebar.addArrangedSubview(scroll)

        let main = NSStackView()
        main.orientation = .vertical
        main.spacing = 12
        rootStack.addArrangedSubview(main)

        let header = NSStackView()
        header.orientation = .horizontal
        header.spacing = 12
        main.addArrangedSubview(header)
        titleLabel.font = .boldSystemFont(ofSize: 26)
        header.addArrangedSubview(titleLabel)
        header.addArrangedSubview(NSView())
        statusLabel.textColor = .secondaryLabelColor
        header.addArrangedSubview(statusLabel)

        priceLabel.font = .boldSystemFont(ofSize: 46)
        main.addArrangedSubview(priceLabel)
        summaryLabel.textColor = .secondaryLabelColor
        main.addArrangedSubview(summaryLabel)
        metricsLabel.font = .monospacedDigitSystemFont(ofSize: 14, weight: .regular)
        main.addArrangedSubview(metricsLabel)

        let split = NSStackView()
        split.orientation = .horizontal
        split.spacing = 14
        main.addArrangedSubview(split)

        let detailScroll = NSScrollView()
        detailScroll.hasVerticalScroller = true
        detailText.isEditable = false
        detailText.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        detailScroll.documentView = detailText
        detailScroll.widthAnchor.constraint(greaterThanOrEqualToConstant: 430).isActive = true
        split.addArrangedSubview(detailScroll)

        let chartBox = NSStackView()
        chartBox.orientation = .vertical
        chartBox.spacing = 8
        split.addArrangedSubview(chartBox)
        klineView.heightAnchor.constraint(equalToConstant: 360).isActive = true
        chartBox.addArrangedSubview(klineView)
        klineNote.textColor = .secondaryLabelColor
        chartBox.addArrangedSubview(klineNote)
    }

    private func button(_ title: String, _ action: Selector) -> NSButton {
        let button = NSButton(title: title, target: self, action: action)
        button.bezelStyle = .rounded
        button.heightAnchor.constraint(equalToConstant: 34).isActive = true
        return button
    }

    @objc private func searchAndAdd() {
        let query = symbolField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !query.isEmpty else { return }
        runAsync("搜索中...") {
            let search = try self.runCore(["search", query])
            let symbol = self.firstSymbol(in: search) ?? query
            _ = try self.runCore(["add", symbol])
            let payload = try self.runCore(["analyze", symbol, "--mode", self.modePopup.titleOfSelectedItem ?? "normal"])
            DispatchQueue.main.async {
                self.refreshWatchlist()
                self.renderAnalysis(payload)
            }
        }
    }

    @objc private func analyzeCurrent() {
        let symbol = symbolField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !symbol.isEmpty else { return }
        runAsync("分析中...") {
            let payload = try self.runCore(["analyze", symbol, "--mode", self.modePopup.titleOfSelectedItem ?? "normal"])
            DispatchQueue.main.async { self.renderAnalysis(payload) }
        }
    }

    @objc private func refreshQuote() {
        let symbol = symbolField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !symbol.isEmpty else { return }
        runAsync("刷新行情中...") {
            let payload = try self.runCore(["quotes", symbol])
            DispatchQueue.main.async {
                self.detailText.string = payload
                self.statusLabel.stringValue = "行情已刷新"
            }
        }
    }

    @objc private func runMonitor() {
        runAsync("监控中...") {
            let payload = try self.runCore(["run-monitor", "--mode", self.modePopup.titleOfSelectedItem ?? "normal"])
            DispatchQueue.main.async {
                self.detailText.string = "【监控结果】\n\(payload)"
                self.statusLabel.stringValue = "监控完成"
            }
        }
    }

    @objc private func sendAlerts() {
        runAsync("发送告警中...") {
            let payload = try self.runCore(["send-alerts"])
            DispatchQueue.main.async {
                self.detailText.string = "【告警发送】\n\(payload)"
                self.statusLabel.stringValue = "告警发送完成"
            }
        }
    }

    @objc private func selectWatch(_ sender: NSButton) {
        symbolField.stringValue = sender.title
        analyzeCurrent()
    }

    private func refreshWatchlist() {
        let payload = (try? runCore(["status"])) ?? "{}"
        watchlist = symbolsFromStatus(payload)
        watchlistView.arrangedSubviews.forEach { view in
            watchlistView.removeArrangedSubview(view)
            view.removeFromSuperview()
        }
        if watchlist.isEmpty {
            let empty = NSTextField(labelWithString: "暂无关注股票")
            empty.textColor = .secondaryLabelColor
            watchlistView.addArrangedSubview(empty)
        } else {
            for symbol in watchlist {
                let b = button(symbol, #selector(selectWatch(_:)))
                watchlistView.addArrangedSubview(b)
            }
        }
    }

    private func renderAnalysis(_ text: String) {
        guard
            let data = text.data(using: .utf8),
            let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let quoteDict = root["quote"] as? [String: Any],
            let klineDict = root["kline"] as? [String: Any],
            let decisionDict = root["decision"] as? [String: Any]
        else {
            detailText.string = text
            return
        }

        let quote = Quote(
            symbol: string(quoteDict, "symbol"),
            name: string(quoteDict, "name"),
            lastPrice: number(quoteDict, "last_price"),
            changePct: number(quoteDict, "change_pct"),
            open: number(quoteDict, "open"),
            high: number(quoteDict, "high"),
            low: number(quoteDict, "low"),
            volumeRatio: number(quoteDict, "volume_ratio"),
            protectionScore: number(quoteDict, "protection_score"),
            alertLevel: string(quoteDict, "alert_level"),
            signalBias: string(quoteDict, "signal_bias"),
            summary: string(quoteDict, "summary")
        )
        let bars = ((klineDict["bars"] as? [[String: Any]]) ?? []).map {
            KlineBar(
                date: string($0, "date"),
                open: number($0, "open"),
                close: number($0, "close"),
                high: number($0, "high"),
                low: number($0, "low"),
                volume: number($0, "volume")
            )
        }
        let reasons = decisionDict["reasons"] as? [String] ?? []
        let payload = AnalysisPayload(
            quote: quote,
            bars: bars,
            trendLabel: string(klineDict, "trend_label"),
            technicalScore: number(klineDict, "technical_score"),
            volumeSummary: string(klineDict, "volume_price_summary"),
            decision: string(decisionDict, "decision"),
            reasons: reasons,
            rawText: text
        )
        titleLabel.stringValue = "\(quote.symbol) \(quote.name)"
        priceLabel.stringValue = String(format: "%.2f", quote.lastPrice)
        summaryLabel.stringValue = "Hermes：保护分 \(Int(quote.protectionScore)) | \(quote.signalBias) | \(quote.summary)"
        metricsLabel.stringValue = String(
            format: "涨跌 %.2f%%   开 %.2f   高 %.2f   低 %.2f   量比 %.2f   风险 %@",
            quote.changePct,
            quote.open,
            quote.high,
            quote.low,
            quote.volumeRatio,
            quote.alertLevel
        )
        detailText.string = """
        【实时行情】
        股票：\(quote.symbol) \(quote.name)
        最新价：\(String(format: "%.2f", quote.lastPrice))
        涨跌幅：\(String(format: "%.2f", quote.changePct))%

        【Hermes 风控】
        保护分：\(Int(quote.protectionScore))
        风险等级：\(quote.alertLevel)
        信号：\(quote.signalBias)
        摘要：\(quote.summary)

        【K 线与量价】
        趋势：\(payload.trendLabel)
        技术分：\(Int(payload.technicalScore))
        量价：\(payload.volumeSummary)

        【投资判断】
        结论：\(payload.decision)
        理由：\(reasons.joined(separator: "；"))
        """
        klineView.bars = bars
        if let latest = bars.last {
            klineNote.stringValue = "\(latest.date) | 开 \(latest.open) 收 \(latest.close) 高 \(latest.high) 低 \(latest.low) | 共 \(bars.count) 根"
        } else {
            klineNote.stringValue = "暂无 K 线数据"
        }
        statusLabel.stringValue = "就绪"
    }

    private func runAsync(_ status: String, work: @escaping () throws -> Void) {
        statusLabel.stringValue = status
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try work()
                DispatchQueue.main.async {
                    if self.statusLabel.stringValue == status {
                        self.statusLabel.stringValue = "就绪"
                    }
                }
            } catch {
                DispatchQueue.main.async {
                    self.statusLabel.stringValue = "执行失败"
                    self.showError(error.localizedDescription)
                }
            }
        }
    }

    private func runCore(_ args: [String]) throws -> String {
        let process = Process()
        process.currentDirectoryURL = root
        process.executableURL = URL(fileURLWithPath: corePython)
        process.arguments = ["simplified_stock_monitor.py"] + args
        let output = Pipe()
        let error = Pipe()
        process.standardOutput = output
        process.standardError = error
        try process.run()
        process.waitUntilExit()
        let stdout = String(data: output.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        let stderr = String(data: error.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        if process.terminationStatus != 0 {
            throw NSError(domain: "SimplifiedStockMonitor", code: Int(process.terminationStatus), userInfo: [
                NSLocalizedDescriptionKey: stderr.isEmpty ? stdout : stderr
            ])
        }
        return stdout
    }

    private func detectCorePython() throws -> String {
        let candidates = [
            ProcessInfo.processInfo.environment["HERMES_CORE_PYTHON"],
            ProcessInfo.processInfo.environment["HERMES_PYTHON_BIN"],
            root.appendingPathComponent(".venv/bin/python").path,
            "/Users/starfeld/.pyenv/versions/3.11.12/bin/python",
            "/opt/homebrew/bin/python3.11",
            "/usr/bin/python3"
        ].compactMap { $0 }.filter { !$0.isEmpty }

        for candidate in candidates {
            let process = Process()
            process.executableURL = URL(fileURLWithPath: candidate)
            process.arguments = ["-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"]
            process.standardOutput = Pipe()
            process.standardError = Pipe()
            do {
                try process.run()
                process.waitUntilExit()
                if process.terminationStatus == 0 {
                    return candidate
                }
            } catch {
                continue
            }
        }
        throw NSError(domain: "SimplifiedStockMonitor", code: 1, userInfo: [
            NSLocalizedDescriptionKey: "找不到 Python 3.10+。请安装 Python 3.11 或设置 HERMES_CORE_PYTHON。"
        ])
    }

    private func firstSymbol(in json: String) -> String? {
        guard
            let data = json.data(using: .utf8),
            let array = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]]
        else { return nil }
        return array.first?["symbol"] as? String
    }

    private func symbolsFromStatus(_ json: String) -> [String] {
        guard
            let data = json.data(using: .utf8),
            let root = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
            let items = root["watchlist"] as? [[String: Any]]
        else { return [] }
        return items.compactMap { item in
            if (item["enabled"] as? Bool) == false { return nil }
            return item["symbol"] as? String
        }
    }

    private func string(_ dict: [String: Any], _ key: String) -> String {
        if let value = dict[key] as? String { return value }
        if let value = dict[key] { return String(describing: value) }
        return "-"
    }

    private func number(_ dict: [String: Any], _ key: String) -> Double {
        if let value = dict[key] as? Double { return value }
        if let value = dict[key] as? Int { return Double(value) }
        if let value = dict[key] as? String { return Double(value) ?? 0 }
        return 0
    }

    private func showError(_ message: String) {
        let alert = NSAlert()
        alert.messageText = "简化股票监控"
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.runModal()
    }
}

let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
