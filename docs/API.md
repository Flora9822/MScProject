# API Reference

All core pipeline functions live in the module `import_cleanup_prototype`.

---

## reload_rules(rules_file_path: str) → None

Reload pipeline rules from an external JSON file.

* **Parameters**

  * `rules_file_path` – Path to a JSON file following the `pipeline_rules.json` schema.

* **Behavior**

  * Updates the global `pipeline_rules` dictionary used by the pipeline.
  * Prints `"Reloaded pipeline_rules from: <path>"` to stdout.

---

## preview_renaming(folder_path: Optional[str]) → Dict[str, str]

Returns a mapping from each asset base name to its collision-free new name (using the current naming prefix).

* **Parameters**

  * `folder_path` – Path to a directory containing assets. If `None`, defaults to `../test_assets`.

* **Returns**

  * A dictionary mapping `{ base_name: new_name }`, where `new_name` reflects sanitized and collision-safe naming.

* **Raises**

  * `FileNotFoundError` if `folder_path` does not exist.

---

## fix_missing_paths() → None

Scan the Maya scene for missing file references (textures, caches, etc.) and auto-fix them if possible.

* **Behavior**

  * Uses `cmds.filePathEditor` to find missing paths.
  * Runs `cmds.filePathEditor(edit=True, fixMissingPath=True)` if any missing files are found.
  * Prints a summary of actions taken.

---

## _collect_asset_files(folder_path: str) → List[str]

Internal helper. Scans a folder for supported asset file types and returns a deduplicated list (one per base name, using priority rules).

* **Parameters**

  * `folder_path` – Directory to scan for asset files.

* **Returns**

  * List of absolute file paths (one per logical asset).

* **Raises**

  * `FileNotFoundError` if the folder does not exist.

---

## batch_import_and_cleanup(
    folder_path: Optional[str],
    center_on_import: bool = False,
    scale_factor: float = 1.0,
    progress_callback: Optional[Callable[[int], None]] = None
) → None

Main entry point: imports assets, performs cleanup, naming, path repair, and namespace merging.

* **Parameters**

  * `folder_path` – Path to asset directory. If `None`, defaults to `../test_assets`.
  * `center_on_import` – If True, centers imported assets at world origin.
  * `scale_factor` – Uniform scale applied to imported assets.
  * `progress_callback` – Optional callback to report progress percentage (0–100).

* **Behavior**

  1. Loads the USD plugin if needed.
  2. Imports each supported asset file (`.fbx`, `.ma`, `.usd`, `.mb`, etc.).
  3. Centers and scales imported assets if requested.
  4. Deletes empty transform nodes.
  5. Renames imported nodes with collision-resilient naming using the current prefix.
  6. Calls `fix_missing_paths()` if path repair is enabled.
  7. Merges and removes namespaces.
  8. Calls `cmds.refresh()` at the end.
  9. Reports progress via `progress_callback`.

* **Raises**

  * `FileNotFoundError` if the folder does not exist.

---

# UI Behavior (in `pipeline_ui`)

## Help Button

* Shows an informational dialog with detailed usage instructions to assist artists.

## Progress Bar

* Connected to the batch import function via a callback.
* Updates dynamically during import to reflect completion percentage.

## Naming Prefix Control

* Checkbox to enable/disable automatic renaming.
* Text input for artist-customized prefix applied during renaming.

## Scale Slider

* Allows artists to scale selected Maya nodes interactively.
* Range: 50% to 150%, default at 100%.
* Resets to 100% on selection change.

## Export Selection to USD

* Exports current selection to a USD or USDA file.
* Uses Maya’s `usdExport` command if available, otherwise falls back on `file` export.
* Logs success or failure messages.

## USD Layers & Variant Browser

* Lists USD reference layers and variant sets from referenced USD files.
* Double-clicking a variant switches the USD stage variant selection accordingly.
* Refreshes references after variant selection change.
* Enables variant-aware workflows directly within Maya.

---
