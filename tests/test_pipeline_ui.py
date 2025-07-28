import os
import sys
import types
import pytest

if os.environ.get("CI") or os.environ.get("NO_UI_TEST"):
    pytest.skip("Skipping UI tests in CI.", allow_module_level=True)

# 1) Fake Maya and its submodules
fake_maya = types.ModuleType("maya")
fake_cmds = types.ModuleType("maya.cmds")
fake_cmds.ls = lambda **k: []
fake_cmds.pluginInfo = lambda *a, **k: True
fake_cmds.file = lambda *a, **k: None
fake_cmds.namespaceInfo = lambda **k: []
fake_cmds.namespace = lambda **k: None
fake_cmds.loadPlugin = lambda *a, **k: None
fake_cmds.refresh = lambda : None
fake_cmds.filePathEditor = lambda **k: []
fake_cmds.objExists = lambda *a, **k: False
fake_cmds.delete = lambda *a, **k: None
fake_cmds.listRelatives = lambda *a, **k: []
fake_cmds.rename = lambda node, new: new
fake_cmds.referenceQuery = lambda *a, **k: False
fake_cmds.warning = lambda *a, **k: None
fake_openmaya = types.ModuleType("maya.OpenMayaUI")
fake_openmaya.MQtUtil = types.SimpleNamespace(mainWindow=lambda: 0)

sys.modules["maya"] = fake_maya
sys.modules["maya.cmds"] = fake_cmds
sys.modules["maya.OpenMayaUI"] = fake_openmaya
fake_maya.cmds = fake_cmds
fake_maya.OpenMayaUI = fake_openmaya

# 2) Fake pxr.Usd so pipeline_ui imports cleanly
fake_pxr = types.ModuleType("pxr")
fake_usd = types.ModuleType("pxr.Usd")
fake_usd.Stage = types.SimpleNamespace(Open=lambda path: None)
sys.modules["pxr"] = fake_pxr
sys.modules["pxr.Usd"] = fake_usd
fake_pxr.Usd = fake_usd

# 3) Stub wrapInstance
import shiboken2
shiboken2.wrapInstance = lambda ptr, cls: None

# 4) PySide2 is present
pytest.importorskip("PySide2")

# 5) Add src/ and ui/ to path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(ROOT, "ui"))
sys.path.insert(0, os.path.join(ROOT, "src"))

from PySide2 import QtWidgets
import import_cleanup_prototype
import pipeline_ui
from pipeline_ui import PipelineToolUI, show_pipeline_ui


def test_ui_components_exist(qapp, qtbot):
    ui = PipelineToolUI()
    qtbot.addWidget(ui)
    assert ui.load_rules_btn.text() == "Load Rules…"
    assert ui.preview_btn.text() == "Preview Renaming"
    assert ui.batch_repair_btn.text() == "Batch Path Repair"
    assert ui.export_btn.text() == "Export Selection to USD"
    assert ui.run_btn.text() == "Import & Clean"
    headers = [ui.preview_table.horizontalHeaderItem(i).text() for i in range(2)]
    assert headers == ["Original", "New Name"]


def test_preview_populates_table(qapp, qtbot, tmp_path, monkeypatch):
    fake = {"foo": "ASSET_foo", "bar": "ASSET_bar"}
    monkeypatch.setattr(import_cleanup_prototype, "preview_renaming", lambda f: fake)
    ui = PipelineToolUI(); qtbot.addWidget(ui)
    ui.dir_line.setText(str(tmp_path))
    ui.on_preview()
    assert ui.preview_table.rowCount() == 2
    for row,(o,n) in enumerate(fake.items()):
        assert ui.preview_table.item(row,0).text() == o
        assert ui.preview_table.item(row,1).text() == n


def test_batch_repair_logs_and_calls(qapp, qtbot, monkeypatch):
    called = []
    monkeypatch.setattr(import_cleanup_prototype, "fix_missing_paths", lambda: called.append(True))
    ui = PipelineToolUI(); qtbot.addWidget(ui)
    ui.on_batch_repair()
    text = ui.log_output.toPlainText()
    assert "Batch Path Repair" in text
    assert called


def test_on_run_invokes_pipeline(qapp, qtbot, monkeypatch):
    calls = []
    monkeypatch.setattr(import_cleanup_prototype, "batch_import_and_cleanup", lambda folder: calls.append(folder))
    ui = PipelineToolUI(); qtbot.addWidget(ui)
    target = "/fake/assets"
    ui.dir_line.setText(target)
    ui.radio_nodes.setChecked(True)
    ui.naming_cb.setChecked(True)
    ui.path_cb.setChecked(True)
    ui.ns_cb.setChecked(False)
    ui.on_run()
    assert calls == [target]


def test_show_pipeline_ui_shows_window(qapp, qtbot):
    show_pipeline_ui()
    from pipeline_ui import _pipeline_tool
    assert isinstance(_pipeline_tool, PipelineToolUI)
    assert _pipeline_tool.isVisible()
