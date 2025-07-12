
# Asset Import & Prep Tool for Maya + USD

A simple pipeline tool for batch importing, cleanup, and management of 3D assets in Maya, with support for USD (Universal Scene Description) reference, namespace, and naming conventions.

---

## Features

* Batch import multiple assets (FBX, OBJ, MA, MB, USD, USDA, ABC)
* **USD Import**: as *reference* or *as nodes*
* Namespace and naming convention enforcement
* Automatic cleanup of empty groups and namespaces
* Path repair for broken asset references
* Quick export of selection to USD
* **USD Layer & Variant browser** (experimental, for inspection)

---

## Requirements

* **Autodesk Maya** 2022+ (with USD support)
* `mayaUsdPlugin` enabled
* Python 3 (built-in for Maya 2022+)
* [PySide2](https://wiki.qt.io/Qt_for_Python) (comes with Maya 2022+)
* [pxr.Usd](https://github.com/PixarAnimationStudios/USD) (Maya built-in)

---

## Installation

1. **Clone or copy the repository files** into your Maya scripts folder or your own project folder, e.g.:

   ```
   /home/<your-username>/Documents/MScProject/src/
   /home/<your-username>/Documents/MScProject/ui/
   ```

2. Place your **assets** (FBX, USD, etc) in a dedicated folder, e.g.:

   ```
   /home/<your-username>/Documents/MScProject/test_assets/
   ```

3. Make sure the following files are present:

   * `src/import_cleanup_prototype.py`
   * `ui/pipeline_ui.py`
   * `src/rules/pipeline_rules.json` (example rules)

---

## Usage

1. **Open Maya**

2. **Open the Script Editor** (`Windows > General Editors > Script Editor`) and switch to the **Python** tab.

3. **Paste and run** the following snippet to load and display the UI:

   ```python
   import sys, importlib
   for p in (
       "/home/<your-username>/Documents/MScProject/src",
       "/home/<your-username>/Documents/MScProject/ui"
   ):
       if p not in sys.path:
           sys.path.append(p)
   import import_cleanup_prototype, pipeline_ui
   importlib.reload(import_cleanup_prototype)
   importlib.reload(pipeline_ui)
   pipeline_ui.show_pipeline_ui()
   ```

   *(Replace `<your-username>` with your actual username or adjust the path as needed.)*

4. **The "Asset Import & Prep Tool" window will appear.**

---

## Typical Workflow

* **Set asset directory** with the *Browse…* button.
* Select USD import mode: *Import as Nodes* or *Import as Reference*.
* (Optionally) Enable/disable naming, path repair, and namespace cleanup.
* Click **Import & Clean** to import and process all assets in the chosen folder.
* (Optional) Check the "USD Layers & Variants" panel to browse referenced USD file structure.
* (Optional) Export current selection to USD using the "Export Selection to USD" button.

---

## Known Limitations / FAQ

* USD **variant switching** only affects the underlying USD reference; if geometry does not visually change, the USD file may not encode visible variant differences.
* "Cannot rename a read only node" and "Cannot delete ... as it has locked or read-only children" messages are normal for referenced USD data (cannot edit referenced nodes directly).
* Some imported USDs from Omniverse/Pixar may require external textures or internet access to fully load their assets.
* If the UI window does not appear, check the Script Editor for errors, make sure the paths are correct, and that your Maya has USD/PySide2 support.
* For custom pipeline rules, edit `src/rules/pipeline_rules.json` and reload rules from the UI.

---

## Example USD Variant Generation (for testing)

You can generate a simple USD file with variants for testing:

```python
import os
from pxr import Usd, UsdGeom

usd_path = "/home/<your-username>/Documents/MScProject/test_assets/variants_test_demo.usda"
if os.path.exists(usd_path):
    os.remove(usd_path)

stage = Usd.Stage.CreateNew(usd_path)
cube = UsdGeom.Cube.Define(stage, "/Cube")
vset = cube.GetPrim().GetVariantSets().AddVariantSet("LOD")
vset.AddVariant("high")
vset.AddVariant("low")
vset.SetVariantSelection("high")
stage.GetRootLayer().Save()
print(" Created test USD with variants at:", usd_path)
```

---

## License

MIT © 2025 Flora/MScProject.

