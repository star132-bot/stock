from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = PROJECT_ROOT / "skills" / "stock-hourly-master-monitor"
SCRIPT_PATH = SKILL_DIR / "scripts" / "hourly_master_monitor.py"
CRON_EXAMPLE_PATH = SKILL_DIR / "examples" / "hermes-cron.yaml"


def load_skill_script():
    assert SCRIPT_PATH.exists(), f"missing script: {SCRIPT_PATH}"
    spec = importlib.util.spec_from_file_location("hourly_master_monitor", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_in_repo_cron_example_is_clone_friendly():
    assert CRON_EXAMPLE_PATH.exists(), f"missing cron example: {CRON_EXAMPLE_PATH}"
    content = CRON_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "schedule: every 1h" in content
    assert "skills/stock-hourly-master-monitor/scripts/hourly_master_monitor.py" in content
    assert "/Users/starfeld/project/stock-realtime-dashboard" in content
    assert "alert_required=true" in content
    assert "MiniMax-M2.7-highspeed" in content


def test_safe_symbol_for_file_keeps_a_share_suffix_readable():
    module = load_skill_script()

    assert module.safe_symbol_for_file("688766.SH") == "688766_SH"
    assert module.safe_symbol_for_file("300750.SZ") == "300750_SZ"


def test_compare_with_previous_flags_hourly_price_jump():
    module = load_skill_script()
    current = {
        "recorded_at": "2026-05-20T02:00:00+00:00",
        "symbol": "688766.SH",
        "quote": {
            "last_price": 103.5,
            "change_pct": 4.8,
            "volume_ratio": 1.2,
        },
    }
    previous = {
        "recorded_at": "2026-05-20T01:00:00+00:00",
        "symbol": "688766.SH",
        "quote": {"last_price": 100.0},
    }
    thresholds = {
        "hourly_move_pct": 3.0,
        "day_change_pct": 5.0,
        "volume_ratio_high": 3.0,
        "volume_ratio_low": 0.3,
    }

    comparison = module.compare_with_previous(current, previous, thresholds)

    assert comparison["alert_required"] is True
    assert comparison["hourly_change_pct"] == 3.5
    assert "hourly_price_move" in comparison["triggers"]


def test_append_and_load_symbol_history_uses_jsonl_per_symbol(tmp_path):
    module = load_skill_script()
    snapshot = {
        "recorded_at": "2026-05-20T02:00:00+00:00",
        "symbol": "688766.SH",
        "quote": {"last_price": 101.2},
    }

    path = module.append_symbol_snapshot(tmp_path, "688766.SH", snapshot)
    history = module.load_symbol_history(tmp_path, "688766.SH", limit=5)

    assert path.name == "688766_SH.jsonl"
    assert history == [snapshot]
    assert json.loads(path.read_text(encoding="utf-8").strip()) == snapshot


def test_build_master_prompt_contains_investment_decision_sections():
    module = load_skill_script()
    payload = {
        "recorded_at": "2026-05-20T02:00:00+00:00",
        "alert_required": True,
        "results": [
            {
                "symbol": "688766.SH",
                "quote": {"name": "普冉股份", "last_price": 101.2, "change_pct": 4.8},
                "comparison": {"alert_required": True, "triggers": ["hourly_price_move"]},
                "decision": {"action": "watch", "summary": "波动放大，等待确认"},
            }
        ],
    }

    prompt = module.build_master_prompt(payload)

    assert "股票大师" in prompt
    assert "投资可行性" in prompt
    assert "历史对比" in prompt
    assert "688766.SH" in prompt
