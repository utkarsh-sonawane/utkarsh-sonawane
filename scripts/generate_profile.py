#!/usr/bin/env python3
"""Generate profile SVG assets for sonawaneutkarsh/sonawaneutkarsh.

Produces:
    assets/generated/hero-dark.svg
    assets/generated/hero-light.svg
    assets/generated/activity-dark.svg
    assets/generated/activity-light.svg

Usage:
    python scripts/generate_profile.py

Set GITHUB_TOKEN to fetch live contribution data from the GitHub GraphQL API.
Without a token, cached data (assets/generated/activity-cache.json) is used if present.
Without either, a deterministic "awaiting first refresh" placeholder is generated.
No synthetic or fabricated activity data is ever generated.

No third-party dependencies required — stdlib only.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path


# ── Paths ──────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"
CACHE_FILE = ASSETS_DIR / "activity-cache.json"

USERNAME = "sonawaneutkarsh"


# ── Typography ─────────────────────────────────────────────────────

FONT = (
    "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, "
    "'Liberation Mono', monospace"
)


# ── Color themes ───────────────────────────────────────────────────

THEMES = {
    "dark": {
        "bg":     "#0d1117",
        "border": "#30363d",
        "text":   "#e6edf3",
        "muted":  "#7d8590",
        "node":   "#484f58",
        "accent": "#58a6ff",
        "cell_0": "#161b22",
        "cell_1": "#1c2d41",
        "cell_2": "#1f4068",
        "cell_3": "#2a6db5",
        "cell_4": "#58a6ff",
    },
    "light": {
        "bg":     "#ffffff",
        "border": "#d0d7de",
        "text":   "#1f2328",
        "muted":  "#656d76",
        "node":   "#8c959f",
        "accent": "#0969da",
        "cell_0": "#eaeef2",
        "cell_1": "#c8d7e5",
        "cell_2": "#7baacc",
        "cell_3": "#3b7ec2",
        "cell_4": "#0969da",
    },
}


# ═══════════════════════════════════════════════════════════════════
# HERO SVG
# ═══════════════════════════════════════════════════════════════════
#
# A sparse NEAT-inspired topology: nodes connected by thin edges,
# framing the name and tagline. One accent node pulses subtly.
# All coordinates are deterministic.

HERO_W, HERO_H = 840, 260

# (x, y, radius) — fixed positions forming an asymmetric topology
NODES = [
    # Left cluster
    (62,  52,  3.0),   #  0
    (48,  100, 2.5),   #  1
    (68,  148, 2.0),   #  2
    (55,  196, 2.5),   #  3
    (72,  238, 2.0),   #  4
    # Right cluster
    (778, 48,  2.5),   #  5
    (792, 108, 3.0),   #  6
    (772, 168, 2.0),   #  7
    (785, 222, 2.5),   #  8
    # Top scatter
    (198, 30,  2.0),   #  9
    (645, 36,  2.0),   # 10
    # Bottom scatter
    (200, 242, 2.0),   # 11
    (648, 240, 2.0),   # 12
    # Accent node
    (148, 142, 3.5),   # 13
]

# (from_index, to_index)
EDGES = [
    (0, 1),    #  0  left chain
    (1, 2),    #  1
    (2, 3),    #  2
    (3, 4),    #  3
    (5, 6),    #  4  right chain
    (6, 7),    #  5
    (7, 8),    #  6
    (0, 9),    #  7  left-top → top-scatter
    (9, 10),   #  8  long top arc             ← dashed
    (10, 5),   #  9  top-scatter → right-top
    (3, 11),   # 10  left-lower → bottom-scatter
    (11, 12),  # 11  long bottom arc          ← dashed
    (12, 8),   # 12  bottom-scatter → right-bottom
    (2, 13),   # 13  left-mid → accent
    (13, 11),  # 14  accent → bottom-scatter
]

DASHED_EDGES = {8, 11}
ACCENT_NODE = 13

# Innovation labels hint at NEAT's innovation tracking
INNOVATIONS = [
    (7,  "i3"),
    (13, "i7"),
]


def _hero_svg(t):
    """Build hero SVG for the given theme dict."""
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {HERO_W} {HERO_H}"'
        f' width="{HERO_W}" height="{HERO_H}"'
        f' role="img"'
        f' aria-label="Utkarsh Sonawane — systems from first principles">',
        f'<title>Utkarsh Sonawane — systems from first principles</title>',
        f'<rect width="{HERO_W}" height="{HERO_H}" fill="{t["bg"]}"/>',
    ]

    # ── Edges ──
    for i, (a, b) in enumerate(EDGES):
        ax, ay, _ = NODES[a]
        bx, by, _ = NODES[b]
        dashed = i in DASHED_EDGES
        dash_attr = ' stroke-dasharray="6 4"' if dashed else ""
        opacity = "0.3" if dashed else "0.5"
        lines.append(
            f'<line x1="{ax}" y1="{ay}" x2="{bx}" y2="{by}"'
            f' stroke="{t["border"]}" stroke-width="0.8"'
            f' opacity="{opacity}"{dash_attr}/>'
        )

    # ── Innovation labels ──
    for edge_i, label in INNOVATIONS:
        a, b = EDGES[edge_i]
        ax, ay, _ = NODES[a]
        bx, by, _ = NODES[b]
        mx = (ax + bx) / 2
        my = (ay + by) / 2 - 7
        lines.append(
            f'<text x="{mx}" y="{my}" fill="{t["muted"]}"'
            f' font-family="{FONT}" font-size="7"'
            f' text-anchor="middle" opacity="0.4">{label}</text>'
        )

    # ── Nodes ──
    for j, (x, y, r) in enumerate(NODES):
        if j == ACCENT_NODE:
            # Soft glow
            lines.append(
                f'<circle cx="{x}" cy="{y}" r="12"'
                f' fill="{t["accent"]}" opacity="0.07"/>'
            )
            # Core with subtle SMIL pulse
            lines.append(
                f'<circle cx="{x}" cy="{y}" r="{r}"'
                f' fill="{t["accent"]}" opacity="0.85">'
                f'<animate attributeName="opacity"'
                f' values="0.6;1;0.6" dur="4s" repeatCount="indefinite"/>'
                f'</circle>'
            )
        else:
            lines.append(
                f'<circle cx="{x}" cy="{y}" r="{r}"'
                f' fill="{t["node"]}" opacity="0.45"/>'
            )

    # ── Name ──
    cx = HERO_W / 2
    lines.append(
        f'<text x="{cx}" y="118" fill="{t["text"]}"'
        f' font-family="{FONT}" font-size="28" font-weight="600"'
        f' text-anchor="middle" letter-spacing="3">'
        f'UTKARSH SONAWANE</text>'
    )

    # ── Tagline ──
    lines.append(
        f'<text x="{cx}" y="148" fill="{t["muted"]}"'
        f' font-family="{FONT}" font-size="12"'
        f' text-anchor="middle" letter-spacing="1">'
        f'systems from first principles</text>'
    )

    lines.append("</svg>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# ACTIVITY DATA
# ═══════════════════════════════════════════════════════════════════

def _clean_calendar(cal):
    """Retain only the minimal day/date/count information required for generation."""
    if not cal or "weeks" not in cal:
        return None
    clean_weeks = []
    for w in cal.get("weeks", []):
        clean_days = []
        for d in w.get("contributionDays", []):
            clean_days.append({
                "contributionCount": d.get("contributionCount", 0),
                "date": d.get("date", ""),
                "weekday": d.get("weekday", 0),
            })
        clean_weeks.append({"contributionDays": clean_days})
    return {
        "totalContributions": cal.get("totalContributions", 0),
        "weeks": clean_weeks,
    }


def _fetch_contributions(token):
    """Query GitHub GraphQL for the public contribution calendar.

    Explicitly targets the public user login sonawaneutkarsh rather than viewer,
    ensuring correct operation under GitHub Actions GITHUB_TOKEN.
    """
    query = (
        '{ user(login: "' + USERNAME + '") {'
        "  contributionsCollection {"
        "    contributionCalendar {"
        "      totalContributions"
        "      weeks {"
        "        contributionDays {"
        "          contributionCount"
        "          date"
        "          weekday"
        "        }"
        "      }"
        "    }"
        "  }"
        "} }"
    )
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "sonawaneutkarsh-profile-gen",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        if "errors" in data:
            print(f"  graphql errors: {data['errors']}", file=sys.stderr)
            return None
        cal = data.get("data", {}).get("user", {}).get("contributionsCollection", {}).get("contributionCalendar")
        return _clean_calendar(cal)
    except Exception as exc:
        print(f"  fetch failed: {exc}", file=sys.stderr)
        return None


def _load_cache():
    try:
        data = json.loads(CACHE_FILE.read_text())
        return _clean_calendar(data)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def _save_cache(cal):
    cleaned = _clean_calendar(cal)
    if cleaned:
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cleaned, indent=2, sort_keys=True) + "\n")


# ═══════════════════════════════════════════════════════════════════
# ACTIVITY SVG
# ═══════════════════════════════════════════════════════════════════

CELL = 11
GAP = 3
STEP = CELL + GAP          # 14
ROWS = 7
PAD_T = 20
PAD_B = 40
ACT_W = 840
ACT_H = PAD_T + ROWS * STEP + PAD_B   # 158


def _quartile_levels(counts):
    """Return a function mapping contribution count → level 0-4."""
    nonzero = sorted(c for c in counts if c > 0)
    if not nonzero:
        return lambda c: 0
    n = len(nonzero)
    q1 = nonzero[n // 4]
    q2 = nonzero[n // 2]
    q3 = nonzero[3 * n // 4]

    def assign(count):
        if count == 0:
            return 0
        if count <= q1:
            return 1
        if count <= q2:
            return 2
        if count <= q3:
            return 3
        return 4

    return assign


def _activity_svg(t, cal):
    """Build activity grid SVG.

    Derives visual columns dynamically from the returned calendar weeks
    (typically 52 or 53 weeks) rather than hardcoding or truncating weeks.
    Accurately represents all dates returned by the calendar.
    """
    palette = [t["cell_0"], t["cell_1"], t["cell_2"], t["cell_3"], t["cell_4"]]

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {ACT_W} {ACT_H}" width="{ACT_W}" height="{ACT_H}"'
        f' role="img" aria-label="GitHub contribution activity">',
        f'<title>GitHub contribution activity</title>',
        f'<rect width="{ACT_W}" height="{ACT_H}" fill="{t["bg"]}"/>',
    ]

    weeks = cal.get("weeks", []) if cal else []
    if not weeks:
        lines.append(
            f'<text x="{ACT_W / 2}" y="{ACT_H / 2}" fill="{t["muted"]}"'
            f' font-family="{FONT}" font-size="11"'
            f' text-anchor="middle">activity data awaiting first workflow refresh</text>'
        )
        lines.append("</svg>")
        return "\n".join(lines)

    # Collect all counts to calculate quartile levels
    all_counts = []
    start_date = None
    end_date = None
    for week in weeks:
        days = week.get("contributionDays", [])
        if days:
            if start_date is None:
                start_date = days[0].get("date")
            end_date = days[-1].get("date")
            for day in days:
                all_counts.append(day.get("contributionCount", 0))

    level_fn = _quartile_levels(all_counts)

    num_cols = len(weeks)
    grid_width = (num_cols - 1) * STEP + CELL
    pad_x = max(20, round((ACT_W - grid_width) / 2))

    total = sum(all_counts)
    active = sum(1 for c in all_counts if c > 0)

    for col_idx, week in enumerate(weeks):
        for day in week.get("contributionDays", []):
            count = day.get("contributionCount", 0)
            weekday = day.get("weekday", 0)
            lvl = level_fn(count)
            x = pad_x + col_idx * STEP
            y = PAD_T + weekday * STEP
            lines.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}"'
                f' rx="2" fill="{palette[lvl]}"/>'
            )

    # Summary metrics aligned with grid
    my = PAD_T + ROWS * STEP + 28
    date_range_str = f" ({start_date} to {end_date})" if start_date and end_date else ""
    lines.append(
        f'<text x="{pad_x}" y="{my}" fill="{t["muted"]}"'
        f' font-family="{FONT}" font-size="11">'
        f'<tspan fill="{t["text"]}" font-weight="500">{total:,}</tspan>'
        f" contributions"
        f' \u00b7 <tspan fill="{t["text"]}" font-weight="500">{active}</tspan>'
        f" active days"
        f'<tspan fill="{t["muted"]}" font-size="10">{date_range_str}</tspan>'
        f"</text>"
    )

    lines.append("</svg>")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    print("generate_profile")

    # ── Hero ──
    for name in ("dark", "light"):
        svg = _hero_svg(THEMES[name])
        dest = ASSETS_DIR / f"hero-{name}.svg"
        dest.write_text(svg)
        print(f"  {dest.relative_to(ROOT)}")

    # ── Contribution data ──
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    cal = None

    if token:
        print("  fetching contributions via GraphQL ...")
        cal = _fetch_contributions(token)
        if cal:
            _save_cache(cal)
            print("  cache updated")

    if cal is None:
        cal = _load_cache()
        if cal:
            print("  using cached contribution data")
        else:
            print("  no verified contribution data available — generating awaiting-refresh state")

    # ── Activity ──
    for name in ("dark", "light"):
        svg = _activity_svg(THEMES[name], cal)
        dest = ASSETS_DIR / f"activity-{name}.svg"
        dest.write_text(svg)
        print(f"  {dest.relative_to(ROOT)}")

    print("done")


if __name__ == "__main__":
    main()
