"""
make_gif.py
-----------
Assembles all PNG files in Vietnam_NightLight_VIIRS_provinces/
into an animated GIF, each frame held for 3 seconds.

Output: Vietnam_Nightlight_Animation.gif  (in the project root)
"""

import os
from PIL import Image

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new"
PNG_DIR    = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS_provinces")
OUT_GIF    = os.path.join(BASE_DIR, "Vietnam_Nightlight_Animation.gif")

# ── Settings ───────────────────────────────────────────────────────────────────
DURATION_MS  = 1200      # 1.5 seconds per frame
MAX_WIDTH    = 1200      # resize width (keeps aspect ratio); None = original size

# ── Collect PNGs sorted by name (= sorted by year) ────────────────────────────
png_files = sorted([
    f for f in os.listdir(PNG_DIR)
    if f.lower().endswith(".png")
])

if not png_files:
    print("No PNG files found in", PNG_DIR)
    raise SystemExit(1)

print(f"Found {len(png_files)} PNG(s):\n  " + "\n  ".join(png_files))
print()

# ── Load and optionally resize frames ─────────────────────────────────────────
frames = []
for fname in png_files:
    img = Image.open(os.path.join(PNG_DIR, fname)).convert("RGB")

    if MAX_WIDTH and img.width > MAX_WIDTH:
        ratio  = MAX_WIDTH / img.width
        new_h  = int(img.height * ratio)
        img    = img.resize((MAX_WIDTH, new_h), Image.LANCZOS)

    # Convert to P (palette) mode with best dithering for GIF
    img_p = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=1)
    frames.append(img_p)
    print(f"  Loaded: {fname}  ({img.width}×{img.height} px)")

print()

# ── Save GIF ──────────────────────────────────────────────────────────────────
print(f"Building GIF → {OUT_GIF}")
frames[0].save(
    OUT_GIF,
    format="GIF",
    save_all=True,
    append_images=frames[1:],
    duration=DURATION_MS,
    loop=0,          # 0 = loop forever
    optimize=False,  # keep False for consistent color palette per frame
)

size_mb = os.path.getsize(OUT_GIF) / 1024 / 1024
print(f"✓ Done!  {len(frames)} frames  |  {size_mb:.1f} MB  →  {OUT_GIF}")
