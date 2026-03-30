"""
mask_vietnam.py
---------------
For each TIF in Vietnam_NightLight_VIIRS/:
  - Pixels INSIDE  Vietnam boundary → keep original value (unchanged)
  - Pixels OUTSIDE Vietnam boundary → set to 0
  - Save to Vietnam_NightLight_VIIRS_clean/

ALL metadata (dtype, CRS, driver, nodata, compression, blocksize, etc.)
is copied exactly from the source — only pixel values outside Vietnam change.
"""

import os
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
import geopandas as gpd
from shapely.ops import unary_union

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new"
INPUT_DIR  = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS")
OUTPUT_DIR = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS_clean")
GEOJSON    = os.path.join(BASE_DIR, "Vietnam_Provinces.geojson")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Build Vietnam boundary (union of all provinces) ───────────────────────────
print("Loading province boundaries...")
gdf = gpd.read_file(GEOJSON)
vietnam_geom = unary_union(gdf.geometry)
print(f"  {len(gdf)} provinces merged into one boundary.\n")

# ── Process each TIF ─────────────────────────────────────────────────────────
tif_files = sorted([f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".tif")])
print(f"Found {len(tif_files)} TIF file(s) to process.\n")

for fname in tif_files:
    src_path = os.path.join(INPUT_DIR, fname)
    out_path = os.path.join(OUTPUT_DIR, fname)   # keep exact same filename

    if os.path.exists(out_path):
        print(f"[SKIP] {fname} already exists.")
        continue

    print(f"[Processing] {fname}")

    with rasterio.open(src_path) as src:

        # Reproject boundary to match raster CRS (if needed)
        if gdf.crs != src.crs:
            geom_proj = gpd.GeoSeries([vietnam_geom], crs=gdf.crs).to_crs(src.crs).iloc[0]
        else:
            geom_proj = vietnam_geom

        # ── Copy ALL original metadata exactly ────────────────────────────────
        out_meta = src.meta.copy()
        # (dtype, crs, transform, nodata, driver, count, width, height
        #  compression, tiling, blocksize — all preserved as-is)

        # ── Apply mask: outside Vietnam → 0, inside → unchanged ──────────────
        masked_data, _ = rio_mask(
            src,
            [geom_proj.__geo_interface__],
            crop=False,     # keep same spatial extent and pixel grid
            invert=False,   # mask outside the boundary
            nodata=0,       # fill value for outside pixels = 0
            filled=True,    # replace masked pixels with fill value
            all_touched=False,
        )

    # ── Write output with identical metadata ──────────────────────────────────
    with rasterio.open(out_path, "w", **out_meta) as dst:
        dst.write(masked_data)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"  ✓ Saved ({size_mb:.1f} MB)\n")

print("All done! Clean files saved to:", OUTPUT_DIR)
