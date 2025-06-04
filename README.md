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

#### C.1) Check CRS Consistency

Function: `check_crs_match(gdf, rules, ucp_folder, fractions_folder)`

This function verifies that the Coordinate Reference System (CRS) of every raster layer matches the CRS of the input vector file (`gdf`).

- For each layer listed in the rule file:
  - Open the corresponding raster.
  - Compare its CRS with the vector mask.
  - Log any mismatches.

**Why this matters:** Spatial misalignment can lead to incorrect rasterization or masking.


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

the check passes, `rule_id` is used to direct the next phase of processing.

### D) Apply Mask Rule

This step performs raster updates using fixed values from the vector layer. It only applies when the rule set has been classified as **C1** (masking).

#### D.1) Mask Individual Raster with Vector Attributes

Function: `apply_masking(gdf, raster_path, attr_name, output_path)`

This function updates a raster layer using fixed values taken from each polygon in the vector dataset.

- Reads the input raster.
- Iterates over all vector features.
- Rasterizes each polygon geometry.
- Replaces the corresponding raster pixels with the polygon's attribute value.
- Writes the modified raster to the output path.

Example logic:

```python
with rasterio.open(raster_path) as src:
    data = src.read(1)
    for idx, row in gdf.iterrows():
        value = row[attr_name]
        mask_arr = rasterize([(row.geometry, 1)], ...)
        data = np.where(mask_arr == 1, value, data)
```

If the raster contains a NoData value, it is preserved throughout the operation.


#### D.2) Apply Masking to All Relevant Layers

Function: `apply_mask_rule_all(gdf, rules, ucp_folder, fractions_folder, output_folder)`

This function loops over all layers defined in the rules and applies masking to each one with a rule of `"mask"`.

- Automatically determines the raster source folder:
  - Fraction layers (prefix `F_`) → `fractions_folder`
  - UCP layers → `ucp_folder`
- Constructs input and output paths for each file.
- Calls `apply_masking()` for each valid layer.


#### D.3) Run Masking Based on Rule ID

The rule type is checked before running masking logic. Masking is only executed if the detected rule type is `C1`.

```python
if rule_id in {"C1"}:
    apply_mask_rule_all(gdf_mask, rules, ucp_folder, fractions_folder, output_folder)
```

Resulting rasters are saved with the suffix `_mask.tif` in the `./output` directory.


**Why this matters:**  
This step allows per-polygon attribute values to directly overwrite raster pixels. It is used in planning scenarios where each land unit is prescribed a deterministic outcome.

### E) Apply Percentage Change Rule

This step adjusts raster values based on percentage change rules defined in the vector attributes. It applies when the rule classification is **C2** or **C3**.


#### E.1) Identify Fraction Layers

Function: `is_fraction_layer(layer_name)`

Checks whether a given raster layer is a fractional land cover layer. These are identified by the prefix `F_`.


#### E.2) Apply Percentage to UCP Layers

Function: `apply_pct_ucp(...)`

This function updates a single UCP raster layer by applying percentage-based modifications defined in the vector attributes.

Key features:
- Each polygon provides a % value that is applied within its area.
- Supports various handling options for:
  - **Zero values** (`preserve` or `raise`)
  - **Out-of-bound results** (`clip`, `normalize`, `ignore`)
- Ensures NoData pixels remain unchanged.

Example:

```python
factor = 1 + (pct_value / 100.0)
data = np.where(update_mask, data * factor, data)
```


#### E.3) Apply Percentage to Fraction Layers (with Normalization)

Function: `apply_pct_all_fractions(...)`

- Loads all fraction rasters (`F_*`) into memory.
- Applies the polygon-wise percentage changes per layer.
- After modification, pixel values are normalized to ensure all fraction values sum to 1.0 per pixel.

This guarantees valid fraction outputs and prevents distortion caused by imbalanced updates.


#### E.4) Orchestrate All Percentage Updates

Function: `apply_pct_all(...)`

Coordinates the update of:
- **UCP layers**: individually processed via `apply_pct_ucp()`
- **Fraction layers**: jointly processed and normalized via `apply_pct_all_fractions()`

This function is called only if the detected rule type is C2 or C3:

```python
if rule_id in {"C2", "C3"}:
    apply_pct_all(gdf_mask, rules, ucp_folder, fractions_folder, output_folder)
```

Output raster files are saved using the `_pct.tif` suffix in the `./output` folder.


**Why this matters:**  
This mechanism supports spatially variable simulation of urban or ecological changes, ensuring controlled and balanced modifications across layers.

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
