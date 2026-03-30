"""
visualize_provinces.py
-----------------------
Renders each Vietnam nightlight TIF in Vietnam_NightLight_VIIRS/
as a PNG image with:
  - White → Yellow → Yellow-Orange gradient for nightlight intensity
  - Province boundaries drawn in white (0.5 px linewidth)
  - Dark background outside Vietnam
  - Year label overlay
  - Saved to Vietnam_NightLight_VIIRS_provinces/

Inputs:
  - Vietnam_NightLight_VIIRS/*.tif       (cropped VIIRS rasters)
  - Vietnam_Provinces.geojson            (province boundaries)

Output:
  - Vietnam_NightLight_VIIRS_provinces/VNM_nightlight_<year>.png
"""

import os
import sys
import warnings
import numpy as np
import rasterio
from rasterio.plot import reshape_as_image
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")   # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new"
INPUT_DIR  = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS_clean")
OUTPUT_DIR = os.path.join(BASE_DIR, "Vietnam_NightLight_VIIRS_provinces")
GEOJSON    = os.path.join(BASE_DIR, "Vietnam_Provinces.geojson")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Custom colormap: dark bg, then white → yellow → yellow-orange ──────────────
# The raster values 0 (dark / outside VN) → deep navy, then
# low positive → white, mid → yellow, high → orange-yellow
NL_CMAP = LinearSegmentedColormap.from_list(
    "nightlight",
    [
        # (0.000, "#000000"),   # pitch black       — no light / ocean / background
        # (0.005, "#1a0800"),   # near-black brown  — noise floor
        # (0.05,  "#3d1500"),   # very dark amber
        # (0.15,  "#7a3000"),   # dark burnt orange
        # (0.35,  "#c86000"),   # amber / sodium lamp orange
        # (0.60,  "#e8920a"),   # warm orange-amber (main city glow)
        # (0.80,  "#f5c842"),   # golden yellow     — dense urban core
        # (0.93,  "#ffe680"),   # pale yellow       — very bright areas
        # (1.00,  "#fffff0"),   # near-white        — hotspot peak

        (0.000, "#121212"),   # Dark Charcoal     
        (0.005, "#1c140d"),   # Soft Shadow       
        (0.05,  "#2e1e12"),   # Muted Coffee      
        (0.15,  "#5c3d1f"),   # Antique Bronze    
        (0.35,  "#8e632d"),   # Ochre Gold        
        (0.60,  "#bfa05a"),   # Muted Brass       
        (0.80,  "#d9c585"),   # Soft Sand         
        (0.93,  "#ede3b4"),   # Champagne         
        (1.00,  "#fdfbf0"),   # Warm Ivory        

    ],
    N=512,
)

# ── Load province boundaries ───────────────────────────────────────────────────
print("Loading province boundaries …")
gdf = gpd.read_file(GEOJSON)
print(f"  {len(gdf)} provinces loaded  |  CRS: {gdf.crs}\n")

# ── Collect TIF files ──────────────────────────────────────────────────────────
import re
tif_files = sorted([f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".tif")])
if not tif_files:
    print("No TIF files found in", INPUT_DIR)
    sys.exit(1)
print(f"Found {len(tif_files)} TIF file(s).\n")

# ── Global colour scale: single pass over ALL files ───────────────────────────
# Collect the 99.5th-percentile value from each year, then take the overall max.
# This way every frame shares the same vmin/vmax so brightness is comparable.
print("Computing global colour scale …")
all_p995 = []
for _f in tif_files:
    with rasterio.open(os.path.join(INPUT_DIR, _f)) as _src:
        _nd  = _src.nodata
        _arr = _src.read(1).astype("float64")
    if _nd is not None:
        _arr[_arr == _nd] = np.nan
    _arr[_arr < 0] = np.nan
    _valid = _arr[~np.isnan(_arr)]
    if len(_valid) > 0:
        all_p995.append(float(np.nanpercentile(_valid, 99.5)))

GLOBAL_VMIN = 0.0
GLOBAL_VMAX = max(all_p995) if all_p995 else 1.0
GLOBAL_VMAX = max(GLOBAL_VMAX, 0.01)   # guard against all-zero
print(f"  Global vmin = {GLOBAL_VMIN}")
print(f"  Global vmax = {GLOBAL_VMAX:.4f}  (max 99.5th-pct across all years)\n")

# ── Process each file ──────────────────────────────────────────────────────────
for fname in tif_files:
    src_path = os.path.join(INPUT_DIR, fname)

    # Extract year label
    match = re.search(r"(\d{4})", fname)
    year_label = match.group(1) if match else fname.split(".")[0]

    out_name = f"VNM_nightlight_{year_label}.png"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    if os.path.exists(out_path):
        print(f"[SKIP] {out_name} already exists.")
        continue

    print(f"[Rendering] {fname}  →  {out_name}")

    with rasterio.open(src_path) as src:
        raster_crs = src.crs
        bounds     = src.bounds          # left, bottom, right, top
        nodata     = src.nodata
        data       = src.read(1).astype("float64")   # band 1

    # ── Mask nodata / negative values ─────────────────────────────────────────
    if nodata is not None:
        data[data == nodata] = np.nan
    data[data < 0] = np.nan

    # ── Use the shared global colour scale (consistent across all years) ────────
    vmin = GLOBAL_VMIN
    vmax = GLOBAL_VMAX

    # Replace NaN with 0 for display (they get the dark navy color)
    display = np.where(np.isnan(data), 0.0, data)

    # ── Reproject boundaries to raster CRS ────────────────────────────────────
    if gdf.crs != raster_crs:
        gdf_plot = gdf.to_crs(raster_crs)
    else:
        gdf_plot = gdf.copy()

    # ── Figure setup ──────────────────────────────────────────────────────────
    dpi    = 400
    aspect = (bounds.right - bounds.left) / (bounds.top - bounds.bottom)
    height = 16          # inches  → ~6400 px tall at 400 dpi
    width  = height * aspect

    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")

    # ── Raster layer ──────────────────────────────────────────────────────────
    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]
    im = ax.imshow(
        display,
        cmap=NL_CMAP,
        vmin=vmin,
        vmax=vmax,
        extent=extent,
        origin="upper",
        interpolation="lanczos",
        aspect="equal",
    )

    # ── Province boundaries — white, 0.5 px ───────────────────────────────────
    gdf_plot.boundary.plot(
        ax=ax,
        color="white",
        linewidth=0.1,
        alpha=0.85,
    )

    # ── Colorbar ──────────────────────────────────────────────────────────────
    cbar = fig.colorbar(
        im, ax=ax,
        fraction=0.025, pad=0.015,
        label="Radiance (nW/cm²/sr)",
    )
    cbar.ax.yaxis.label.set_color("white")
    cbar.ax.tick_params(colors="white", labelsize=10)
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")

    # ── Year label ────────────────────────────────────────────────────────────
    ax.text(
        0.015, 0.97, year_label,
        transform=ax.transAxes,
        fontsize=32, fontweight="bold",
        color="white", alpha=0.9,
        va="top", ha="left",
        fontfamily="monospace",
    )

    # ── Title ─────────────────────────────────────────────────────────────────
    ax.set_title(
        f"Vietnam Nighttime Light  –  {year_label}",
        color="white", fontsize=16, pad=10,
    )

    # ── Clean up axes ─────────────────────────────────────────────────────────
    ax.set_xlabel("Longitude", color="#aaaaaa", fontsize=11)
    ax.set_ylabel("Latitude",  color="#aaaaaa", fontsize=11)
    ax.tick_params(colors="#aaaaaa", labelsize=10)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333333")

    plt.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)

    size_kb = os.path.getsize(out_path) / 1024
    print(f"  ✓ Saved  {out_name}  ({size_kb:.0f} KB)\n")

print("All done! PNGs saved to:", OUTPUT_DIR)
