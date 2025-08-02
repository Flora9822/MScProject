
[![Coverage Status](https://img.shields.io/badge/coverage-83%25-green)]


# Asset Import and Preparation Pipeline Tool for Maya

A streamlined pipeline tool designed for Autodesk Maya to batch import, clean up, and manage 3D assets efficiently. Supports USD workflows, customizable naming conventions, namespace cleanup, variant browsing, progress feedback, and collision-safe numbering.

---

## Features

- **Batch Import**: Supports `.fbx`, `.obj`, `.ma`, `.mb`, `.usd`, `.usda`, `.abc`
- **USD Import Modes**: Import as Reference or as Nodes
- **Preview Renaming**: Visualize sanitized and collision-safe names before applying
- **Custom Naming Prefix**: Artists can define custom prefixes for imported assets
- **Progress Bar**: Real-time progress during batch operations
- **Interactive Scale Slider**: Scale selected objects between 50% and 150% interactively
- **Batch Path Repair**: One-click fix for missing file paths (textures, references)
- **Empty Group Cleanup**: Deletes empty transform nodes
- **Namespace Cleanup**: Merges and removes all non-UI namespaces
- **Viewport Refresh**: Ensures scene updates post-processing
- **Export Selection to USD**: Save selected objects as USD files
- **USD Layer & Variant Browser**: Browse and select USD variants (experimental)
- **Help Button**: Provides contextual help for UI features and workflow

---

## Requirements

- Autodesk Maya 2022 or newer (with USD support)
- Enabled `mayaUsdPlugin`
- Python 3.9+ (bundled with Maya)
- PySide2 (bundled with Maya)
- USD Python API (`pxr.Usd`, included in MayaUSD)

---

## Installation

1. Clone or copy this repository into your Maya scripts directory, e.g.:

```

\~/Documents/MScProject/
├── src/import\_cleanup\_prototype.py
├── src/rules/pipeline\_rules.json
└── ui/pipeline\_ui.py

```

2. Create a `test_assets/` folder alongside for test models:

```

\~/Documents/MScProject/test\_assets/

````

3. Confirm `pipeline_rules.json` is present in `src/rules/`.

---

## Quick Start

1. Launch Maya.

2. Open the Script Editor → Python tab.

3. Paste and run:

```python
import sys, importlib

paths = [
    "/home/you/Documents/MScProject/src",
    "/home/you/Documents/MScProject/ui"
]
for p in paths:
    if p not in sys.path:
        sys.path.append(p)

import import_cleanup_prototype, pipeline_ui
importlib.reload(import_cleanup_prototype)
importlib.reload(pipeline_ui)

pipeline_ui.show_pipeline_ui()
````

4. The **Asset Import & Prep Tool** UI will appear.

---

## Typical Workflow

1. Optionally reload or modify pipeline rules (`pipeline_rules.json`).

2. Click **Browse...** and select your asset folder.

3. Preview sanitized and collision-safe asset names.

4. Enable/disable options:

   * Naming prefix toggle and input
   * Path repair toggle
   * Namespace cleanup toggle

5. Use **Batch Path Repair** to fix broken paths independently.

6. Select USD import mode (*Reference* or *Nodes*).

7. Adjust scale slider for interactive scaling.

8. Choose **Center on Import** to move assets to world origin.

9. Click **Import & Clean** to process assets, with live progress.

10. Browse USD layers and variants if using referenced USD.

11. Export selected objects to USD using the export button.

12. Click **? Help** for UI guidance anytime.

---

## Architecture Diagram

![Architecture Diagram](docs/architecture_diagram.png)
*Visualizes key components and data flow.*

---

## Known Limitations & FAQ

* Collision-safe naming affects Maya scene nodes only, not file names on disk.
* Referenced USD nodes are read-only (cannot rename/delete).
* If UI fails to load, verify `sys.path` and Python tab in Maya.
* Run **Batch Path Repair** anytime to resolve missing file references.

---

## Example: Generate Test USD with Variants

```python
import os
from pxr import Usd, UsdGeom

usd_path = "/home/you/Documents/MScProject/test_assets/variants_test_demo.usda"
if os.path.exists(usd_path):
    os.remove(usd_path)

stage = Usd.Stage.CreateNew(usd_path)
cube = UsdGeom.Cube.Define(stage, "/Cube")
vset = cube.GetPrim().GetVariantSets().AddVariantSet("LOD")
vset.AddVariant("high")
vset.AddVariant("low")
vset.SetVariantSelection("high")
stage.GetRootLayer().Save()

print("Created test USD with variants at:", usd_path)
```

---


