import sys
import os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if root not in sys.path:
    sys.path.insert(0, root)

import import_cleanup_prototype 

import pytest

@pytest.fixture(autouse=True)
def patch_pipeline_rules():
    import_cleanup_prototype.pipeline_rules = {
        "naming": {
            "prefix": "ASSET_",
            "sanitizePattern": "[^a-zA-Z0-9_]"
        },
        "pathRepair": {
            "autoFix": True
        },
        "cleanup": {
            "deleteEmptyGroups": True,
            "namespaceCleanup": True
        }
    }
