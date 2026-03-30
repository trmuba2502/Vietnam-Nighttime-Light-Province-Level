"""
read_vietnam_tif.py
-------------------
Analyzes percentage of null/nodata values in each TIF file
inside Vietnam_NightLight_VIIRS/.
"""

import os
import numpy as np
import rasterio

FOLDER = r"E:\IU\DEVELOPMENT ECONOMICS\Group Project - new\Vietnam_NightLight_VIIRS"

tif_files = sorted([f for f in os.listdir(FOLDER) if f.lower().endswith(".tif")])
print(f"Found {len(tif_files)} TIF file(s)\n")
print(f"{'File':<45} {'Total Px':>12} {'NoData Px':>12} {'Null %':>10} {'Zero Px':>12} {'Zero %':>10}")
print("-" * 105)

for fname in tif_files:
    fpath = os.path.join(FOLDER, fname)
    with rasterio.open(fpath) as src:
        data   = src.read(1).astype("float64")
        nodata = src.nodata
        total  = data.size

        # Count NoData pixels (flagged by nodata value)
        if nodata is not None:
            nd_mask = (data == nodata)
        else:
            nd_mask = np.zeros(data.shape, dtype=bool)

        # Also count NaN pixels (if float raster)
        nan_mask = np.isnan(data)
        null_mask = nd_mask | nan_mask

        null_count = int(null_mask.sum())
        null_pct   = null_count / total * 100

        # Count zero-value pixels (excluding nodata)
        zero_mask  = (~null_mask) & (data == 0)
        zero_count = int(zero_mask.sum())
        zero_pct   = zero_count / total * 100

    print(f"{fname:<45} {total:>12,} {null_count:>12,} {null_pct:>9.2f}% {zero_count:>12,} {zero_pct:>9.2f}%")

print("-" * 105)
print("\nNote: 'NoData Px' = pixels flagged as NoData or NaN.")
print("      'Zero Px'   = valid pixels with radiance value = 0 (dark areas).")
