#!/usr/bin/env wish

set appTitle "简化股票监控"
wm title . $appTitle
wm geometry . 1120x720
wm minsize . 960 620

set rootDir [file dirname [info script]]
cd $rootDir

proc detectCorePython {} {
    set candidates {}
    if {[info exists ::env(HERMES_CORE_PYTHON)] && $::env(HERMES_CORE_PYTHON) ne ""} {
        lappend candidates $::env(HERMES_CORE_PYTHON)
    }
    if {[info exists ::env(HERMES_PYTHON_BIN)] && $::env(HERMES_PYTHON_BIN) ne ""} {
        lappend candidates $::env(HERMES_PYTHON_BIN)
    }
    lappend candidates \
        [file join [pwd] ".venv" "bin" "python"] \
        "/Users/starfeld/.pyenv/versions/3.11.12/bin/python" \
        "/opt/homebrew/bin/python3.11" \
        "python3.11" \
        "python3.10"

    foreach candidate $candidates {
        if {[catch {exec $candidate -c {import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)}}] == 0} {
            return $candidate
        }
    }
    return ""
}

set corePython [detectCorePython]
if {$corePython eq ""} {
    tk_messageBox -title $appTitle -icon error -message "需要 Python 3.10+ 作为股票监控核心。\n请设置 HERMES_CORE_PYTHON。"
    exit 1
}

set selectedSymbol ""
set hermesMode "normal"
set statusText "就绪 | 核心 $corePython"
set summaryText "搜索或选择一只股票开始。"
set klineText "暂无 K 线数据"

proc pycmd {args} {
    global corePython
    set command [list $corePython "simplified_stock_monitor.py"]
    foreach item $args {
        lappend command $item
    }
    if {[catch {exec {*}$command} output]} {
        error $output
    }
    return $output
}

proc setStatus {text} {
    global statusText
    set statusText $text
    update idletasks
}

proc showText {text} {
    .main.panes.left.text configure -state normal
    .main.panes.left.text delete 1.0 end
    .main.panes.left.text insert end $text
    .main.panes.left.text configure -state disabled
}

proc refreshWatchlist {} {
    .side.watch.list delete 0 end
    if {[catch {pycmd status} output]} {
        setStatus "关注池读取失败"
        return
    }
    set matches [regexp -all -inline {"symbol": "[^"]+"} $output]
    foreach match $matches {
        regexp {"symbol": "([^"]+)"} $match -> symbol
        .side.watch.list insert end $symbol
    }
}

proc parseJsonString {json key} {
    set pattern "\"$key\": \"(\[^\"\]*)\""
    if {[regexp $pattern $json -> value]} {
        return $value
    }
    return "-"
}

proc parseJsonNumber {json key} {
    set pattern "\"$key\": (-?\[0-9.\]+)"
    if {[regexp $pattern $json -> value]} {
        return $value
    }
    return "-"
}

proc drawKline {json} {
    global klineText
    set canvas .main.panes.right.canvas
    $canvas delete all

    set barPattern {\{"date": "([^"]+)", "open": (-?[0-9.]+), "close": (-?[0-9.]+), "high": (-?[0-9.]+), "low": (-?[0-9.]+)}
    set rawBars [regexp -all -inline $barPattern $json]
    if {[llength $rawBars] == 0} {
        set klineText "暂无 K 线数据"
        return
    }

    set bars {}
    foreach {_ date open close high low} $rawBars {
        lappend bars [list $date $open $close $high $low]
    }
    if {[llength $bars] > 50} {
        set bars [lrange $bars end-49 end]
    }

    set width [winfo width $canvas]
    set height [winfo height $canvas]
    if {$width < 420} { set width 420 }
    if {$height < 300} { set height 300 }
    set pad 24
    set maxPrice -1
    set minPrice 999999999
    foreach bar $bars {
        set high [lindex $bar 3]
        set low [lindex $bar 4]
        if {$high > $maxPrice} { set maxPrice $high }
        if {$low < $minPrice} { set minPrice $low }
    }
    set span [expr {$maxPrice - $minPrice}]
    if {$span <= 0} { set span 1 }
    set chartH [expr {$height - $pad * 2}]
    set gap [expr {double($width - $pad * 2) / max([llength $bars], 1)}]
    set candleW [expr {max(3, min(9, $gap * 0.55))}]

    set i 0
    foreach bar $bars {
        lassign $bar date open close high low
        set x [expr {$pad + $gap * $i + $gap / 2}]
        set yHigh [expr {$pad + ($maxPrice - $high) / $span * $chartH}]
        set yLow [expr {$pad + ($maxPrice - $low) / $span * $chartH}]
        set yOpen [expr {$pad + ($maxPrice - $open) / $span * $chartH}]
        set yClose [expr {$pad + ($maxPrice - $close) / $span * $chartH}]
        set color [expr {$close >= $open ? "#0e7c66" : "#c4493a"}]
        $canvas create line $x $yHigh $x $yLow -fill $color
        set top [expr {min($yOpen, $yClose)}]
        set bottom [expr {max($yOpen, $yClose)}]
        if {abs($bottom - $top) < 2} { set bottom [expr {$top + 2}] }
        $canvas create rectangle [expr {$x - $candleW / 2}] $top [expr {$x + $candleW / 2}] $bottom -outline $color -fill $color
        incr i
    }

    set latest [lindex $bars end]
    set klineText "[lindex $latest 0] | 开 [lindex $latest 1] 收 [lindex $latest 2] 高 [lindex $latest 3] 低 [lindex $latest 4] | 共 [llength $bars] 根"
}

proc renderAnalysis {json} {
    global summaryText selectedSymbol
    set symbol [parseJsonString $json symbol]
    set name [parseJsonString $json name]
    set last [parseJsonNumber $json last_price]
    set change [parseJsonNumber $json change_pct]
    set protection [parseJsonNumber $json protection_score]
    set signal [parseJsonString $json signal_bias]
    set alert [parseJsonString $json alert_level]
    set trend [parseJsonString $json trend_label]
    set tech [parseJsonNumber $json technical_score]
    set decision [parseJsonString $json decision]
    set summary [parseJsonString $json summary]
    set volSummary [parseJsonString $json volume_price_summary]

    set selectedSymbol $symbol
    .main.header.title configure -text "$symbol $name"
    set summaryText "最新 $last | 涨跌 $change% | 保护分 $protection | $signal"

    showText "【实时行情】\n股票：$symbol $name\n最新价：$last    涨跌幅：$change%\n\n【Hermes 风控】\n保护分：$protection    等级：$alert\n信号：$signal\n摘要：$summary\n\n【K 线与量价】\n趋势：$trend    技术分：$tech\n量价总结：$volSummary\n\n【投资判断】\n结论：$decision\n"
    drawKline $json
}

proc searchAndAdd {} {
    global selectedSymbol hermesMode
    set query [.side.search.entry get]
    if {$query eq ""} { return }
    setStatus "搜索中..."
    if {[catch {
        set searchOutput [pycmd search $query]
        if {[regexp {"symbol": "([^"]+)"} $searchOutput -> symbol]} {
            pycmd add $symbol
        } else {
            set symbol $query
        }
        set selectedSymbol $symbol
        refreshWatchlist
        set analysis [pycmd analyze $symbol --mode $hermesMode]
        renderAnalysis $analysis
        setStatus "就绪"
    } err]} {
        setStatus "执行失败"
        tk_messageBox -title $::appTitle -icon error -message $err
    }
}

proc analyzeSelected {} {
    global selectedSymbol hermesMode
    set symbol $selectedSymbol
    if {$symbol eq ""} {
        set symbol [.side.search.entry get]
    }
    if {$symbol eq ""} { return }
    setStatus "分析中..."
    if {[catch {
        set analysis [pycmd analyze $symbol --mode $hermesMode]
        renderAnalysis $analysis
        setStatus "就绪"
    } err]} {
        setStatus "执行失败"
        tk_messageBox -title $::appTitle -icon error -message $err
    }
}

proc onWatchSelect {} {
    global selectedSymbol
    set index [.side.watch.list curselection]
    if {$index eq ""} { return }
    set selectedSymbol [.side.watch.list get $index]
    analyzeSelected
}

proc runMonitor {} {
    global hermesMode
    setStatus "监控中..."
    if {[catch {
        set output [pycmd run-monitor --mode $hermesMode]
        showText "【监控结果】\n$output"
        setStatus "就绪"
    } err]} {
        setStatus "执行失败"
        tk_messageBox -title $::appTitle -icon error -message $err
    }
}

proc sendAlerts {} {
    setStatus "发送告警中..."
    if {[catch {
        set output [pycmd send-alerts]
        showText "【告警发送】\n$output"
        setStatus "就绪"
    } err]} {
        setStatus "执行失败"
        tk_messageBox -title $::appTitle -icon error -message $err
    }
}

proc configureAlerts {} {
    set target [tk_getSaveFile -title "输入告警目标请取消此窗口，暂用命令行 config-alerts 配置"]
    if {$target ne ""} {
        return
    }
    tk_messageBox -title $::appTitle -message "请暂用终端配置：\npython3 simplified_stock_monitor.py config-alerts --target pushplus:YOUR_TOKEN"
}

ttk::frame .side -padding 14
grid .side -row 0 -column 0 -sticky ns
grid columnconfigure . 1 -weight 1
grid rowconfigure . 0 -weight 1

ttk::label .side.title -text $appTitle -font {Helvetica 18 bold}
grid .side.title -row 0 -column 0 -sticky w -pady {0 10}

ttk::labelframe .side.search -text "搜索与操作" -padding 8
grid .side.search -row 1 -column 0 -sticky ew
ttk::entry .side.search.entry -width 28
.side.search.entry insert 0 "688766"
grid .side.search.entry -row 0 -column 0 -sticky ew -pady {0 6}
ttk::button .side.search.add -text "搜索并加入关注" -command searchAndAdd
ttk::button .side.search.analyze -text "分析当前股票" -command analyzeSelected
ttk::button .side.search.monitor -text "运行一次监控" -command runMonitor
ttk::button .side.search.send -text "发送告警" -command sendAlerts
grid .side.search.add -row 1 -column 0 -sticky ew -pady 2
grid .side.search.analyze -row 2 -column 0 -sticky ew -pady 2
grid .side.search.monitor -row 3 -column 0 -sticky ew -pady 2
grid .side.search.send -row 4 -column 0 -sticky ew -pady 2

ttk::labelframe .side.mode -text "Hermes 模式" -padding 8
grid .side.mode -row 2 -column 0 -sticky ew -pady {10 0}
ttk::radiobutton .side.mode.normal -text "正常" -variable hermesMode -value normal
ttk::radiobutton .side.mode.defensive -text "防守" -variable hermesMode -value defensive
ttk::radiobutton .side.mode.crash -text "崩坏" -variable hermesMode -value crash
grid .side.mode.normal -row 0 -column 0 -sticky w
grid .side.mode.defensive -row 0 -column 1 -sticky w
grid .side.mode.crash -row 0 -column 2 -sticky w

ttk::labelframe .side.watch -text "关注池" -padding 8
grid .side.watch -row 3 -column 0 -sticky nsew -pady {10 0}
grid rowconfigure .side 3 -weight 1
listbox .side.watch.list -height 16
grid .side.watch.list -row 0 -column 0 -sticky nsew
grid rowconfigure .side.watch 0 -weight 1
grid columnconfigure .side.watch 0 -weight 1
bind .side.watch.list <<ListboxSelect>> onWatchSelect
ttk::button .side.watch.refresh -text "刷新关注池" -command refreshWatchlist
grid .side.watch.refresh -row 1 -column 0 -sticky ew -pady {8 0}

ttk::frame .main -padding {6 14 14 14}
grid .main -row 0 -column 1 -sticky nsew
grid columnconfigure .main 0 -weight 1
grid rowconfigure .main 2 -weight 1

ttk::frame .main.header
grid .main.header -row 0 -column 0 -sticky ew
grid columnconfigure .main.header 0 -weight 1
ttk::label .main.header.title -text "未选择股票" -font {Helvetica 20 bold}
ttk::label .main.header.status -textvariable statusText
grid .main.header.title -row 0 -column 0 -sticky w
grid .main.header.status -row 0 -column 1 -sticky e

ttk::label .main.summary -textvariable summaryText -wraplength 820
grid .main.summary -row 1 -column 0 -sticky ew -pady {8 10}

ttk::panedwindow .main.panes -orient horizontal
grid .main.panes -row 2 -column 0 -sticky nsew
ttk::frame .main.panes.left -padding 8
ttk::frame .main.panes.right -padding 8
.main.panes add .main.panes.left -weight 1
.main.panes add .main.panes.right -weight 1
grid rowconfigure .main.panes.left 1 -weight 1
grid columnconfigure .main.panes.left 0 -weight 1
grid rowconfigure .main.panes.right 1 -weight 1
grid columnconfigure .main.panes.right 0 -weight 1

ttk::label .main.panes.left.title -text "行情 / Hermes / 投资判断" -font {Helvetica 13 bold}
text .main.panes.left.text -height 20 -wrap word -state disabled
grid .main.panes.left.title -row 0 -column 0 -sticky w
grid .main.panes.left.text -row 1 -column 0 -sticky nsew -pady {8 0}

ttk::label .main.panes.right.title -text "简化 K 线" -font {Helvetica 13 bold}
canvas .main.panes.right.canvas -background "#f7fafc" -height 330 -highlightthickness 1 -highlightbackground "#d6e0e6"
ttk::label .main.panes.right.note -textvariable klineText -wraplength 420
grid .main.panes.right.title -row 0 -column 0 -sticky w
grid .main.panes.right.canvas -row 1 -column 0 -sticky nsew -pady {8 0}
grid .main.panes.right.note -row 2 -column 0 -sticky ew -pady {8 0}

bind .side.search.entry <Return> searchAndAdd
refreshWatchlist
