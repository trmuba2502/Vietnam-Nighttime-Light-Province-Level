"""
extract_province_nightlight.py
-------------------------------
Calculates mean VIIRS nightlight radiance per Vietnam province
for each year using rasterio + geopandas + rasterstats (zonal_stats).

Inputs:
  - Vietnam_NightLight_VIIRS/*.tif   (Vietnam-cropped VIIRS rasters)
  - Vietnam_Provinces.geojson        (province boundaries, NAME_1 column)

Output:
  - Vietnam_Province_Nightlight.csv  (long format: Province | Year | Mean_Nightlight)
  - Vietnam_Province_Nightlight_Wide.csv (wide format: Province | 2012 | 2013 | ...)
"""

import os
import re
import sys
import warnings
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR        = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new"
TIF_DIR         = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS")
GEOJSON_PATH    = os.path.join(BASE_DIR, "Vietnam_Provinces.geojson")
OUT_LONG        = os.path.join(BASE_DIR, "Vietnam_Province_Nightlight.csv")
OUT_WIDE        = os.path.join(BASE_DIR, "Vietnam_Province_Nightlight_Wide.csv")

# ── Load province boundaries ───────────────────────────────────────────────────
print("Loading province boundaries...")
gdf = gpd.read_file(GEOJSON_PATH)
print(f"  {len(gdf)} provinces loaded.")
print(f"  CRS: {gdf.crs}")
print(f"  Columns: {list(gdf.columns)}")
print()

# Use NAME_1 as the province identifier
PROVINCE_COL = "NAME_1"

# ── Collect TIF files ─────────────────────────────────────────────────────────
tif_files = sorted([
    f for f in os.listdir(TIF_DIR)
    if f.lower().endswith(".tif")
])
print(f"Found {len(tif_files)} TIF file(s):\n  " + "\n  ".join(tif_files))
print()

# ── Try to import rasterstats, fall back to manual masking ────────────────────
try:
    from rasterstats import zonal_stats
    USE_RASTERSTATS = True
    print("Using rasterstats for zonal statistics.\n")
except ImportError:
    USE_RASTERSTATS = False
    print("rasterstats not found — using manual rasterio masking.\n")

# ── Process each TIF ──────────────────────────────────────────────────────────
records = []

for fname in tif_files:
    fpath = os.path.join(TIF_DIR, fname)

    # Extract year label from filename (e.g. 2013, or 201204-201212)
    match = re.search(r'(\d{4}(?:\d{2}-\d{6})?)', fname)
    year_label = match.group(1) if match else fname.split(".")[0]
    # Simplify: if it contains a hyphen treat it as 2012 (partial year)
    if "-" in year_label:
        year_label = year_label[:4]   # "2012"

    print(f"Processing {fname}  →  year={year_label}")

    with rasterio.open(fpath) as src:
        raster_crs = src.crs
        nodata     = src.nodata

    # Reproject GeoJSON to match raster CRS if needed
    if gdf.crs != raster_crs:
        gdf_proj = gdf.to_crs(raster_crs)
    else:
        gdf_proj = gdf.copy()

    if USE_RASTERSTATS:
        # ── rasterstats path ──────────────────────────────────────────────────
        stats = zonal_stats(
            gdf_proj,
            fpath,
            stats=["mean", "count", "nodata"],
            nodata=nodata,
            all_touched=False,
        )
        for i, row in gdf_proj.iterrows():
            prov = row[PROVINCE_COL]
            mean_val = stats[i]["mean"]
            count    = stats[i]["count"]
            records.append({
                "Province"       : prov,
                "Year"           : year_label,
                "Mean_Nightlight": round(mean_val, 6) if mean_val is not None else np.nan,
                "Valid_Pixels"   : count,
            })

    else:
        # ── Manual rasterio masking path ──────────────────────────────────────
        from rasterio.mask import mask as rio_mask
        from shapely.geometry import mapping

        with rasterio.open(fpath) as src:
            for i, row in gdf_proj.iterrows():
                prov = row[PROVINCE_COL]
                geom = [mapping(row.geometry)]
                try:
                    out_image, _ = rio_mask(src, geom, crop=True, nodata=np.nan)
                    data = out_image[0].astype("float64")
                    # Also mask original nodata
                    if nodata is not None:
                        data[data == nodata] = np.nan
                    valid = data[~np.isnan(data)]
                    mean_val = float(np.nanmean(valid)) if len(valid) > 0 else np.nan
                    count    = int(len(valid))
                except Exception:
                    mean_val = np.nan
                    count    = 0

                records.append({
                    "Province"       : prov,
                    "Year"           : year_label,
                    "Mean_Nightlight": round(mean_val, 6) if not np.isnan(mean_val) else np.nan,
                    "Valid_Pixels"   : count,
                })

    print(f"  ✓  Done")

print()

# ── Build DataFrames ──────────────────────────────────────────────────────────
df_long = pd.DataFrame(records)
df_long = df_long.sort_values(["Province", "Year"]).reset_index(drop=True)

# Wide format
df_wide = df_long.pivot_table(
    index="Province",
    columns="Year",
    values="Mean_Nightlight"
).reset_index()
df_wide.columns.name = None

# ── Save ──────────────────────────────────────────────────────────────────────
df_long.to_csv(OUT_LONG, index=False)
df_wide.to_csv(OUT_WIDE, index=False)

print(f"Saved long format  → {OUT_LONG}")
print(f"Saved wide format  → {OUT_WIDE}")
print()
print("Preview (long format, first 20 rows):")
print(df_long.head(20).to_string(index=False))
print()
print("Preview (wide format):")
print(df_wide.to_string(index=False))
