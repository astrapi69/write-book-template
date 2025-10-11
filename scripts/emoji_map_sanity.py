# scripts/emoji_map_sanity.py
from __future__ import annotations

from emoji_map import EMOJI_MAP  # same directory


def main() -> int:
    if not isinstance(EMOJI_MAP, dict) or not EMOJI_MAP:
        print("❌ EMOJI_MAP must be a non-empty dict")
        return 1
    for k, v in EMOJI_MAP.items():
        if not isinstance(k, str) or not isinstance(v, str):
            print("❌ All keys/values must be str")
            return 1
        if not k:
            print("❌ Empty key found")
            return 1
    print(f"OK. entries={len(EMOJI_MAP)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
