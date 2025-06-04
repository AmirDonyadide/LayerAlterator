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
