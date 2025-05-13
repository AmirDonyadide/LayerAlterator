# 🛰️ LayerAlterator

**LayerAlterator** is a Python-based geospatial simulation tool for programmatically modifying raster datasets within vector-defined zones, based on attribute-driven rules. It’s tailored for use in urban planning, climate adaptation modeling, and land cover change simulation.

---

## 📌 Overview

This tool processes raster datasets using spatial rules defined in a vector mask (GeoJSON/GPKG). Each raster is altered according to per-layer configurations provided in a JSON file, enabling two main types of operations:

- **`"pct"`**: Applies proportional (percentage-based) changes with automatic balancing.
- **`"replace"`**: Replaces values directly as defined by attributes in the mask.

Special features include validation and balancing logic for land cover (LC) fractions and optional support for modifying Urban Climate Parameters (UCPs). Output rasters are clipped to remain within a specified numeric range (default: 0–1).

---

## 🔍 Key Features

✅ Raster modification driven by vector attribute rules  
✅ Batch processing of multiple layers  
✅ Intelligent handling of LC fractions (`F_*.tif`) with sum constraints  
✅ Skipping of rasters with missing or `null` rules  
✅ JSON-based configuration for flexible simulation scenarios  
✅ Format support: `.tif`, `.tiff` rasters; `.geojson`, `.gpkg` vectors  

---

## 🗂️ Repository Structure

```bash
LayerAlterator/
├── test_data/
│   ├── lc_fractions/        # Input raster layers (GeoTIFFs)
│   ├── ucps/                # UCP layers (optional)
│   ├── sample_mask.geojson  # Vector mask with simulation attributes
│   └── operation_rules.json # Configuration for each raster layer
├── test_layer_sim.ipynb         # Interactive Jupyter Notebook example
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
└── .gitignore                   # Ignored files and folders
```

---

## 📥 Input Data Structure

### 🌍 Raster Layers

- Format: `.tif` or `.tiff`
- Naming: Each filename must match a column name in the vector mask (case-insensitive, without extension)
- Example: `F_AC.tif` → `F_AC` column in vector

### 🗺️ Vector Mask

- Format: `.geojson` or `.gpkg`
- Geometry type: Polygons
- Attributes: One column per raster, named after the raster filename (uppercase, no extension)

### ⚙️ Operation Rules (JSON)

```json
{
  "F_AC.tif": "replace",
  "IMD.tif": "pct",
  "F_G.tif": null
}
```

- `"replace"`: Replace values directly based on polygon attributes  
- `"pct"`: Apply proportional adjustment (automatically balanced)  
- `null`: Skip the raster layer  

---

## ⚙️ Functionality Details

### Land Cover Fractions (`F_*.tif`)

- `"pct"`: Balancing logic ensures per-pixel sum remains 1  
- `"replace"`: Total value across LC fractions must not exceed 1 (validated)

### Urban Climate Parameters (UCPs)

- Rules can be `"replace"`, `"pct"`, or `null`
- No inter-parameter validation (yet)

### Raster Operations

- Reads each raster and overlays it with relevant polygons
- Identifies matching attributes by filename
- Applies rules per-pixel using the polygon’s attribute values
- Clips final raster to specified numeric range

---

## 🚀 Quick Start

### 🧰 Installation

```bash
git clone https://github.com/AmirDonyadide/LayerAlterator.git
cd LayerAlterator
pip install -r requirements.txt
```

### ▶️ Python Script Usage

```python
from layer_alterator import layer_alterator

layer_alterator(
    raster_folder="./test_data/lc_fractions",
    vector_path="./test_data/sample_mask.geojson",
    operation_rule_path="./test_data/operation_rules.json",
    output_folder="./output/modified_raster/new_data",
    value_range=(0, 1)
)
```

### 📓 Notebook Interface

Use the provided `test_layer_sim.ipynb` Jupyter notebook for:

- Loading input layers
- Visualizing changes
- Running simulations interactively

---

## 🧪 Sample Output

```bash
[SKIP] No operation rule for 'F_W.tif'
[DONE] Modified F_S.tif with 'replace' → ./output/modified_raster/new_data/F_S.tif
[DONE] Modified F_AC.tif with 'replace' → ./output/modified_raster/new_data/F_AC.tif
```

---

## 💡 Applications

- Urban growth simulation  
- Vegetation and land cover modeling  
- Environmental impact assessments  
- Climate-sensitive parameter tuning (e.g. albedo, thermal conductivity)

---

## 🧰 Development Roadmap

- [ ] Command-line interface (CLI) support
- [ ] `.shp` vector support
- [ ] `.vrt` stack raster support
- [ ] UCP logical validations (e.g., `BF ≤ IMP`)
- [ ] GUI for visual rule editing (planned)

---

## 🧑‍💼 Author

**Amirhossein Donyadidegan**  
MSc Geoinformatics Engineering  
Politecnico di Milano  
📫 [GitHub](https://github.com/AmirDonyadide) | 📍 Karlsruhe / Milano

---

## 🧑‍🏫 Supervisor

**Dr. Daniele Oxoli**  
Assistant Professor, Politecnico di Milano  
🌐 [GitHub](https://github.com/danioxoli)

---

## 📄 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.
