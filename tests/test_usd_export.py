import pytest

try:
    import maya.standalone
    from maya import cmds
    from pxr import Usd
except ImportError:
    pytest.skip("maya.standalone not available—skipping USD export tests", allow_module_level=True)

def setup_module(module):
    maya.standalone.initialize(name='python')

def teardown_module(module):
    maya.standalone.uninitialize()

def test_export_and_load(tmp_path):
    cmds.file(new=True, force=True)
    cube   = cmds.polyCube(name='TestCube')[0]
    sphere = cmds.polySphere(name='TestSphere')[0]
    cmds.select([cube, sphere], replace=True)

    out_file = tmp_path / "export_test.usda"
    cmds.usdExport(file=str(out_file), selection=[cube, sphere])
    assert out_file.exists()

    stage = Usd.Stage.Open(str(out_file))
    assert stage
    prims = [p for p in stage.Traverse() if p.IsValid()]
    assert len(prims) >= 2
