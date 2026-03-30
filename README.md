# Vietnam Nighttime Light Analysis

> A data pipeline for processing, cleaning, and visualizing VIIRS nighttime light satellite data across Vietnam's provinces — used as a proxy indicator for economic development in a Development Economics group project.

---

## Project Overview

This project analyzes **VIIRS (Visible Infrared Imaging Radiometer Suite)** nighttime light (NTL) radiance data over Vietnam from **2012 to 2020**. Nighttime light intensity is widely used as a proxy for economic activity, electricity access, and urbanization in economics research.

The pipeline covers three stages:
1. **Data Preparation** — Crop global rasters to Vietnam, mask non-Vietnam pixels
2. **Data Extraction** — Compute mean nightlight radiance per province per year
3. **Visualization** — Render high-resolution maps with province boundaries and NASA-style glow colormap

---

## Project Structure

```
Group Project - new/
│
├── Vietnam_NightLight_VIIRS/           # Cropped to Vietnam bounding box
├── Vietnam_NightLight_VIIRS_clean/     # Masked: pixels outside Vietnam = 0
├── Vietnam_NightLight_VIIRS_provinces/ # High-res PNG visualizations per year
├── Vietnam_Nightlights_Annual/         # (Additional processed rasters)
│
├── Vietnam_Provinces.geojson           # Province boundary geometries (WGS84)
│
├── Vietnam_Province_Nightlight.csv          # Long format: Province | Year | Mean_Nightlight
├── Vietnam_Province_Nightlight_Wide.csv     # Wide format: Province | 2012 | 2013 | ...
├── Vietnam_Nightlight_Index_by_Province_2013-2020.csv
├── Vietnam_Nightlight_Index_by_Province_2013-2020.nc
│
├── crop_vietnam.py                     # Step 1: Crop global TIFs to Vietnam
├── mask_vietnam.py                     # Step 2: Mask pixels outside Vietnam border
├── read_vietnam_tif.py                 # Utility: Inspect TIF file statistics
├── extract_province_nightlight.py      # Step 3: Zonal stats → CSV output
├── visualize_provinces.py              # Step 4: Render province maps as PNG
│
├── Nighttime-light-cleaned.ipynb       # Jupyter notebook for analysis
```

---

## ⚙️ Pipeline Steps

### Step 1 — `crop_vietnam.py`
Crops all raw global VIIRS TIF files to Vietnam's bounding box with a padding margin.

| Parameter | Value |
|-----------|-------|
| Tight bounding box | 102.14°E – 109.47°E, 8.18°N – 23.39°N |
| Padding added | **1.5°** on each side |
| Final crop extent | 100.64°E – 110.97°E, 6.68°N – 24.89°N |

- No resampling or compression changes — original pixel values preserved
- Output: `Vietnam_NightLight_VIIRS/VNM_nightlight_<year>.tif`

---

### Step 2 — `mask_vietnam.py`
Masks pixels **outside** Vietnam's national boundary to `0`, keeping all interior pixels at their original radiance values.

- Uses `Vietnam_Provinces.geojson` to build a national boundary (union of all provinces)
- Reprojects boundary CRS to match raster CRS automatically
- Output: `Vietnam_NightLight_VIIRS_clean/` (same filenames)

---

### Step 3 — `extract_province_nightlight.py`
Computes **mean VIIRS radiance per province per year** using zonal statistics.

- Prefers `rasterstats.zonal_stats` if available; falls back to manual `rasterio` masking
- Province identifier: `NAME_1` column in GeoJSON
- Outputs:
  - `Vietnam_Province_Nightlight.csv` — long format
  - `Vietnam_Province_Nightlight_Wide.csv` — wide format (pivot by year)

---

### Step 4 — `visualize_provinces.py`
Renders each TIF year as a **high-resolution PNG map** (400 DPI, ~6400 px tall).

| Feature | Detail |
|---------|--------|
| Colormap | NASA Black Marble style: black → dark amber → orange-gold → warm ivory |
| Province borders | White, 0.1 px linewidth |
| Color scaling | 99.5th-percentile stretch (robust to outliers) |
| Interpolation | Lanczos (sharpest for downscaling) |
| Output size | ~16 × 10 inches @ 400 DPI |

- Output: `Vietnam_NightLight_VIIRS_provinces/VNM_nightlight_<year>.png`

---

### Utility — `read_vietnam_tif.py`
Prints a summary table for each TIF: total pixels, NoData count, zero-value count, and percentages. Useful for data quality checks.

---

## 🗺️ Data Source

- **VIIRS Day/Night Band (DNB)** monthly/annual composites — accessed via [NOAA/NGDC](https://www.ngdc.noaa.gov/) or [NASA Earthdata](https://earthdata.nasa.gov/)
- **Province boundaries** — `Vietnam_Provinces.geojson` (GADM or similar administrative boundary dataset)

---

## Dependencies

```bash
pip install rasterio geopandas numpy matplotlib rasterstats shapely
```

| Package | Purpose |
|---------|---------|
| `rasterio` | Read/write/crop GeoTIFF rasters |
| `geopandas` | Load and reproject province boundaries |
| `rasterstats` | Fast zonal statistics |
| `matplotlib` | Map rendering and colormap |
| `shapely` | Geometry union for masking |
| `numpy` | Array operations |

---

## Running the Pipeline

Run scripts in order:

```bash
# 1. Crop global rasters to Vietnam (with margin)
python crop_vietnam.py

# 2. Mask pixels outside Vietnam border
python mask_vietnam.py

# 3. Extract mean radiance per province per year
python extract_province_nightlight.py

# 4. Render high-res visualizations
python visualize_provinces.py
```

> **Note:** Each script skips files that already exist in the output folder.

---

## Output Files

| File | Description |
|------|-------------|
| `Vietnam_Province_Nightlight.csv` | Long-format panel data: Province × Year → Mean radiance |
| `Vietnam_Province_Nightlight_Wide.csv` | Wide-format: one column per year |
| `Vietnam_Nightlight_Index_by_Province_2013-2020.csv` | Indexed nightlight data (2013–2020) |
| `Vietnam_Nightlight_Index_by_Province_2013-2020.nc` | NetCDF version for GIS/stats software |
| `Vietnam_NightLight_VIIRS_provinces/*.png` | High-res nightlight maps per year |

---