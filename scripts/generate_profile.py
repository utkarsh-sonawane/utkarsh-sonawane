#!/usr/bin/env python3
"""Orchestrator to generate/refresh profile assets.

Runs scripts/generate_stats.py to refresh section headings and language metrics.
Portrait generation (scripts/make_portrait.py) is maintained as a dedicated
tool for one-off photographic updates.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GENERATE_STATS = os.path.join(HERE, "generate_stats.py")


def main():
    print("Running profile graphics generator...")
    res = subprocess.run([sys.executable, GENERATE_STATS], check=True)
    sys.exit(res.returncode)


if __name__ == "__main__":
    main()
