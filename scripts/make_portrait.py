#!/usr/bin/env python3
"""
Generate a recognizable monochrome stipple / contour SVG portrait for GitHub profile.

Pipeline:
  1. Load source photograph (face.png), crop centered on head and collar.
  2. Segment background wall using HSV thresholding (plain off-white wall -> 0 dots).
  3. Extract facial edge contours:
     - Glasses wireframe: smooth rounded-rectangular frames, nose bridge, and temples.
     - Eyes: natural eyelid curves and stippled irises with white catchlight reflections.
     - Nose: nostril wings and columella (zero bridge lines for clean negative space).
     - Mouth & lips: Cupid's bow, lip parting line, and lower lip contour.
     - Jawline & ears: natural boundary from photo edges.
     - Collar & placket: authentic folds of the polo shirt.
  4. Organic stippling:
     - Hair: density-weighted organic stippling capturing authentic volume and texture.
     - Eyebrows: dense stippling following dark eyebrow hairs.
     - Beard & mustache: organic stipple distribution matching the trimmed facial hair.
  5. Pure stipple output:
     - Dual-theme CSS: #24292f in light mode / #c9d1d9 in dark mode.
     - Preserves clean negative space on cheeks and forehead.
     - Avoids large dark mass on the polo shirt.
"""

import argparse
import math
import os
import sys

import cv2
import numpy as np

SVG_WIDTH = 460
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def rounded_rect_pts(x_l, y_t, x_r, y_b, cr=5.0, n_side=16, n_corner=6):
    """Generate sample points along a rounded rectangle with corner radius cr."""
    pts = []
    for t in np.linspace(x_l + cr, x_r - cr, n_side):
        pts.append((t, y_t))
    for a in np.linspace(-math.pi / 2, 0, n_corner):
        pts.append((x_r - cr + cr * math.cos(a), y_t + cr + cr * math.sin(a)))
    for t in np.linspace(y_t + cr, y_b - cr, n_side):
        pts.append((x_r, t))
    for a in np.linspace(0, math.pi / 2, n_corner):
        pts.append((x_r - cr + cr * math.cos(a), y_b - cr + cr * math.sin(a)))
    for t in np.linspace(x_r - cr, x_l + cr, n_side):
        pts.append((t, y_b))
    for a in np.linspace(math.pi / 2, math.pi, n_corner):
        pts.append((x_l + cr + cr * math.cos(a), y_b - cr + cr * math.sin(a)))
    for t in np.linspace(y_b - cr, y_t + cr, n_side):
        pts.append((x_l, t))
    for a in np.linspace(math.pi, 3 * math.pi / 2, n_corner):
        pts.append((x_l + cr + cr * math.cos(a), y_t + cr + cr * math.sin(a)))
    pts.append(pts[0])
    return pts


def generate_portrait(photo_path, out_path=None):
    if not os.path.isfile(photo_path):
        sys.exit(f"Error: photo not found at {photo_path}")

    img = cv2.imread(photo_path)
    if img is None:
        sys.exit(f"Error: could not decode image at {photo_path}")

    # Crop head and shoulders: x in [65, 355] (w=290), y in [20, 385] (h=365)
    crop = img[20:385, 65:355]
    h, w = crop.shape[:2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    smooth = cv2.bilateralFilter(gray, 7, 40, 40)

    scale = SVG_WIDTH / float(w)
    svg_h = int(h * scale)

    stipples = []

    def add_dot(x, y, r=1.0):
        stipples.append((x * scale, y * scale, r * scale * 0.70))

    def add_path_dots(points, spacing=1.8, r=1.10):
        for i in range(len(points) - 1):
            x_a, y_a = points[i]
            x_b, y_b = points[i + 1]
            seg_len = math.hypot(x_b - x_a, y_b - y_a)
            if seg_len < 1e-4:
                continue
            n_steps = max(1, int(round(seg_len / spacing)))
            for s in range(n_steps):
                t = s / float(n_steps)
                px = x_a + t * (x_b - x_a)
                py = y_a + t * (y_b - y_a)
                add_dot(px, py, r)

    # 1. HAIR & TOP SILHOUETTE
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    is_wall = (hsv[:, :, 1] < 35) & (hsv[:, :, 2] > 180)

    np.random.seed(42)

    for cy in range(12, 128):
        for cx in range(35, 245):
            if is_wall[cy, cx]:
                continue
            val = smooth[cy, cx]
            if val < 90:
                prob = ((90.0 - val) / 90.0) ** 1.3
                if np.random.random() < prob * 0.40:
                    jx = cx + np.random.uniform(-0.4, 0.4)
                    jy = cy + np.random.uniform(-0.4, 0.4)
                    r = 0.70 + (1.0 - val / 90.0) * 0.65
                    add_dot(jx, jy, r)

    # Outer hair silhouette
    is_subject = (1 - is_wall).astype(np.uint8)
    is_subject = cv2.morphologyEx(is_subject, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    subj_edges = cv2.Canny(is_subject * 255, 100, 200)
    hy, hx = np.where((subj_edges > 0) & (np.arange(h)[:, None] < 185))
    h_grid = {}
    for idx in np.random.permutation(len(hx)):
        gx = int(hx[idx] / 2.2)
        gy = int(hy[idx] / 2.2)
        if (gx, gy) not in h_grid:
            h_grid[(gx, gy)] = True
            add_dot(hx[idx], hy[idx], r=1.0)

    # 2. EYEBROWS
    for cy in range(118, 138):
        for cx in range(68, 215):
            val = smooth[cy, cx]
            if 136 <= cx <= 152:
                continue
            if val < 95:
                prob = ((95.0 - val) / 95.0) ** 1.25
                if np.random.random() < prob * 0.48:
                    jx = cx + np.random.uniform(-0.4, 0.4)
                    jy = cy + np.random.uniform(-0.4, 0.4)
                    r = 0.70 + (1.0 - val / 95.0) * 0.60
                    add_dot(jx, jy, r)

    # 3. GLASSES WIREFRAME (Rounded rectangular frames, bridge, temples, pads)
    left_frame = rounded_rect_pts(74.5, 128.5, 136.0, 172.5, cr=5.0)
    add_path_dots(left_frame, spacing=1.7, r=1.15)

    right_frame = rounded_rect_pts(153.0, 131.5, 210.5, 175.5, cr=5.0)
    add_path_dots(right_frame, spacing=1.7, r=1.15)

    bridge_pts = []
    for t in np.linspace(0, 1, 12):
        bx = 136.0 + t * (153.0 - 136.0)
        by = 143.0 + t * (144.0 - 143.0) - 1.6 * 4 * t * (1 - t)
        bridge_pts.append((bx, by))
    add_path_dots(bridge_pts, spacing=1.6, r=1.15)

    temple_l = [(74.5 - t * 22.5, 143.0 + t * 23.0) for t in np.linspace(0, 1, 14)]
    temple_r = [(210.5 + t * 9.0, 150.0 + t * 3.0) for t in np.linspace(0, 1, 6)]
    add_path_dots(temple_l, spacing=1.8, r=1.10)
    add_path_dots(temple_r, spacing=1.8, r=1.10)

    pad_l = [(136.0 - 1.8 * math.sin(t), 152.0 + t * 9.0) for t in np.linspace(0, 1, 6)]
    pad_r = [(153.0 + 1.8 * math.sin(t), 154.0 + t * 9.0) for t in np.linspace(0, 1, 6)]
    add_path_dots(pad_l, spacing=1.7, r=0.95)
    add_path_dots(pad_r, spacing=1.7, r=0.95)

    # 4. EYES & IRISES
    lid_l = []
    for t in np.linspace(0, 1, 22):
        lx = 84.0 + t * 40.0
        ly = (1 - t) ** 2 * 153.0 + 2 * (1 - t) * t * 143.5 + t ** 2 * 151.0
        lid_l.append((lx, ly))
    add_path_dots(lid_l, spacing=1.5, r=1.15)

    lid_l_low = []
    for t in np.linspace(0, 1, 15):
        lx = 88.0 + t * 32.0
        ly = (1 - t) ** 2 * 154.0 + 2 * (1 - t) * t * 157.0 + t ** 2 * 152.0
        lid_l_low.append((lx, ly))
    add_path_dots(lid_l_low, spacing=2.2, r=0.85)

    for iy in np.linspace(144.5, 155.5, 12):
        for ix in np.linspace(100.5, 111.5, 12):
            dist = math.hypot(ix - 106.0, iy - 150.0)
            dist_cl = math.hypot(ix - 103.8, iy - 148.0)
            if dist <= 5.6 and dist_cl > 1.8:
                prob = 0.85 if dist <= 3.0 else 0.55
                if np.random.random() < prob:
                    add_dot(
                        ix + np.random.uniform(-0.25, 0.25),
                        iy + np.random.uniform(-0.25, 0.25),
                        0.95,
                    )

    lid_r = []
    for t in np.linspace(0, 1, 22):
        rx = 163.0 + t * 39.0
        ry = (1 - t) ** 2 * 153.0 + 2 * (1 - t) * t * 145.5 + t ** 2 * 153.0
        lid_r.append((rx, ry))
    add_path_dots(lid_r, spacing=1.5, r=1.15)

    lid_r_low = []
    for t in np.linspace(0, 1, 15):
        rx = 166.0 + t * 32.0
        ry = (1 - t) ** 2 * 154.0 + 2 * (1 - t) * t * 158.0 + t ** 2 * 153.5
        lid_r_low.append((rx, ry))
    add_path_dots(lid_r_low, spacing=2.2, r=0.85)

    for iy in np.linspace(145.5, 156.5, 12):
        for ix in np.linspace(176.5, 187.5, 12):
            dist = math.hypot(ix - 182.0, iy - 151.0)
            dist_cl = math.hypot(ix - 179.8, iy - 149.0)
            if dist <= 5.6 and dist_cl > 1.8:
                prob = 0.85 if dist <= 3.0 else 0.55
                if np.random.random() < prob:
                    add_dot(
                        ix + np.random.uniform(-0.25, 0.25),
                        iy + np.random.uniform(-0.25, 0.25),
                        0.95,
                    )

    # 5. NOSE BASE
    n_l = []
    for t in np.linspace(0, 1, 10):
        nx = 129.0 + t * 9.0
        ny = (1 - t) ** 2 * 195.0 + 2 * (1 - t) * t * 201.0 + t ** 2 * 200.0
        n_l.append((nx, ny))
    add_path_dots(n_l, spacing=1.6, r=1.05)

    columella = []
    for t in np.linspace(0, 1, 12):
        cx = 141.0 + t * 13.0
        cy = (1 - t) ** 2 * 201.0 + 2 * (1 - t) * t * 204.0 + t ** 2 * 201.0
        columella.append((cx, cy))
    add_path_dots(columella, spacing=1.6, r=1.05)

    n_r = []
    for t in np.linspace(0, 1, 10):
        nx = 157.0 + t * 9.0
        ny = (1 - t) ** 2 * 200.0 + 2 * (1 - t) * t * 201.0 + t ** 2 * 195.0
        n_r.append((nx, ny))
    add_path_dots(n_r, spacing=1.6, r=1.05)

    add_dot(134.0, 199.0, r=1.0)
    add_dot(136.0, 199.5, r=1.0)
    add_dot(159.0, 199.5, r=1.0)
    add_dot(161.0, 199.0, r=1.0)

    for cy in range(198, 204):
        for cx in range(141, 154):
            val = smooth[cy, cx]
            if val < 125 and np.random.random() < 0.40:
                add_dot(cx + np.random.uniform(-0.3, 0.3), cy + np.random.uniform(-0.3, 0.3), 0.85)

    # 6. MOUTH & LIPS
    mouth_roi = gray[220:242, 110:185]
    mouth_edges = cv2.Canny(cv2.GaussianBlur(mouth_roi, (3, 3), 0), 28, 80)
    my, mx = np.where(mouth_edges > 0)
    m_grid = {}
    for idx in np.random.permutation(len(mx)):
        rx = mx[idx] + 110
        ry = my[idx] + 220
        gx = int(rx / 1.9)
        gy = int(ry / 1.9)
        if (gx, gy) not in m_grid:
            m_grid[(gx, gy)] = True
            add_dot(rx, ry, r=1.10)

    chin_shadow = []
    for t in np.linspace(0, 1, 14):
        sx = 135.0 + t * 25.0
        sy = 244.0 + 2.0 * math.sin(t * math.pi)
        chin_shadow.append((sx, sy))
    add_path_dots(chin_shadow, spacing=2.0, r=0.85)

    # 7. BEARD & MUSTACHE
    for cy in range(204, 292):
        for cx in range(55, 225):
            if cy < 224 and cx < 112:
                continue
            if cy < 224 and cx > 172:
                continue
            if 226 <= cy <= 242 and 124 <= cx <= 168:
                continue

            val = smooth[cy, cx]
            if val < 135:
                prob = ((135.0 - val) / 135.0) ** 1.35
                boost = 1.4 if (206 <= cy <= 222 and 122 <= cx <= 172) else 1.0
                if np.random.random() < prob * 0.40 * boost:
                    jx = cx + np.random.uniform(-0.4, 0.4)
                    jy = cy + np.random.uniform(-0.4, 0.4)
                    r = 0.65 + (1.0 - val / 135.0) * 0.55
                    add_dot(jx, jy, r)

    # 8. JAWLINE & EARS
    jaw_roi = cv2.GaussianBlur(gray[180:295, 45:240], (5, 5), 0)
    jaw_edges = cv2.Canny(jaw_roi, 28, 70)
    jy, jx = np.where(jaw_edges > 0)
    j_grid = {}
    for idx in np.random.permutation(len(jx)):
        rx = jx[idx] + 45
        ry = jy[idx] + 180
        if ry > 260 or (ry > 215 and (rx < 74 or rx > 205)):
            gx = int(rx / 2.2)
            gy = int(ry / 2.2)
            if (gx, gy) not in j_grid:
                j_grid[(gx, gy)] = True
                add_dot(rx, ry, r=1.0)

    r_jaw_pts = [(210.0 - t * 3.0, 175.0 + t * 45.0) for t in np.linspace(0, 1, 14)]
    add_path_dots(r_jaw_pts, spacing=2.5, r=0.85)

    ear_pts = []
    for t in np.linspace(0, 1, 16):
        ex = (1 - t) ** 2 * 55.0 + 2 * (1 - t) * t * 41.0 + t ** 2 * 56.0
        ey = 160.0 + t * 55.0
        ear_pts.append((ex, ey))
    add_path_dots(ear_pts, spacing=2.0, r=0.95)

    # 9. COLLAR & POLO SHIRT
    collar_roi = cv2.GaussianBlur(gray[290:365, 30:260], (3, 3), 0)
    collar_edges = cv2.Canny(collar_roi, 32, 80)
    cy_pts, cx_pts = np.where(collar_edges > 0)
    c_grid = {}
    for idx in np.random.permutation(len(cx_pts)):
        rx = cx_pts[idx] + 30
        ry = cy_pts[idx] + 290
        if ry > 355 or rx < 55 or rx > 215:
            continue
        gx = int(rx / 2.2)
        gy = int(ry / 2.2)
        if (gx, gy) not in c_grid:
            c_grid[(gx, gy)] = True
            add_dot(rx, ry, r=1.05)

    c_left = [
        (95.0, 315.0),
        (75.0, 340.0),
        (60.0, 375.0),
        (75.0, 385.0),
        (95.0, 360.0),
    ]
    add_path_dots(c_left, spacing=2.0, r=1.05)

    c_right = [
        (175.0, 315.0),
        (195.0, 340.0),
        (210.0, 370.0),
        (195.0, 380.0),
        (175.0, 360.0),
    ]
    add_path_dots(c_right, spacing=2.0, r=1.05)

    placket = [(147.0, 325.0 + t * 35.0) for t in np.linspace(0, 1, 15)]
    add_path_dots(placket, spacing=2.2, r=1.00)

    # 10. GENERATE SVG
    dots_svg = []
    for x, y, r in stipples:
        dots_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}"/>')

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{svg_h}" viewBox="0 0 {SVG_WIDTH} {svg_h}" role="img" aria-label="Portrait of Utkarsh Sonawane">
<title>Utkarsh Sonawane</title>
<style>
.stipple {{ fill: #24292f; }}
@media (prefers-color-scheme: dark) {{
  .stipple {{ fill: #c9d1d9; }}
}}
</style>
<g class="stipple">
{''.join(dots_svg)}
</g>
</svg>'''

    if not out_path:
        out_path = os.path.join(ROOT, "assets", "generated", "portrait.svg")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    print(
        f"Generated {out_path}: {len(stipples)} stipple dots, {len(svg_content):,} bytes, viewBox 0 0 {SVG_WIDTH} {svg_h}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate monochrome stipple / contour portrait SVG."
    )
    parser.add_argument("photo", nargs="?", default="face.png")
    parser.add_argument("--out", "-o", default=None)
    args = parser.parse_args()

    photo = args.photo
    if not os.path.isfile(photo):
        for candidate in ["face.png", "face.jpg", "assets/face.png", "avatar.png"]:
            cand_path = os.path.join(ROOT, candidate)
            if os.path.isfile(cand_path):
                photo = cand_path
                break

    generate_portrait(photo, args.out)


if __name__ == "__main__":
    main()
