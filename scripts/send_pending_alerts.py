#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sender import flush_outbox, retry_failed, sender_env_help  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Send pending Hermes stock alerts from outbox.")
    parser.add_argument("--limit", type=int, default=None, help="Only send up to N pending records")
    parser.add_argument("--retry-failed", action="store_true", help="Reset failed records to pending before sending")
    parser.add_argument("--help-targets", action="store_true", help="Print supported target channel formats")
    args = parser.parse_args()

    if args.help_targets:
        print(json.dumps(sender_env_help(), ensure_ascii=False, indent=2))
        return 0

    result = retry_failed(limit=args.limit) if args.retry_failed else flush_outbox(limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
