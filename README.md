# 🛰️ LayerAlterator

A Python-based geospatial tool for modifying raster layers using vector-defined zones and attribute-driven rules. Designed for spatial simulations where input maps need to be programmatically altered based on scenario definitions (e.g. urban expansion, vegetation removal, land cover redistribution).

---

## 📌 Overview

This tool processes raster datasets by applying either **proportional variations** (`"pct"`) or **value replacement** (`"replace"`) within vector-defined polygons, using per-layer configuration defined in a JSON file. It supports batch processing of multiple raster files and ensures values stay within a specified numeric range.

---

## 🗂️ Repository Structure

```bash
LayerAlterator/
├── test_data/
│   |
│   ├── lc_fractions/        # Input raster layers (GeoTIFFs)
│   ├── ucps/                # UCP layers (optional extension)
│   ├── sample_mask.geojson  # Vector mask
│   └── operation_rules.json # Configuration rules
├── output/                      # Output folder for modified rasters
├── test_layer_sim.ipynb         # Jupyter Notebook for testing and demonstration
├── requirements.txt
├── README.md
└── .gitignore
```

---

## ⚙️ Functionality

- ✅ Applies spatial edits using geometry masks from a GeoJSON or GPKG file
- ✅ Automatically matches each raster to an attribute in the vector file
- ✅ Reads simulation rules (`"pct"` or `"replace"`) from a JSON file
- ✅ Clips output pixel values to a safe user-defined range (default: 0–1)
- ✅ Skips rasters with no rule or missing attribute column

---

## 📥 Input Files

### 🗺️ Raster Layers

- Format: `.tif` or `.tiff`
- One file per covariate layer (e.g., `F_AC.tif`, `IMD.tif`, etc.)

### 🗂️ Vector Mask

- Format: `.geojson` or `.gpkg`
- Must contain columns named after the raster filenames (uppercased, without extension)

### 🧾 Operation Rules (JSON)

```json
{
  "F_AC.tif": "replace",
  "IMD.tif": "pct",
  "F_G.tif": null
}
```

- Keys: Raster filenames
- Values:
  - `"pct"` – Apply a percentage-based reduction
  - `"replace"` – Apply a fixed value replacement
  - `null` – Skip this layer

---

## 🚀 Usage

### 📦 Installation

```bash
pip install -r requirements.txt
```

### ▶️ Running the Script

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

### 📓 Alternatively, Use the Jupyter Notebook

Open `test_layer_sim.ipynb` to run the full workflow interactively and inspect outputs.

---

## 🧪 Example Output

```text
[SKIP] No operation rule for 'F_W.tif'
[DONE] Modified F_S.tif with 'replace' → ./output/modified_raster/new_data/F_S.tif
[DONE] Modified F_AC.tif with 'replace' → ./output/modified_raster/new_data/F_AC.tif
```

---

## 🔧 Future Improvements

- Add CLI interface for command-line usage
- Support for `.shp` vector files and `.vrt` raster stacks
- Post-processing validation controller (e.g., sum of land cover fractions = 1)
- Optional correction for small inconsistencies

---

## 🧑‍💻 Author

**Amirhossein Donyadidegan**  
MSc Geoinformatics Engineering  
Politecnico di Milano    
[GitHub Profile →](https://github.com/AmirDonyadide)

---

## 🧑‍💻 Supervisor

**Dr. Daniele Oxoli**  
Politecnico di Milano
[GitHub Profile →](https://github.com/danioxoli)

---

## 📄 License

This project is released under the MIT License.
