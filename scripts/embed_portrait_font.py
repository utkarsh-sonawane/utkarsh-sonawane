#!/usr/bin/env python3
"""Inline the ramp subset of JetBrains Mono into portrait.svg.

Ensures the advance width is pinned at exactly 0.600 em (CHAR_W 7.74 at font-size 12.9)
across all operating systems and browsers, eliminating platform font divergence.
Idempotent: running multiple times preserves existing content.
"""
import base64
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "fonts", "jbmono-ramp.woff2")
FAMILY = "JBMono,ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def main():
    target = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.path.join(HERE, "..", "assets", "generated", "portrait.svg")
    )
    target = os.path.abspath(target)

    if not os.path.isfile(target):
        sys.exit(f"Target SVG not found: {target}")

    with open(target, "r", encoding="utf-8") as f:
        svg = f.read()

    if "JBMono" in svg and "data:font/woff2;base64" in svg:
        print(f"{target}: already carries inlined JetBrains Mono")
        return

    if not os.path.isfile(FONT):
        sys.exit(f"Font file not found: {FONT}")

    with open(FONT, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")

    rule = (
        f"@font-face{{font-family:JBMono;font-style:normal;font-weight:400;"
        f"font-display:block;src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
    )

    if "<style>" not in svg:
        sys.exit(f"{target}: no <style> tag found")

    svg = svg.replace("<style>", f"<style>{rule}", 1)
    swapped, n = re.subn(r'font-family="[^"]*"', f'font-family="{FAMILY}"', svg)
    if not n:
        swapped = svg.replace("<svg ", f'<svg font-family="{FAMILY}" ', 1)

    with open(target, "w", encoding="utf-8") as f:
        f.write(swapped)

    print(f"{target}: successfully inlined {len(b64) // 1024} KB JetBrains Mono subset")


if __name__ == "__main__":
    main()
