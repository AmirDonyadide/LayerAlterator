# --- A) IMPORT LIBRARIES ---
import os
import pandas as pd
import rasterio
import numpy as np
from rasterio.features import rasterize
import geopandas as gpd


# --- B) FUNCTIONS ---
def load_vector_mask(vector_mask_path, layer_name=None):
    """
    Load a vector mask (polygon layer) from a supported geospatial file format.

    Supported formats:
    - GPKG (GeoPackage): requires a layer name if the file contains multiple layers.
    - GeoJSON / JSON: single-layer vector data.
    - Shapefile (.shp): standard ESRI format.

    Parameters:
    -----------
    vector_mask_path : str
        Path to the vector file (e.g., .gpkg, .geojson, .json, .shp).
    
    layer_name : str, optional
        Required only for GPKG files with multiple layers.

    Returns:
    --------
    geopandas.GeoDataFrame
        The loaded vector data as a GeoDataFrame.

    Raises:
    -------
    ValueError
        If the file extension is not one of the supported formats.
    """

    # Handle GeoPackage format
    if vector_mask_path.endswith(".gpkg"):
        gdf_mask = gpd.read_file(vector_mask_path, layer=layer_name)
        return gdf_mask

    # Handle GeoJSON, JSON, or Shapefile
    elif vector_mask_path.endswith((".geojson", ".json", ".shp")):
        gdf_mask = gpd.read_file(vector_mask_path)
        return gdf_mask

    # Raise error for unsupported formats
    else:
        raise ValueError("Unsupported vector format. Use GPKG, GeoJSON, or Shapefile.")


def check_crs_match(gdf, rules, ucp_folder, fractions_folder):
    """
    Check whether the Coordinate Reference Systems (CRS) of all raster layers 
    match the CRS of the input GeoDataFrame.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        The reference GeoDataFrame whose CRS will be used for comparison.
    
    rules : list of str
        List of raster layer filenames (with extensions) to check.
    
    ucp_folder : str
        Path to the folder containing UCP raster layers.
    
    fractions_folder : str
        Path to the folder containing fraction raster layers (those starting with "F_").

    Output:
    -------
    None
        The function prints warnings for:
        - Any raster that could not be opened.
        - Any CRS mismatch between raster layers and the input GeoDataFrame.
        - Or confirms that all CRSs match.
    """

    mismatched_layers = []  # Store mismatches for reporting

    for layer_with_ext in rules:
        # Choose the appropriate folder based on the filename prefix
        if layer_with_ext.startswith("F_"):
            raster_path = os.path.join(fractions_folder, layer_with_ext)
        else:
            raster_path = os.path.join(ucp_folder, layer_with_ext)

        try:
            # Open the raster file and read its CRS
            with rasterio.open(raster_path) as src:
                raster_crs = src.crs
                # Compare with GeoDataFrame CRS
                if raster_crs != gdf.crs:
                    mismatched_layers.append((layer_with_ext, str(raster_crs)))
        except Exception as e:
            # Warn if the file could not be opened
            print(f"Warning: Could not open raster for layer {layer_with_ext}: {e}")

    # Print summary of results
    if mismatched_layers:
        print("Warning: CRS mismatch detected in the following layers:")
        for lyr, crs in mismatched_layers:
            print(f" - {lyr}: CRS = {crs}, differs from vector CRS = {gdf.crs}")
    else:
        print("All raster layers have the same CRS as the vector mask.")


def parse_rules_from_mask(gdf, rules):
    """
    Analyze and validate rule definitions for raster layer processing,
    based on per-polygon vector attributes in a GeoDataFrame.

    This function classifies the provided rules into one of several predefined categories (C0 to C5),
    and enforces specific per-feature checks when rule type is "mask".

    Categories:
    -----------
    - C0: All rules are 'none' → No processing.
    - C1: All rules are 'mask' → Enforce:
        - C1.1: All values (fractions and UCP) ∈ [0, 1]
        - C1.2: IMD ≥ BSF
        - C1.3: Sum(F_*) == 1
    - C2: All rules are 'pct' → Uniform percentage-based changes.
    - C3: Mix of 'pct' and 'none' → Apply PCT, treat NONE as 0%.
    - C4: Invalid combination of 'mask' and 'none' → Raise error.
    - C5: Invalid combination of 'mask' and 'pct' → Raise error.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Polygons with attribute columns named after the raster layers.

    rules : dict
        Dictionary mapping raster layer names (with or without .tif) to one of:
        {'mask', 'pct', 'none'}.

    Returns:
    --------
    tuple
        rule_code : str
            One of {"C0", "C1", "C2", "C3"} indicating the processing category.
        rule_info : dict
            Reserved for future metadata (currently empty).

    Raises:
    -------
    ValueError
        If the rule combination is invalid or if any polygon fails
        rule-specific constraints (e.g. sum of fractions ≠ 1, out-of-bound values).
    """

    # Normalize layer names
    normalized_keys = [k.replace(".tif", "") for k in rules]
    fractions_keys = [k for k in normalized_keys if k.startswith("F_")]
    ucp_keys = [k for k in normalized_keys if not k.startswith("F_")]
    rule_types = set(rules.values())

    # --- Rule C0: No processing ---
    if rule_types == {"none"}:
        print("Rule C0: All layers set to NONE. No processing will be done.")
        return "C0", {}

    # --- Rule C1: All layers require masking ---
    if rule_types == {"mask"}:
        print("Rule C1: All layers set to MASKING. Checking per-polygon constraints...")

        for idx, row in gdf.iterrows():
            print(f"\nChecking Feature ID {idx}")

            # C1.1 + C1.3: Fraction values must be [0, 1] and sum to 1
            fraction_values = {}
            for k in fractions_keys:
                val = row.get(k)
                if pd.notna(val):
                    try:
                        fraction_values[k] = float(val)
                    except (ValueError, TypeError):
                        raise ValueError(f"C1.3 Violation in feature {idx}: '{k}' has non-convertible value: {val}")

            # UCP values must also be [0, 1]
            ucp_values = {}
            for k in ucp_keys:
                val = row.get(k)
                if pd.notna(val):
                    try:
                        ucp_values[k] = float(val)
                    except (ValueError, TypeError):
                        raise ValueError(f"C1.1 Violation in feature {idx}: '{k}' has non-convertible value: {val}")

            combined_values = {**fraction_values, **ucp_values}
            out_of_bounds = {k: v for k, v in combined_values.items() if not (0.0 <= v <= 1.0)}
            if out_of_bounds:
                print("\nC1.1 Violation: Values outside [0,1] detected.")
                df_show = pd.DataFrame({
                    "Key": list(out_of_bounds.keys()),
                    "Value": list(out_of_bounds.values())
                })
                df_show.insert(0, "Feature ID", idx)
                print(df_show.to_string(index=False))
                raise ValueError(f"C1.1 Violation in feature {idx}: Some values not in [0,1].")

            # C1.2: IMD ≥ BSF
            imd = row.get("IMD")
            bsf = row.get("BSF")
            print(f"IMD: {imd}, BSF: {bsf}")
            if imd is None or bsf is None:
                raise ValueError(f"C1.2 Violation in feature {idx}: IMD or BSF is missing.")
            try:
                imd_val = float(imd)
                bsf_val = float(bsf)
            except (ValueError, TypeError):
                raise ValueError(f"C1.2 Violation in feature {idx}: IMD or BSF not convertible to float.")
            if imd_val < bsf_val:
                print("C1.2 Violation: IMD < BSF")
                df_show = pd.DataFrame([{
                    "Feature ID": idx,
                    "IMD": imd,
                    "BSF": bsf
                }])
                print(df_show.to_string(index=False))
                raise ValueError(f"C1.2 Violation in feature {idx}: IMD < BSF")

            # C1.3: Fraction sum == 1
            fraction_sum = sum(fraction_values.values())
            df_show = pd.DataFrame({
                "Fraction Key": list(fraction_values.keys()),
                "Value": list(fraction_values.values())
            })
            df_show.insert(0, "Feature ID", idx)
            df_show.loc[len(df_show.index)] = [idx, "SUM", fraction_sum]
            print("Fraction values and sum:")
            print(df_show.to_string(index=False))
            if not np.isclose(fraction_sum, 1.0):
                print("C1.3 Violation: Sum of fractions != 1.0")
                raise ValueError(f"C1.3 Violation in feature {idx}: Sum = {fraction_sum} != 1.0")

        print("\nAll per-polygon constraints (C1.1, C1.2, C1.3) are satisfied.")
        return "C1", {}

    # --- Rule C2: Percentage-based processing only ---
    if rule_types == {"pct"}:
        print("Rule C2: All layers set to PCT. Proceeding with PCT logic.")
        return "C2", {}

    # --- Rule C3: pct + none combination ---
    if rule_types == {"pct", "none"}:
        print("Rule C3: Layers set to PCT and NONE. Proceeding with PCT logic and treating NONE as 0.")
        return "C3", {}

    # --- Rule C4: Invalid mix of mask + none ---
    if rule_types == {"mask", "none"}:
        print("Rule C4 violation: MASKING + NONE is not allowed.")
        raise ValueError("Rule C4 violation: Please change NONE to MASKING and provide valid attributes.")

    # --- Rule C5: Invalid mix of mask + pct ---
    if "mask" in rule_types and "pct" in rule_types:
        print("Rule C5 violation: MASKING + PCT is not allowed.")
        raise ValueError("Rule C5 violation: Please use either MASKING or PCT rules exclusively.")

    # --- Unknown rule types ---
    raise ValueError("Invalid rule combination detected in rule file.")


def apply_masking(gdf, raster_path, attr_name, output_path):
    """
    Apply masking values from vector attributes to a raster.

    For each polygon in the input GeoDataFrame, the function assigns the value 
    of a specified attribute (`attr_name`) to the corresponding area in a raster.
    The modified raster is then written to a new file.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Vector data with geometries and a numeric attribute used for masking.
    
    raster_path : str
        Path to the input raster file to be masked.
    
    attr_name : str
        Name of the attribute in `gdf` that contains the values to assign.
    
    output_path : str
        Destination path for the output masked raster.

    Output:
    -------
    None
        The function saves the modified raster to `output_path`.
        It also prints informative messages during processing.
    """

    # Open the input raster
    with rasterio.open(raster_path) as src:
        data = src.read(1)               # Read the first (and typically only) raster band
        meta = src.meta.copy()           # Copy raster metadata
        nodata_val = src.nodata          # Get NoData value

        # Report on NoData pixels
        if nodata_val is not None:
            nodata_mask = (data == nodata_val)
            count_nodata = np.count_nonzero(nodata_mask)
            print(f"Detected {count_nodata} NoData pixels in input raster.")
        else:
            print("No explicit NoData value defined in the input raster.")

        # Loop over each polygon feature and apply its attribute value to the raster
        for idx, row in gdf.iterrows():
            value = row[attr_name]  # Get the value to burn into the raster

            # Rasterize the current geometry as a binary mask (1 inside polygon, 0 elsewhere)
            mask_arr = rasterize(
                [(row.geometry, 1)],
                out_shape=src.shape,
                transform=src.transform,
                fill=0,
                dtype=np.uint8
            )

            # Update the raster data where the mask is 1 (i.e., inside the polygon)
            data = np.where(mask_arr == 1, value, data)

        print(f"Applying masking for attribute '{attr_name}' on raster {os.path.basename(raster_path)} with value {value}")

        # Write the updated raster to a new file
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(data, 1)

    print(f"Masking complete: output saved to {os.path.basename(output_path)}.")


def apply_mask_rule_all(gdf, rules, ucp_folder, fractions_folder, output_folder):
    """
    Apply the 'mask' rule to all applicable raster layers based on vector attributes.

    For each raster layer in the rules dictionary that is set to "mask", this function:
    - Locates the corresponding raster in the appropriate folder (UCP or fractions).
    - Applies the masking operation using vector attributes from the GeoDataFrame.
    - Saves the output to the specified output directory with a "_mask.tif" suffix.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Vector polygons with attributes corresponding to raster layer names.
    
    rules : dict
        Mapping of raster layer names (with or without .tif extensions) to rule types.
        Only layers with rule value "mask" will be processed.
    
    ucp_folder : str
        Directory containing general UCP raster layers.
    
    fractions_folder : str
        Directory containing fraction raster layers (those starting with "F_").
    
    output_folder : str
        Destination directory where masked rasters will be saved.

    Output:
    -------
    None
        The function creates new raster files in `output_folder`, one for each layer
        that was masked, named with a "_mask.tif" suffix.
    """

    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)

    for layer, rule in rules.items():
        # Only process layers marked for masking
        if rule != "mask":
            continue

        # Remove .tif extension if present
        if layer.endswith(".tif"):
            layer = layer[:-4]

        # Select appropriate folder based on prefix
        if layer.startswith("F_"):
            raster_path = os.path.join(fractions_folder, layer + ".tif")
        else:
            raster_path = os.path.join(ucp_folder, layer + ".tif")

        # Construct output path for masked raster
        output_path = os.path.join(output_folder, layer + "_mask.tif")

        # Apply masking using the provided vector layer and attribute
        apply_masking(gdf, raster_path, layer, output_path)


def is_fraction_layer(layer_name):
    """
    Determine if a raster layer name refers to a fraction layer.

    Fraction layers are identified by a specific naming convention: they start with "F_".

    Parameters:
    -----------
    layer_name : str
        The name of the raster layer (with or without file extension).

    Returns:
    --------
    bool
        True if the layer is a fraction layer (starts with "F_"), False otherwise.
    """
    return layer_name.startswith("F_")


def apply_pct_ucp(
    gdf,
    raster_path,
    attr_name,
    rule_type,
    output_path,
    exceed_handling="clip",
    zero_handling="raise",
    zero_value=0.01
):
    """
    Apply per-polygon percentage change to UCP raster pixels using vector attributes.

    For each polygon in the GeoDataFrame, this function adjusts the raster values 
    in the corresponding area by a percentage specified in the given attribute column.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Polygons containing percentage values for modifying raster regions.
    
    raster_path : str
        Path to the input UCP raster file.
    
    attr_name : str
        Name of the GeoDataFrame column that holds percentage change values.
    
    rule_type : str
        Either 'pct' to apply the percentage change, or 'none' to skip modification.
    
    output_path : str
        File path to save the modified raster.

    exceed_handling : str, default='clip'
        How to handle values outside the valid [0, 1] range after modification.
        Options:
            - 'clip': Truncate values to [0, 1].
            - 'normalize': Rescale values across the full [0, 1] range.
            - 'ignore': Leave values unchanged.

    zero_handling : str, default='raise'
        How to treat pixels with value 0 before applying percentage change.
        Options:
            - 'raise': Replace 0s with `zero_value` before scaling.
            - 'preserve': Leave 0s as-is.

    zero_value : float, default=0.01
        Value to replace 0s with if `zero_handling='raise'`.

    Returns:
    --------
    np.ndarray
        The modified raster data as a NumPy array.
    """

    with rasterio.open(raster_path) as src:
        data = src.read(1).astype(np.float32)
        meta = src.meta.copy()
        nodata_val = src.nodata

        # Preserve NoData metadata
        if nodata_val is not None:
            meta['nodata'] = nodata_val
            nodata_mask = (data == nodata_val)
            count_nodata = np.count_nonzero(nodata_mask)
            if count_nodata > 0:
                print(f"Detected {count_nodata} NoData pixels in input raster: {os.path.basename(raster_path)}.")
        else:
            print("No explicit NoData value defined in the input raster.")
            nodata_mask = None

        # Process each polygon feature
        for idx, row in gdf.iterrows():
            pct_value = 0.0
            if rule_type == "pct":
                val = row.get(attr_name)
                if val is not None and not np.isnan(val):
                    pct_value = val

            factor = 1 + (pct_value / 100.0)
            print(attr_name, rule_type, pct_value, factor)

            # Rasterize polygon geometry as a binary mask
            mask_arr = rasterize(
                [(row.geometry, 1)],
                out_shape=src.shape,
                transform=src.transform,
                fill=0,
                dtype=np.uint8
            )

            # Handle zero values before update
            if zero_handling == "raise":
                zero_mask = (data == 0.0) & (mask_arr == 1)
                if nodata_mask is not None:
                    zero_mask = zero_mask & (~nodata_mask)
                data = np.where(zero_mask, zero_value, data)

            # Mask only valid (non-NoData) areas
            if nodata_mask is not None:
                update_mask = (mask_arr == 1) & (~nodata_mask)
            else:
                update_mask = (mask_arr == 1)

            # Apply the percentage modification
            data = np.where(update_mask, data * factor, data)

        # Post-processing: handle out-of-bound values
        valid_data = data[~nodata_mask] if nodata_mask is not None else data
        min_val = np.min(valid_data)
        max_val = np.max(valid_data)

        if max_val > 1.0 or min_val < 0.0:
            print(f"Warning: values outside [0,1] detected in {os.path.basename(output_path)}. "
                  f"Handling method: {exceed_handling}.")

            if exceed_handling == "clip":
                data = np.where(~nodata_mask, np.clip(data, 0.0, 1.0), data) if nodata_mask is not None else np.clip(data, 0.0, 1.0)

            elif exceed_handling == "normalize":
                if max_val != min_val:
                    scaled = (valid_data - min_val) / (max_val - min_val)
                    data = np.where(~nodata_mask, scaled, data) if nodata_mask is not None else scaled
                else:
                    data[:] = 0.0

            elif exceed_handling == "ignore":
                pass  # No action taken

            else:
                raise ValueError("Invalid exceed_handling value. Use 'clip', 'normalize', or 'ignore'.")

        # Restore NoData values in output
        if nodata_mask is not None:
            data = np.where(nodata_mask, nodata_val, data)

        # Save modified raster
        with rasterio.open(output_path, 'w', **meta) as dst:
            dst.write(data, 1)

    return data


def apply_pct_all_fractions(gdf, rules, fractions_folder, output_folder):
    """
    Apply per-polygon percentage changes to all fraction layers and normalize them.

    This function:
    - Loads all relevant fraction rasters (those starting with "F_").
    - For each polygon in the GeoDataFrame:
        - Applies the specified percentage change per layer.
        - Normalizes the pixel stack so all fractions sum to 1.0 within the polygon.
    - Saves updated rasters to the output folder with a "_pct.tif" suffix.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Polygon geometries with attributes used to adjust fraction layers.

    rules : dict
        Dictionary mapping raster filenames (e.g., 'F_AC.tif') to rule types:
        only those with prefix "F_" and rule == "pct" will be processed.

    fractions_folder : str
        Directory containing the original fraction rasters.

    output_folder : str
        Directory to save the adjusted and normalized fraction rasters.

    Output:
    -------
    None
        Outputs are saved as new rasters. Prints status updates during processing.
    """

    os.makedirs(output_folder, exist_ok=True)

    # Filter rules to include only fraction layers
    fraction_rules = {k: v for k, v in rules.items() if is_fraction_layer(k.replace(".tif", ""))}
    fraction_layers = list(fraction_rules.keys())
    if not fraction_layers:
        return

    # Load all fraction raster layers
    fraction_data = {}
    meta = None
    nodata_mask = None

    for fname in fraction_layers:
        path = os.path.join(fractions_folder, fname)
        with rasterio.open(path) as src:
            arr = src.read(1).astype(np.float32)
            if meta is None:
                meta = src.meta.copy()
                if src.nodata is not None:
                    nodata_mask = (arr == src.nodata)
                    meta["nodata"] = src.nodata
                else:
                    nodata_mask = None
                    print(f"No explicit NoData value defined in input raster: {os.path.basename(path)}")
            fraction_data[fname] = arr

    shape = (meta["height"], meta["width"])
    transform = meta["transform"]

    # Process each polygon
    for _, row in gdf.iterrows():
        geom = row.geometry

        # Rasterize geometry to mask area
        mask_arr = rasterize(
            [(geom, 1)],
            out_shape=shape,
            transform=transform,
            fill=0,
            dtype=np.uint8
        )
        polygon_pixels = mask_arr == 1
        if not np.any(polygon_pixels):
            continue

        # Stack raster arrays: shape = (N_layers, N_pixels)
        pixel_stack = np.stack([fraction_data[fname] for fname in fraction_layers], axis=0)
        polygon_values = pixel_stack[:, polygon_pixels]

        # Apply % changes per layer
        for i, fname in enumerate(fraction_layers):
            rule_type = fraction_rules[fname]
            attr_name = fname.replace(".tif", "")
            pct_value = 0.0
            if rule_type == "pct":
                val = row.get(attr_name)
                if val is not None and not np.isnan(val):
                    pct_value = val
            factor = 1 + (pct_value / 100.0)
            print(attr_name, rule_type, pct_value, factor)
            polygon_values[i, :] *= factor

        # Normalize to ensure all layers sum to 1 per pixel
        sums = np.sum(polygon_values, axis=0)
        sums_safe = np.where(sums == 0, 1.0, sums)
        polygon_values /= sums_safe[np.newaxis, :]

        # Optional validation
        check_sums = np.sum(polygon_values, axis=0)
        print("Pixel sum stats:", np.min(check_sums), np.max(check_sums), np.mean(check_sums))

        # Write modified values back to each layer
        for i, fname in enumerate(fraction_layers):
            arr = fraction_data[fname]
            arr[polygon_pixels] = polygon_values[i, :]
            fraction_data[fname] = arr

    # Re-apply NoData mask
    if nodata_mask is not None:
        for fname in fraction_layers:
            arr = fraction_data[fname]
            arr[nodata_mask] = meta["nodata"]
            fraction_data[fname] = arr

    # Save modified rasters
    for fname in fraction_layers:
        out_path = os.path.join(output_folder, fname.replace(".tif", "_pct.tif"))
        with rasterio.open(out_path, 'w', **meta) as dst:
            dst.write(fraction_data[fname], 1)

    print("Finished applying percentage changes and polygon-wise normalization to fraction layers.")


def apply_pct_all(gdf, rules, ucp_folder, fractions_folder, output_folder):
    """
    Apply percentage-based changes to both UCP and fraction raster layers using vector attributes.

    This function separates rules into two categories:
    - UCP layers: processed individually using `apply_pct_ucp()`.
    - Fraction layers: processed in batch using `apply_pct_all_fractions()`.

    Parameters:
    -----------
    gdf : geopandas.GeoDataFrame
        Polygons with attributes used to define percentage adjustments.

    rules : dict
        Dictionary mapping raster layer filenames (e.g., "F_AC.tif", "IMD.tif")
        to rule types ("pct", "none", "mask", etc.). Only "pct" and "none" are used here.

    ucp_folder : str
        Folder path containing UCP raster layers (e.g., IMD, BSF).

    fractions_folder : str
        Folder path containing fraction raster layers (those prefixed with "F_").

    output_folder : str
        Destination folder where the updated raster files will be saved.

    Output:
    -------
    None
        Outputs are written to disk with "_pct.tif" suffix for each modified layer.
    """

    os.makedirs(output_folder, exist_ok=True)

    # Separate UCP and fraction layers
    ucp_rules = {}
    fraction_rules = {}

    for layer_with_ext, rule_type in rules.items():
        if rule_type not in {"pct", "none"}:
            continue

        layer_name = layer_with_ext.replace(".tif", "")
        if is_fraction_layer(layer_name):
            fraction_rules[layer_with_ext] = rule_type
        else:
            ucp_rules[layer_with_ext] = rule_type

    # Apply percentage changes to all fraction layers at once
    if fraction_rules:
        apply_pct_all_fractions(gdf, fraction_rules, fractions_folder, output_folder)

    # Apply percentage changes to each UCP layer one at a time
    for layer_with_ext, rule_type in ucp_rules.items():
        layer_name = layer_with_ext.replace(".tif", "")
        raster_path = os.path.join(ucp_folder, layer_with_ext)
        output_path = os.path.join(output_folder, layer_name + "_pct.tif")

        if not os.path.exists(raster_path):
            print(f"Warning: Missing raster file: {raster_path}")
            continue

        apply_pct_ucp(gdf, raster_path, layer_name, rule_type, output_path)


def check_imd_bsf_consistency(output_folder, imd_filename="IMD_pct.tif", bsf_filename="BSF_pct.tif"):
    """
    Check whether IMD ≥ BSF for each pixel in the output rasters.

    This validation ensures that after percentage adjustments, the IMD raster values
    are still greater than or equal to the corresponding BSF raster values per pixel.

    Parameters:
    -----------
    output_folder : str
        Directory where the adjusted output rasters are saved.
    
    imd_filename : str, default="IMD_pct.tif"
        Filename of the adjusted IMD raster.
    
    bsf_filename : str, default="BSF_pct.tif"
        Filename of the adjusted BSF raster.

    Output:
    -------
    None
        Prints a warning if any pixels violate the IMD ≥ BSF constraint.
        Prints confirmation if all pixels are valid.
    """

    imd_path = os.path.join(output_folder, imd_filename)
    bsf_path = os.path.join(output_folder, bsf_filename)

    # Check file existence
    if not os.path.exists(imd_path) or not os.path.exists(bsf_path):
        print("Warning: Cannot perform IMD ≥ BSF check because one or both files are missing.")
        return

    with rasterio.open(imd_path) as src_imd, rasterio.open(bsf_path) as src_bsf:
        imd = src_imd.read(1)
        bsf = src_bsf.read(1)

        # Ensure both rasters have the same dimensions
        if imd.shape != bsf.shape:
            print("Warning: IMD and BSF rasters have different shapes. Cannot compare.")
            return

        # Check for violations of IMD < BSF, ignoring NaNs
        invalid = (imd < bsf) & (~np.isnan(imd)) & (~np.isnan(bsf))

        if np.any(invalid):
            n_invalid = np.count_nonzero(invalid)
            total = imd.size
            pct = (n_invalid / total) * 100
            print(f"Warning: {n_invalid} pixels ({pct:.2f}%) have IMD < BSF. "
                  "Consider adjusting the 'pct' attributes in the vector mask.")
        else:
            print("Check passed: All pixels satisfy IMD ≥ BSF.")