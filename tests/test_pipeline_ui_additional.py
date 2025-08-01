import pytest
from unittest.mock import patch, MagicMock
import pipeline_ui as pui

def test_ui_method_wrappers_call(qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    with patch.object(ui, "_on_preview") as mock_preview, \
         patch.object(ui, "_on_batch_repair") as mock_batch, \
         patch.object(ui, "_on_run") as mock_run, \
         patch.object(ui, "_on_variant_activate") as mock_variant:

        ui.on_preview()
        mock_preview.assert_called_once()

        ui.on_batch_repair()
        mock_batch.assert_called_once()

        ui.on_run()
        mock_run.assert_called_once()

        ui.on_variant_activate(None)
        mock_variant.assert_called_once()

def test_scale_slider_no_selection(monkeypatch, qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    monkeypatch.setattr(pui.cmds, "ls", lambda **kwargs: [])
    with patch("builtins.print") as mock_print:
        ui._on_scale_slider_changed(100)
        mock_print.assert_called_with("No object selected for scaling.")

def test_on_selection_changed_resets_slider(qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    ui.scale_slider.setValue(50)
    ui._on_selection_changed()
    assert ui.scale_slider.value() == 100

def test_preview_with_invalid_path(monkeypatch, qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    monkeypatch.setattr(pui.import_cleanup_prototype, "preview_renaming", lambda path=None: (_ for _ in ()).throw(Exception("fail")))
    with patch("PySide2.QtWidgets.QMessageBox.critical") as mock_msg:
        ui._on_preview()
        mock_msg.assert_called_once()

def test_batch_repair_logs_call(monkeypatch, qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    called = []
    monkeypatch.setattr(pui.import_cleanup_prototype, "fix_missing_paths", lambda: called.append(True))
    ui._on_batch_repair()
    assert ">>> Running Batch Path Repair…" in ui.log_output.toPlainText()
    assert called

def test_usd_export_no_selection(monkeypatch, qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    monkeypatch.setattr(pui.cmds, "ls", lambda **kwargs: [])
    with patch("PySide2.QtWidgets.QMessageBox.warning") as mock_warning:
        ui._on_usd_export()
        mock_warning.assert_called_once()

def test_usd_export_fail(monkeypatch, qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    monkeypatch.setattr(pui.cmds, "ls", lambda **kwargs: ["node"])
    monkeypatch.setattr(pui.QtWidgets.QFileDialog, "getSaveFileName", lambda *a, **k: ("fakepath.usd", None))
    # Add dummy usdExport to avoid AttributeError, simulate failure by raising Exception
    setattr(pui.cmds, "usdExport", lambda *args, **kwargs: (_ for _ in ()).throw(Exception("fail export")))
    monkeypatch.setattr(pui.cmds, "file", lambda *a, **k: (_ for _ in ()).throw(Exception("fail export")))
    ui._on_usd_export()
    assert "Export failed" in ui.log_output.toPlainText()

def test_on_variant_activate_handles_non_variant(qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    item = MagicMock()
    item.text.side_effect = lambda idx: "Prim" if idx == 1 else ""
    ui._on_variant_activate(item, None)

def test_show_pipeline_ui_opens_window(qtbot):
    pui.show_pipeline_ui()
    from pipeline_ui import _pipeline_tool
    assert _pipeline_tool.isVisible()

def test_help_dialog_shows(qtbot):
    ui = pui.PipelineToolUI()
    qtbot.addWidget(ui)
    with patch("PySide2.QtWidgets.QMessageBox.information") as mock_info:
        ui._on_help()
        mock_info.assert_called_once()
