import os
import sys
import types
import importlib
import pytest

from PySide2 import QtWidgets

# Add ui/ and src/ to sys.path
ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UI_DIR  = os.path.join(ROOT, 'ui')
SRC_DIR = os.path.join(ROOT, 'src')
for p in (UI_DIR, SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Stub out maya modules
maya_mod      = types.ModuleType('maya')
maya_cmds     = types.ModuleType('maya.cmds')
maya_mui      = types.ModuleType('maya.OpenMayaUI')

def _noop(*args, **kwargs): return []

for name in (
    'ls','pluginInfo','file','listRelatives','delete',
    'objExists','rename','filePathEditor','namespaceInfo',
    'namespace','loadPlugin','refresh','warning'
):
    setattr(maya_cmds, name, _noop)

maya_mui.MQtUtil = types.SimpleNamespace(mainWindow=lambda: 0)

sys.modules['maya']            = maya_mod
sys.modules['maya.cmds']       = maya_cmds
sys.modules['maya.OpenMayaUI'] = maya_mui
setattr(maya_mod, 'cmds', maya_cmds)
setattr(maya_mod, 'OpenMayaUI', maya_mui)

import pipeline_ui

# Fake USD classes for testing
class FakeVariantSet:
    def __init__(self):
        self._names = ["high", "low"]
        self._sel   = "low"
    def GetNames(self):             return self._names
    def GetVariantNames(self):     return self._names
    def GetVariantSelection(self): return self._sel
    def SetVariantSelection(self, v): self._sel = v

class FakePrim:
    def __init__(self):
        self._path = "/MyPrim"
        self._vs   = FakeVariantSet()
    def GetPath(self):               return types.SimpleNamespace(pathString=self._path)
    def GetVariantSets(self):
        return types.SimpleNamespace(
            GetNames=lambda: self._vs.GetNames(),
            GetVariantSet=lambda name: self._vs
        )

class FakeStage:
    def __init__(self):
        self.layers = [types.SimpleNamespace(identifier="Layer0")]
        self.prims  = [FakePrim()]
        self.saved  = False
    def GetLayerStack(self):         return self.layers
    def Traverse(self):              return iter(self.prims)
    def GetPrimAtPath(self, path):   return self.prims[0]
    def GetRootLayer(self):          return self
    def Save(self):                  self.saved = True

@pytest.fixture(autouse=True)
def patch_usd(monkeypatch):
    fake_usd = types.SimpleNamespace(Stage=types.SimpleNamespace())
    stage    = FakeStage()
    fake_usd.Stage.Open = lambda path: stage
    monkeypatch.setattr(pipeline_ui, 'Usd', fake_usd)
    yield

@pytest.fixture
def ui_app(qtbot):
    win = pipeline_ui.PipelineToolUI()
    qtbot.addWidget(win)
    return win

def test_populate_usd_tree_shows_layer_and_prim(ui_app):
    ui_app.current_usd = "dummy.usda"
    ui_app.populate_usd_tree("dummy.usda")

    kinds = {
        ui_app.usd_tree.topLevelItem(i).text(1)
        for i in range(ui_app.usd_tree.topLevelItemCount())
    }
    assert "Layer" in kinds
    assert "Prim"  in kinds

def test_variants_listed_and_selection(ui_app):
    ui_app.current_usd = "dummy.usda"
    ui_app.populate_usd_tree("dummy.usda")

    prim_item = next(
        ui_app.usd_tree.topLevelItem(i)
        for i in range(ui_app.usd_tree.topLevelItemCount())
        if ui_app.usd_tree.topLevelItem(i).text(1) == "Prim"
    )

    vs_item = next(
        prim_item.child(j)
        for j in range(prim_item.childCount())
        if prim_item.child(j).text(1) == "VariantSet"
    )

    sel = vs_item.text(2)
    assert sel in ("high", "low")

def test_on_variant_activate_changes_selection(ui_app):
    ui_app.current_usd = "dummy.usda"
    ui_app.populate_usd_tree("dummy.usda")

    prim_item = next(
        ui_app.usd_tree.topLevelItem(i)
        for i in range(ui_app.usd_tree.topLevelItemCount())
        if ui_app.usd_tree.topLevelItem(i).text(1) == "Prim"
    )
    vs_item  = next(
        prim_item.child(j)
        for j in range(prim_item.childCount())
        if prim_item.child(j).text(1) == "VariantSet"
    )
    high_leaf = next(
        vs_item.child(k)
        for k in range(vs_item.childCount())
        if vs_item.child(k).text(0) == "high"
    )

    # Call public method, must exist now
    ui_app.on_variant_activate(high_leaf, 0)

    stage = pipeline_ui.Usd.Stage.Open(ui_app.current_usd)
    assert stage.saved

    # UI should update selection text
    ui_app.populate_usd_tree("dummy.usda")
    prim_item = next(
        ui_app.usd_tree.topLevelItem(i)
        for i in range(ui_app.usd_tree.topLevelItemCount())
        if ui_app.usd_tree.topLevelItem(i).text(1) == "Prim"
    )
    vs_item  = next(
        prim_item.child(j)
        for j in range(prim_item.childCount())
        if prim_item.child(j).text(1) == "VariantSet"
    )
    assert vs_item.text(2) == "high"
