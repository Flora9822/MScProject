import os
import json
import pytest
import import_cleanup_prototype as icp
from unittest.mock import patch, MagicMock

def test_reload_rules_file_not_found():
    # Test reload_rules raises FileNotFoundError when file is missing
    with pytest.raises(FileNotFoundError):
        icp.reload_rules("/nonexistent/path.json")

def test_reload_rules_invalid_json(tmp_path):
    # Test reload_rules raises JSONDecodeError on invalid JSON
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{ invalid json }")
    with pytest.raises(json.JSONDecodeError):
        icp.reload_rules(str(bad_file))

def test_collect_asset_files_no_valid_extensions(tmp_path):
    # Test _collect_asset_files returns empty list if no matching extensions
    d = tmp_path / "empty"
    d.mkdir()
    (d / "file.txt").write_text("test")
    files = icp._collect_asset_files(str(d))
    assert files == []

def test_get_unique_asset_name_increment(monkeypatch):
    # Test get_unique_asset_name increments suffix properly
    called_names = []
    def fake_objExists(name):
        called_names.append(name)
        return name in ("ASSET_test", "ASSET_test_001")
    monkeypatch.setattr(icp.cmds, "objExists", fake_objExists)
    name = icp.get_unique_asset_name("test", prefix="ASSET_")
    assert name == "ASSET_test_002"
    assert called_names[-1] == "ASSET_test_002"

def test_preview_renaming_folder_not_exist():
    # Test preview_renaming raises FileNotFoundError for invalid folder
    with pytest.raises(FileNotFoundError):
        icp.preview_renaming("/invalid/path")

def test_fix_missing_paths_handles_exception(monkeypatch):
    # Test fix_missing_paths catches exceptions gracefully
    def raise_exc(*args, **kwargs):
        raise RuntimeError("simulated failure")
    monkeypatch.setattr(icp.cmds, "filePathEditor", raise_exc)
    icp.fix_missing_paths()  # Should not raise, just print error

def test_batch_import_usd_skipped(monkeypatch, tmp_path):
    # Test batch_import_and_cleanup skips USD files if flags set to False
    d = tmp_path
    (d / "file.usd").write_text("")
    monkeypatch.setattr(icp.cmds, "file", lambda *a, **k: [])
    monkeypatch.setattr(icp.cmds, "objectType", lambda n: "transform")
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda n, **k: [])
    monkeypatch.setattr(icp.cmds, "rename", lambda old, new: new)
    monkeypatch.setattr(icp.cmds, "objExists", lambda name: False)
    icp.USD_IMPORT_AS_REF = False
    icp.USD_IMPORT_AS_NODES = False
    icp.batch_import_and_cleanup(str(d))

def test_batch_import_center_and_scale_exceptions(monkeypatch, tmp_path):
    # Test exceptions during center and scale operations are caught
    d = tmp_path
    (d / "file.ma").write_text("")
    monkeypatch.setattr(icp.cmds, "file", lambda *a, **k: ["node"])
    monkeypatch.setattr(icp.cmds, "objectType", lambda n: "transform")
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda n, **k: [])
    monkeypatch.setattr(icp.cmds, "xform", lambda *a, **k: (_ for _ in ()).throw(Exception("xform failed")))
    monkeypatch.setattr(icp.cmds, "getAttr", lambda attr: 1.0)
    monkeypatch.setattr(icp.cmds, "setAttr", lambda *a, **k: (_ for _ in ()).throw(Exception("setAttr failed")))
    monkeypatch.setattr(icp.cmds, "rename", lambda old, new: new)
    monkeypatch.setattr(icp.cmds, "objExists", lambda name: False)
    icp.batch_import_and_cleanup(str(d), center_on_import=True, scale_factor=2.0)

def test_batch_import_rename_exception(monkeypatch, tmp_path):
    # Test batch_import_and_cleanup handles rename exceptions gracefully
    d = tmp_path
    (d / "file.ma").write_text("")
    monkeypatch.setattr(icp.cmds, "file", lambda *a, **k: ["node"])
    monkeypatch.setattr(icp.cmds, "objectType", lambda n: "transform")
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda n, **k: [])
    monkeypatch.setattr(icp.cmds, "rename", lambda old, new: (_ for _ in ()).throw(Exception("rename failed")))
    monkeypatch.setattr(icp.cmds, "objExists", lambda name: False)
    icp.batch_import_and_cleanup(str(d))

def test_batch_import_delete_empty_groups_exception(monkeypatch):
    # Test delete empty group failure does not crash the import
    monkeypatch.setattr(icp.cmds, "ls", lambda **k: ["emptyGroup"])
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda n, **k: [])
    monkeypatch.setattr(icp.cmds, "delete", lambda n: (_ for _ in ()).throw(Exception("delete failed")))
    icp.batch_import_and_cleanup()

def test_batch_import_namespace_cleanup_exception(monkeypatch):
    # Test namespace cleanup failure is handled gracefully
    monkeypatch.setattr(icp.cmds, "namespaceInfo", lambda **k: ["badNamespace"])
    monkeypatch.setattr(icp.cmds, "namespace", lambda **k: (_ for _ in ()).throw(Exception("namespace cleanup failed")))
    icp.batch_import_and_cleanup()
