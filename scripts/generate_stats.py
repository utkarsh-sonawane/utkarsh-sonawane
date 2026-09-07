#!/usr/bin/env python3
"""Generate profile headings and language breakdown SVGs.

Inspired by Andrii Drok's profile architecture (andriidrok1/andriidrok1),
adapted for Utkarsh Sonawane's profile.

Outputs:
  assets/generated/hd-about.svg
  assets/generated/hd-stack.svg
  assets/generated/hd-projects.svg
  assets/generated/hd-langs.svg
  assets/generated/hd-colophon.svg
  assets/generated/langs.svg

No external dependencies — standard library only.
Inlines subset JetBrains Mono (OFL) to pin advance geometry at 0.600 em.
Uses pure SMIL animations (clipPath reveals with traveling cursor) and
dual-theme CSS via @media (prefers-color-scheme: dark).
"""
import argparse
import base64
import functools
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "assets", "generated")
FONT_DIR = os.path.join(HERE, "fonts")

WIDTH = 620
LEFT = 34
REVEAL = 0.95
API = "https://api.github.com/graphql"

# Verified factual snapshot across sonawaneutkarsh's 12 public non-fork repos
FACTUAL_LANGS_BY_SIZE = [
    ("Python", 312076),
    ("TypeScript", 290792),
    ("JavaScript", 156759),
    ("Shell", 45404),
    ("C++", 4478),
]
FACTUAL_LANGS_BY_REPO = [
    ("Python", 5),
    ("TypeScript", 3),
    ("JavaScript", 3),
    ("C++", 1),
]

# GitHub dark and light palette
LIGHT = dict(data="#6e7681", emph="#424a53", dim="#8c959f", rule="#d8dee4", surface="#ffffff")
DARK = dict(data="#c9d1d9", emph="#f0f6fc", dim="#8b949e", rule="#30363d", surface="#0d1117")

MONO = "JBMono,ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


@functools.lru_cache(maxsize=None)
def face(filename, weight):
    path = os.path.join(FONT_DIR, filename)
    if not os.path.isfile(path):
        return ""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return (
        f"@font-face{{font-family:JBMono;font-style:normal;font-weight:{weight};"
        f"font-display:block;src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
    )


def font_text():
    return face("jbmono-400.woff2", 400) + face("jbmono-600.woff2", 600)


def font_head():
    f = face("jbmono-head.woff2", 600)
    if not f:
        f = face("jbmono-600.woff2", 600)
    return f


def style(extra="", font=None):
    def block(t):
        return (
            f".d-f{{fill:{t['data']}}}.d-s{{stroke:{t['data']}}}"
            f".e-f{{fill:{t['emph']}}}.m-f{{fill:{t['dim']}}}"
            f".u-s{{stroke:{t['rule']}}}.r{{stroke:{t['surface']}}}"
        )
    return (
        f"<style>{font or font_text()}"
        f"{block(LIGHT)}.w{{fill:{LIGHT['data']};opacity:.13}}{extra}"
        f"@media(prefers-color-scheme:dark){{{block(DARK)}"
        f".w{{fill:{DARK['data']};opacity:.16}}}}</style>"
    )


def svg_header(w, h, font=None):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" fill="none" font-family="{MONO}">'
        + style(font=font)
    )


def fade(delay, dur=0.45):
    return f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="{dur}s" fill="freeze"/>'


def wipe(cid, x, y, w, h, delay, dur=REVEAL):
    clip = (
        f'<clipPath id="{cid}"><rect x="{x}" y="{y}" height="{h}" width="0">'
        f'<animate attributeName="width" from="0" to="{w}" '
        f'begin="{delay:.2f}s" dur="{dur}s" fill="freeze"/></rect></clipPath>'
    )
    cursor = (
        f'<rect y="{y}" width="2" height="{h}" class="d-f" opacity="0">'
        f'<animate attributeName="x" from="{x}" to="{x + w}" '
        f'begin="{delay:.2f}s" dur="{dur}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.55" begin="{delay:.2f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay + dur:.2f}s"/></rect>'
    )
    return clip, cursor


def label(x, y, text, size=11, cls="m-f", anchor="start", extra=""):
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}"{a}{extra}>{text}</text>'


def hbar(x, y, w, h, cls="d-f", r=3.0):
    if w <= 0.6:
        return ""
    r = min(r, h / 2.0, w)
    return (
        f'<path d="M{x:.1f} {y:.1f}H{x + w - r:.1f}'
        f'Q{x + w:.1f} {y:.1f} {x + w:.1f} {y + r:.1f}'
        f'V{y + h - r:.1f}Q{x + w:.1f} {y + h:.1f} {x + w - r:.1f} {y + h:.1f}'
        f'H{x:.1f}Z" class="{cls}"/>'
    )


def draw_heading(word):
    """Draw a section heading in monospace with a hairline rule extending to 620px."""
    FS = 16
    H = 26
    text_end = len(word) * FS * 0.6 + 18
    p = [svg_header(WIDTH, H, font=font_head())]
    p.append(label(0, 18, word, FS, "e-f", extra=' font-weight="600"'))
    p.append(
        f'<line x1="{text_end:.0f}" y1="12.5" x2="{WIDTH}" y2="12.5" '
        f'class="u-s" stroke-width="1"/>'
    )
    p.append("</svg>")
    return "".join(p)


def draw_langs(by_size, by_repo):
    """Draw two-column language breakdown: by bytes share and by primary repository count."""
    rows = max(len(by_size), len(by_repo), 1)
    H = 26 + rows * 22 + 6
    colw = (WIDTH - LEFT - 30) / 2
    name_w = 84
    bar_max = colw - name_w - 44

    p = [svg_header(WIDTH, H)]
    groups = [
        (LEFT, "by bytes", by_size, True),
        (LEFT + colw + 30, "by repos", by_repo, False),
    ]

    for gi, (gx, title, data, as_pct) in enumerate(groups):
        p.append(
            f'<g opacity="0">{fade(0.10 + gi * 0.10)}'
            + label(gx, 12, title.upper(), 9, "m-f", extra=' letter-spacing="1.3"')
            + '</g>'
        )
        if not data:
            continue
        top = max(v for _, v in data) or 1
        total = sum(v for _, v in data) or 1
        cid = f"rl{gi}"
        clip, cursor = wipe(cid, gx + name_w, 20, bar_max, rows * 22, 0.34 + gi * 0.12, 0.95)
        p.append(clip)
        for ri, (name, val) in enumerate(data):
            y = 26 + ri * 22
            shown = f"{val / total * 100:.0f}%" if as_pct else f"{val}"
            p.append(
                f'<g opacity="0">{fade(0.24 + gi * 0.10 + ri * 0.05)}'
                + label(gx, y + 8, name.lower()[:11], 11, "e-f")
                + label(gx + colw - 6, y + 8, shown, 11, "m-f", "end")
                + '</g>'
            )
            p.append(
                f'<g clip-path="url(#{cid})">'
                + hbar(gx + name_w, y, bar_max * val / top, 7)
                + '</g>'
            )
        p.append(cursor)

    p.append("</svg>")
    return "".join(p)


def fetch_live_data(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        API,
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        payload = json.load(r)
    repos = payload.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    by_size, by_repo = {}, {}
    for node in repos:
        edges = node.get("languages", {}).get("edges", [])
        for e in edges:
            name = e["node"]["name"]
            by_size[name] = by_size.get(name, 0) + e["size"]
        if edges:
            top_lang = edges[0]["node"]["name"]
            by_repo[top_lang] = by_repo.get(top_lang, 0) + 1

    ranked_size = sorted(by_size.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    ranked_repo = sorted(by_repo.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    return ranked_size, ranked_repo


def main():
    parser = argparse.ArgumentParser(description="Generate profile heading and language SVGs.")
    parser.add_argument("--out-dir", default=OUT_DIR, help="Destination directory")
    args = parser.parse_args()

    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    # 1. Generate section headings
    headings = ["about", "stack", "projects", "languages", "colophon"]
    for h in headings:
        path = os.path.join(out_dir, f"hd-{h}.svg")
        content = draw_heading(h)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {path}")

    # 2. Get language data (live API if token available, else factual snapshot)
    token = os.environ.get("GITHUB_TOKEN")
    login = os.environ.get("GH_LOGIN", "sonawaneutkarsh")
    by_size, by_repo = FACTUAL_LANGS_BY_SIZE, FACTUAL_LANGS_BY_REPO
    if token:
        try:
            live_size, live_repo = fetch_live_data(login, token)
            if live_size and live_repo:
                by_size, by_repo = live_size, live_repo
                print("Fetched live language metrics from GitHub API.")
        except Exception as e:
            print(f"Notice: Using cached snapshot (API fetch failed: {e})")
    else:
        print("Using verified repository language metrics snapshot.")

    # 3. Generate langs.svg
    langs_path = os.path.join(out_dir, "langs.svg")
    langs_content = draw_langs(by_size, by_repo)
    with open(langs_path, "w", encoding="utf-8") as f:
        f.write(langs_content)
    print(f"Generated {langs_path}")


if __name__ == "__main__":
    main()
