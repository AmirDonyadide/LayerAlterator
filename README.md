# LayerAlterator

**LayerAlterator** is a Python-based geospatial simulation tool that programmatically modifies raster datasets using vector-defined spatial rules. Developed for applications in urban planning, climate adaptation, and land-use forecasting, it provides a lightweight engine for simulating "what-if" scenarios such as densification, reforestation, or infrastructure development.

The tool is rule-driven and applies transformations based on polygon attributes specified in a GeoPackage, GeoJSON, or Shapefile. It supports both absolute value substitution (masking) and relative change (percentage adjustment), and it ensures normalization of fractional layers, data consistency, and CRS alignment. 

Designed to be modular, testable, and easily extensible, LayerAlterator is suited for integration into Digital Twin platforms or stand-alone exploratory simulations.

---

## Overview

- Apply attribute-based transformations to raster layers using vector masks
- Designed for climate-sensitive urban simulations (e.g., UHI)
- Supports both deterministic (mask) and proportional (pct) rule logic
- Ensures CRS alignment, NoData preservation, and normalization
- Modular Python architecture with Jupyter support
- Ready for integration into Digital Twins and scenario prototyping

---

## Key Features

- Rule-driven raster processing with vector mask input
- Support for `mask`, `pct`, and `none` rule types
- Validation of polygon attributes and logical conditions
- Automated CRS consistency check for all input files
- Pixel-wise normalization for land cover fraction layers
- Modular function-based architecture (`layer_alterator`, `apply_masking`, etc.)
- Clear output management with `_mask.tif` / `_pct.tif` suffixing
- Visual inspection-ready outputs (QGIS compatible)
- Jupyter-integrated test suite for debugging and demonstration
- Lightweight and dependency-lean (only open-source libraries)

---

## Repository Structure

```
LayerAlterator/
├── functions.py                    # Main processing functions
├── test_functions.ipynb            # Jupyter notebook for running and testing all modules
├── requirements.txt                # Required libraries
├── test_data/                      # Contains input/output examples for all test functions
│   ├── fun_1/ ... fun_11/          # Each folder corresponds to a separate test case
│       ├── vector/                 # Polygon files (.gpkg, .shp, .geojson)
│       ├── ucps/                   # UCP raster inputs (e.g., IMD.tif, BSF.tif)
│       ├── lc_fractions/           # Fractional raster inputs (F_*.tif)
│       ├── operation_rules_*.json  # Rule files per test case
│       └── output/                 # Outputs produced (_mask.tif, _pct.tif)
├── README.md                       # This file
```
---

## Input Data Structure

The input data must follow a clearly defined folder and naming convention:

```
test_data/fun_X/
├── vector/                  # Vector mask (one of .gpkg, .geojson, .shp)
├── ucps/                    # UCP raster files: IMD.tif, BSF.tif, etc.
├── lc_fractions/            # Fraction rasters: F_AC.tif, F_UF.tif, etc.
├── operation_rules_*.json   # JSON rule file
```

### Vector Mask
- File formats supported: `.gpkg`, `.geojson`, `.shp`
- Must contain attribute fields matching the raster names (e.g., `IMD`, `BSF`, `F_AC`, `F_UF`)
- Used to define polygon-level logic

### Raster Inputs
- UCP folder: stores general-purpose raster layers (e.g., building metrics)
- Fraction folder: land cover layers, prefixed with `F_`, must sum to 1 per pixel

### Rules File
- JSON file defining rules per raster layer:
  - `"mask"`: assign fixed value from vector
  - `"pct"`: apply percentage change
  - `"none"`: skip layer

Example `operation_rules_C3.json`:
```json
{
  "IMD.tif": "pct",
  "BSF.tif": "pct",
  "F_AC.tif": "mask",
  "F_UF.tif": "mask"
}
```

---

## Documentation 

Each function is fully documented in the source code and in `test_functions.ipynb`. The main steps and responsibilities are:

| Step | Function(s) | Description |
|------|-------------|-------------|
| 1️ Load vector | `gpd.read_file()` | Reads polygon mask with attributes |
| 2️ Load rasters | `rasterio.open()` | Loads UCP/fraction TIFF files |
| 3️ Parse rules | `parse_rules_from_mask()` | Classifies into rule sets (C0–C5) |
| 4️ Check CRS | `check_crs_match()` | Validates spatial consistency |
| 5️ Apply Mask | `apply_mask_rule_all()` | Runs fixed-value update for rule C1 |
| 6️ Apply Pct | `apply_pct_all()` | Runs relative-change updates for rule C2/C3 |
| 7️ Save Output | `rasterio.write()` | Writes final TIFFs to output folder |

Each step is independently testable and includes appropriate error handling and logging.

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

## Functionality Details

The tool is driven by the central `layer_alterator()` function, which executes the full pipeline:

```python
layer_alterator(
    vector_mask_path,
    ucp_folder,
    fractions_folder,
    rules_path,
    output_folder
)
```

### Logic Flow:
1. Load and validate the vector mask.
2. Read the JSON rule file and determine processing type (C0–C5).
3. Check CRS consistency across all input rasters.
4. Based on the rule type:
   - Run `apply_mask_rule_all()` for C1
   - Run `apply_pct_all()` for C2/C3
5. Each updated raster is saved with a suffix `_mask.tif` or `_pct.tif`.

### Function Summary:
- `parse_rules_from_mask()` — classify rule type (C0–C5)
- `check_crs_match()` — ensure raster and vector alignment
- `apply_masking()` — per-layer fixed value masking
- `apply_pct_ucp()` — apply percentage to UCP raster
- `apply_pct_all_fractions()` — apply and normalize fractions
- `apply_mask_rule_all()` — apply masking to all layers
- `apply_pct_all()` — coordinate UCP + fraction updates

This modular design allows the user to plug-and-play functionality, extend scenarios, or chain processing steps across simulations.

---

## Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Prepare input data**:
- Organize a folder (e.g., `test_data/fun_11/`) with:
  - `vector/` containing a `.gpkg`, `.geojson`, or `.shp`
  - `ucps/` and `lc_fractions/` containing raster `.tif` files
  - a rule file like `operation_rules_C3.json`

3. **Run from Python or notebook**:
```python
from functions import layer_alterator

layer_alterator(
    vector_mask_path="./test_data/fun_11/vector/test_mask.geojson",
    ucp_folder="./test_data/fun_11/ucps",
    fractions_folder="./test_data/fun_11/lc_fractions",
    rules_path="./test_data/fun_11/operation_rules_C3.json",
    output_folder="./test_data/fun_11/output"
)
```

4. **Inspect outputs** in the specified folder. Output files will have `_mask.tif` or `_pct.tif` suffixes.

---

## Sample Output

After running the tool, the `output/` folder will contain:

```
output/
├── IMD_pct.tif
├── BSF_pct.tif
├── F_AC_mask.tif
├── F_UF_mask.tif
```

- These files represent the updated rasters after applying the rules.
- You can open them in QGIS for visual inspection or use `rasterio`/`gdalinfo` for stats.

📌 All processing respects NoData, alignment, and normalization constraints.

---

## Applications

LayerAlterator was developed to support spatially explicit simulation needs in urban and environmental modeling contexts. Example applications include:

- 🏙️ Urban densification studies
- 🌳 Reforestation or green infrastructure planning
- 🌡️ Urban Heat Island mitigation simulation
- 📊 Preprocessing for Local Climate Zone modeling
- 🧪 Scenario testing in Digital Twin platforms
- 🛰️ Land cover change prototype modeling

The flexible rule-driven engine allows users to test policy interventions, simulate transformation hypotheses, or prototype planning alternatives with minimal computational overhead.

---

## Development Roadmap

Planned or potential enhancements include:

- Batch rule scenario support (loop over multiple JSON rule sets)
- GUI or web interface for non-technical users
- Smart validation for conflicting or overlapping polygon logic
- Packaged CLI tool version for deployment
- Integration hooks for use in Digital Twin APIs or dashboards

Feature suggestions and contributions are welcome!

---

## Author

**Amirhossein Donyadidegan**  
MSc Geoinformatics Engineering  
Politecnico di Milano  
📫 [GitHub](https://github.com/AmirDonyadide) | 📍 Karlsruhe / Milano

---

## Supervisor

**Dr. Daniele Oxoli**  
Assistant Professor, Politecnico di Milano  
🌐 [GitHub](https://github.com/danioxoli)

---

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.
