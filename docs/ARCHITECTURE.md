# System Architecture

This document describes the high-level architecture and data flow of the Asset Import & Prep Tool.

## Overview

The tool is structured into three main layers:

![Architecture Diagram](docs/architecture_diagram.png)

*Figure 1: High-level dataflow between UI, Core Engine, Maya API, Rules File, and Assets.*

## Components

### 1. User Interface (UI)

* **Location**: `src/ui/pipeline_ui.py`
* **Technology**: PySide2
* **Responsibilities**:

  * Load and display rules file path.
  * Allow selection of asset folder.
  * Toggle import/cleanup options.
  * Trigger preview and import/cleanup actions.
  * Display progress and logs.
  * Visualize USD layers & variants.

### 2. Controller

* **Location**: `src/ui/pipeline_ui.py`
* **Role**: Glue between UI and Core Engine.
* **Key Methods**:

  * `show_pipeline_ui()`: Launch the dialog.
  * `on_preview()`: Calls `preview_renaming()`.
  * `on_run()`: Applies flags, clears scene, calls `batch_import_and_cleanup()`.
  * `populate_usd_tree()`: Uses `pxr.Usd` to build variant tree.

### 3. Core Engine

* **Location**: `src/import_cleanup_prototype.py`
* **Responsibilities**:

  * Read and reload pipeline rules from JSON.
  * Collect asset files with `_collect_asset_files()`.
  * Preview renaming with `preview_renaming()`.
  * Execute batch import and cleanup with `batch_import_and_cleanup()`.
  * Handle all Maya API calls (`cmds.file`, `cmds.delete`, `cmds.rename`, etc.).

### 4. Maya Python API

* **Module**: `maya.cmds`
* **Used For**:

  * Importing assets in various formats.
  * Scene graph queries and modifications.
  * Path repair via `filePathEditor`.
  * Namespace operations.
  * Refreshing the viewport.

### 5. Rules File

* **Location**: `src/rules/pipeline_rules.json`
* **Format**: JSON, defines naming, cleanup, and path repair rules.

### 6. Assets Folder

* **Structure**:

  ```
  /test_assets
    ├── modelA.fbx
    ├── modelB.usd
    └── scene1.ma
  ```

## Deployment

* **Installation**: Copy `src/` into Maya’s scripts path, ensure JSON rules in `src/rules/`.
* **Dependencies**:

  * Maya 2022+ with `mayaUsdPlugin`.
  * Python 3.9 (for standalone tests).
  * PySide2.
  * USD (for variant tree visualization).

## Diagram Asset

The architecture diagram image is located at:

```
docs/architecture_diagram.png
```


