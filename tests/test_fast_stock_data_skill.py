from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = PROJECT_ROOT / "skills" / "hermes-fast-stock-data" / "SKILL.md"


def read_skill() -> str:
    assert SKILL_PATH.exists(), f"missing skill: {SKILL_PATH}"
    return SKILL_PATH.read_text(encoding="utf-8")


def test_fast_stock_data_skill_defines_local_first_workflow():
    content = read_skill()

    assert "name: hermes-fast-stock-data" in content
    assert "Fast path first" in content
    assert ".runtime/stock_latest/<SYMBOL>.json" in content
    assert ".runtime/stock_snapshots/<SYMBOL>.jsonl" in content
    assert "query 688766.SH" in content
    assert "analyze 688766.SH --lookback 240" in content


def test_fast_stock_data_skill_guards_against_slow_refreshes():
    content = read_skill()

    assert "Do not pass `--refresh` by default" in content
    assert "Use `--force` only" in content
    assert "Prefer `run` without `--force`" in content
    assert "cached_quote_fallback" in content
    assert "Never treat a failed live quote with `last_price=0` as a real crash" in content


def test_fast_stock_data_skill_has_api_and_answer_template():
    content = read_skill()

    assert "GET  /api/hermes/stock-monitors/{symbol}/query" in content
    assert "GET  /api/hermes/stock-monitors/{symbol}/analysis" in content
    assert "GET  /api/hermes/capabilities" in content
    assert "股票：<symbol> <name>" in content
    assert "操作倾向：<recommendation label>" in content
    assert "不是投资建议" in content
