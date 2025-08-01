import os
import tempfile
import pytest
import import_cleanup_prototype as icp
from unittest.mock import patch

def test_reload_rules(tmp_path):
    file = tmp_path / "rules.json"
    file.write_text('{"naming": {"prefix": "T_", "sanitizePattern": "[^a-zA-Z0-9_]"}, "cleanup": {}, "pathRepair": {}}')
    icp.reload_rules(str(file))
    assert icp.pipeline_rules['naming']['prefix'] == "T_"

def test_collect_asset_files_pytest_mode(monkeypatch, tmp_path):
    filenames = ["foo.ma", "foo.mb", "foo.usda", "bar.fbx", "baz.txt"]
    for f in filenames:
        (tmp_path / f).write_text("test")
    monkeypatch.setattr("sys.modules", {"pytest": True})
    result = icp._collect_asset_files(str(tmp_path))
    assert any(f.endswith(".ma") for f in result)
    assert all(f.endswith(('.ma','.mb','.usd','.usda','.obj','.fbx','.abc')) for f in result)

def test_get_unique_asset_name(monkeypatch):
    monkeypatch.setattr(icp.cmds, "objExists", lambda name: name in ("ASSET_foo", "ASSET_foo_001", "ASSET_foo_002"))
    name = icp.get_unique_asset_name("foo", prefix="ASSET_")
    assert name == "ASSET_foo_003"

def test_preview_renaming_exception():
    with pytest.raises(FileNotFoundError):
        icp.preview_renaming(folder_path="/nonexistent/path")

def test_fix_missing_paths_exception(monkeypatch):
    def raise_exc(*a, **k): raise RuntimeError("fail")
    monkeypatch.setattr(icp.cmds, "filePathEditor", raise_exc)
    icp.fix_missing_paths()  # catch and print error

def test_batch_import_and_cleanup_edge_cases(monkeypatch, tmp_path):
    # Test nonexistent folder raises error
    with pytest.raises(FileNotFoundError):
        icp.batch_import_and_cleanup("/nonexistent/path")

    test_file = tmp_path / "test.ma"
    test_file.write_text("")

    monkeypatch.setattr(icp, "_collect_asset_files", lambda folder: [str(test_file)])

    # Simulate file import exception
    monkeypatch.setattr(icp.cmds, "file", lambda fp, **kwargs: (_ for _ in ()).throw(Exception("fail import")))
    icp.batch_import_and_cleanup(str(tmp_path))

    # Simulate rename failure
    monkeypatch.setattr(icp.cmds, "file", lambda fp, **kwargs: ["node1"])
    monkeypatch.setattr(icp.cmds, "objectType", lambda name: "transform")
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda node, **kwargs: [])
    monkeypatch.setattr(icp.cmds, "rename", lambda old, new: (_ for _ in ()).throw(Exception("fail rename")))
    monkeypatch.setattr(icp.cmds, "objExists", lambda name: False)
    icp.batch_import_and_cleanup(str(tmp_path))

    # Simulate delete failure on empty groups
    monkeypatch.setattr(icp.cmds, "ls", lambda **kwargs: ["empty_group"])
    monkeypatch.setattr(icp.cmds, "listRelatives", lambda node, **kwargs: [])
    monkeypatch.setattr(icp.cmds, "delete", lambda node: (_ for _ in ()).throw(Exception("fail delete")))
    icp.batch_import_and_cleanup(str(tmp_path))

    # Simulate namespace cleanup failure
    monkeypatch.setattr(icp.cmds, "namespaceInfo", lambda **kwargs: ["bad_ns"])
    monkeypatch.setattr(icp.cmds, "namespace", lambda **kwargs: (_ for _ in ()).throw(Exception("fail ns")))
    icp.batch_import_and_cleanup(str(tmp_path))
