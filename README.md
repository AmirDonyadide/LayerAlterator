# 🛰️ LayerAlterator

**LayerAlterator** is a Python-based geospatial simulation tool for programmatically modifying raster datasets within vector-defined zones, based on attribute-driven rules. It’s tailored for use in urban planning, climate adaptation modeling, and land cover change simulation.

---

## 📌 Overview

---

## 🔍 Key Features

---

## 🗂️ Repository Structure

---

## 📥 Input Data Structure

---

## 📥 Documentation

### A) Import Libraries

```python
import os
import json
import geopandas as gpd
import pandas as pd
import rasterio
import numpy as np
from rasterio.mask import mask
from rasterio.features import rasterize
from shapely.geometry import mapping
```

This section imports all the necessary Python libraries required for geospatial raster-vector operations, numerical computations, and file handling.

#### Standard Libraries
- **`os`**: Handles file system paths and directory operations.
- **`json`**: Parses JSON files, particularly the operation rules.

#### Geospatial Libraries
- **`geopandas`** (`gpd`): Used for reading and processing vector data (e.g., GeoJSON, Shapefile, GPKG). It extends `pandas` with spatial capabilities.
- **`rasterio`**: Used for raster data I/O and manipulation.
  - `rasterio.mask.mask`: Masks raster datasets using polygon geometries.
  - `rasterio.features.rasterize`: Converts vector shapes into raster masks.

#### Numerical and Tabular Data Libraries
- **`numpy`** (`np`): Provides fast array manipulation and mathematical operations.
- **`pandas`** (`pd`): Used to handle structured data such as attribute tables from vector data.

#### Geometry Conversion
- **`shapely.geometry.mapping`**: Converts geometries into a format suitable for rasterio operations (GeoJSON-like mapping).

> These libraries form the foundation of the layer simulator and enable seamless integration of vector attributes into raster processing workflows.

### B) Import Input Data

This section prepares all necessary input files for the simulation process, including vector masks, raster layers, operational rules, and the output path.

#### B.1) Load Vector Mask

The vector mask defines spatial units (polygons) that carry the attributes needed to control how raster layers will be processed.

Supported formats include:
- `.gpkg` (GeoPackage)
- `.geojson` / `.json` (GeoJSON)
- `.shp` (Shapefile)

The code automatically detects the format and reads the file using `GeoPandas`:

```python
if vector_mask_path.endswith(".gpkg"):
    vector_mask_layer = "layer_name"
    gdf_mask = gpd.read_file(vector_mask_path, layer=vector_mask_layer)
elif vector_mask_path.endswith(".geojson") or vector_mask_path.endswith(".json"):
    gdf_mask = gpd.read_file(vector_mask_path)
elif vector_mask_path.endswith(".shp"):
    gdf_mask = gpd.read_file(vector_mask_path)
else:
    raise ValueError("Unsupported vector format. Use GPKG, GeoJSON, or Shapefile.")
```

**Output:** A `GeoDataFrame` named `gdf_mask` containing the geometries and attributes used in the simulation.

#### B.2) Define Covariate Layer Folders

The code expects two folders containing raster layers:
- `./ucps/`: Urban Conversion Parameter (UCP) rasters such as `IMD.tif`, `BSF.tif`, etc.
- `./lc_fractions/`: Fractional land cover layers, all prefixed with `F_`, such as `F_AC.tif`, `F_UF.tif`, etc.

These paths are defined as:

```python
ucp_folder = "./ucps"
fractions_folder = "./lc_fractions"
```

#### B.3) Load JSON Rule File

Rules for processing each raster layer are defined in a JSON file. Each entry in the file maps a raster filename to one of the following rule types:
- `"mask"`: apply fixed value from the vector attribute
- `"pct"`: apply percentage-based modification
- `"none"`: skip processing

Example JSON content:

```json
{
  "F_AC.tif": "mask",
  "F_UF.tif": "mask",
  "IMD.tif": "pct",
  "BSF.tif": "pct"
}
```

Loading the file in Python:

```python
rules_path = "./operation_rules_C3.json"
with open(rules_path) as f:
    rules = json.load(f)
```

**Output:** A `dict` named `rules` mapping each raster layer to its processing type.

#### B.4) Set Output Folder

Processed rasters will be saved into the specified output folder. The folder is created later in the workflow if it does not already exist:

```python
output_folder = "./output"
```

**Output:** A path where the final masked or adjusted raster layers will be written.

### C) Parse Vector Mask Attributes and Check Rules

This step validates that all input data aligns spatially and logically before performing raster processing.

---

#### C.1) Check CRS Consistency

Function: `check_crs_match(gdf, rules, ucp_folder, fractions_folder)`

This function verifies that the Coordinate Reference System (CRS) of every raster layer matches the CRS of the input vector file (`gdf`).

- For each layer listed in the rule file:
  - Open the corresponding raster.
  - Compare its CRS with the vector mask.
  - Log any mismatches.

**Why this matters:** Spatial misalignment can lead to incorrect rasterization or masking.

---

#### C.2) Parse and Validate Rules

Function: `parse_rules_from_mask(gdf, rules)`

This function determines the processing category for the simulation based on the content of the rules JSON file and the attributes found in each polygon.

##### Supported Rule Categories:

- **C0**: All layers set to `"none"` → no processing required.
- **C1**: All layers set to `"mask"` → must validate:
  - **C1.1**: All values (UCP + fraction) must be within [0, 1].
  - **C1.2**: `IMD ≥ BSF` per polygon.
  - **C1.3**: Sum of all `F_` fraction values per polygon must equal 1.0.
- **C2**: All layers set to `"pct"` → apply uniform percentage change.
- **C3**: A mix of `"pct"` and `"none"` → treat `"none"` as 0% change.
- **C4**: Invalid combination of `"mask"` and `"none"` → raise error.
- **C5**: Invalid combination of `"mask"` and `"pct"` → raise error.

##### Return:
- `rule_id`: one of `"C0"`, `"C1"`, `"C2"`, `"C3"`.
- `parsed_info`: currently unused; reserved for future use.

**Why this matters:** It ensures that the per-polygon rules are logically and numerically valid before applying them to raster data.

---

#### C.3) Execute Rule Validation

Code block to invoke the above logic:

```python
check_crs_match(gdf_mask, rules, ucp_folder, fractions_folder)

try:
    rule_id, parsed_info = parse_rules_from_mask(gdf_mask, rules)
except ValueError as e:
    print("Rule validation failed:", e)
    raise
```

If the check passes, `rule_id` is used to direct the next phase of processing.


---

## ⚙️ Functionality Details

---

## 🚀 Quick Start

---

## 🧪 Sample Output


---

## 💡 Applications


---

## 🧰 Development Roadmap


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
