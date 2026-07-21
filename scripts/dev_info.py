#!/usr/bin/env python
"""Developer helper: print environment / tooling status."""

from __future__ import annotations

import platform
import sys


def main() -> None:
    print(f"python={sys.version.split()[0]}")
    print(f"platform={platform.platform()}")
    print(f"executable={sys.executable}")
    try:
        import forgemind

        print(f"forgemind={forgemind.__version__}")
    except ImportError:
        print("forgemind=not-installed (run: pip install -e '.[dev]')")


if __name__ == "__main__":
    main()
