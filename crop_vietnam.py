"""
crop_vietnam.py
---------------
Crops all global VIIRS nightlight TIF files in the VIIRS/ folder
to Vietnam's bounding box and saves them to Vietnam_Nightlights_Annual/.

The output files are identical to the input in every way EXCEPT the
spatial extent — no resampling, no compression changes, nothing altered.

Vietnam bounding box (WGS84) — tight:
  Longitude: 102.14 E  to  109.47 E
  Latitude :   8.18 N  to   23.39 N

A PADDING margin (in degrees) is added on every side so Vietnam
sits centred with breathing room in the final raster.
"""

import os
import sys
import rasterio
from rasterio.windows import from_bounds

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new"
INPUT_DIR  = os.path.join(BASE_DIR, "VIIRS")
OUTPUT_DIR = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Vietnam bounding box (WGS84) — tight extents ─────────────────────────────
VN_LEFT   = 102.14
VN_RIGHT  = 109.47
VN_BOTTOM =   8.18
VN_TOP    =  23.39

# Padding (degrees) added to each side so Vietnam sits centred with margins
PADDING = 1.5

CROP_LEFT   = VN_LEFT   - PADDING
CROP_RIGHT  = VN_RIGHT  + PADDING
CROP_BOTTOM = VN_BOTTOM - PADDING
CROP_TOP    = VN_TOP    + PADDING

# ── Collect TIF files ─────────────────────────────────────────────────────────
tif_files = sorted([
    f for f in os.listdir(INPUT_DIR)
    if f.lower().endswith(".tif")
])

if not tif_files:
    print("No TIF files found in", INPUT_DIR)
    sys.exit(1)

print(f"Found {len(tif_files)} file(s) to process.\n")

# ── Process each file ─────────────────────────────────────────────────────────
for fname in tif_files:
    src_path = os.path.join(INPUT_DIR, fname)

    # Build output filename — extract year/period token from original name
    parts = fname.split("_")
    year_token = None
    for p in parts:
        if p[:4].isdigit():
            year_token = p
            break
    year_label = year_token if year_token else fname.split(".")[0]

    out_name = f"VNM_nightlight_{year_label}.tif"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    if os.path.exists(out_path):
        print(f"[SKIP] {out_name} already exists.")
        continue

    print(f"[Processing] {fname}")
    print(f"  → Output : {out_name}")

    try:
        with rasterio.open(src_path) as src:
            print(f"  → CRS     : {src.crs}")
            print(f"  → Bounds  : {src.bounds}")
            print(f"  → Size    : {src.width} x {src.height} px")
            print(f"  → Dtype   : {src.dtypes}")

            # Compute the pixel window for Vietnam bbox (with padding)
            window = from_bounds(
                left      = max(CROP_LEFT,   src.bounds.left),
                bottom    = max(CROP_BOTTOM, src.bounds.bottom),
                right     = min(CROP_RIGHT,  src.bounds.right),
                top       = min(CROP_TOP,    src.bounds.top),
                transform = src.transform
            ).round_lengths().round_offsets()

            # Read only that window — no resampling, original values
            data = src.read(window=window)

            # New geotransform for the cropped area
            new_transform = src.window_transform(window)

            # Copy ALL original metadata exactly; only update spatial fields
            out_meta = src.meta.copy()
            out_meta.update({
                "height"   : data.shape[1],
                "width"    : data.shape[2],
                "transform": new_transform,
            })

            with rasterio.open(out_path, "w", **out_meta) as dst:
                dst.write(data)

        size_mb = os.path.getsize(out_path) / 1024 / 1024
        print(f"  ✓ Saved ({size_mb:.1f} MB)\n")

    except Exception as e:
        print(f"  ✗ ERROR: {e}\n")

print("All done! Files saved to:", OUTPUT_DIR)
