import sys
import os
import importlib
import maya.utils

try:
    project_root = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ is not defined, fallback
    project_root = "/home/s5722414/Documents/MScProject"  

src_dir = os.path.join(project_root, "src")
ui_dir = os.path.join(project_root, "ui")

for path in (src_dir, ui_dir):
    if path not in sys.path:
        sys.path.append(path)

import import_cleanup_prototype
import pipeline_ui
importlib.reload(import_cleanup_prototype)
importlib.reload(pipeline_ui)

# Launch the tool deferred
maya.utils.executeDeferred(lambda: pipeline_ui.show_pipeline_ui())
