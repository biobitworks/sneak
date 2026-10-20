from __future__ import annotations

import json
import sys

from . import healthcheck


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--check"] or args == []:
        print(json.dumps(healthcheck(), sort_keys=True))
        return 0
    print("usage: python -m security_demo --check", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
