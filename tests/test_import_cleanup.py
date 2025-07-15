import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
import import_cleanup_prototype

# 1. Test rules reload
def test_reload_rules():
    rules_path = os.path.join(os.path.dirname(__file__), '../src/rules/pipeline_rules.json')
    import_cleanup_prototype.reload_rules(rules_path)
    assert 'naming' in import_cleanup_prototype.pipeline_rules

# 2. Test preview renaming
def test_preview_renaming(tmp_path):
    # Setup: create dummy assets
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    for name in ["cube.ma", "sphere.obj", "cone.usd"]:
        (asset_dir / name).touch()
    preview = import_cleanup_prototype.preview_renaming(str(asset_dir))
    assert "cube" in preview and preview["cube"].startswith("ASSET_")
    assert "sphere" in preview and preview["sphere"].startswith("ASSET_")
    assert "cone" in preview and preview["cone"].startswith("ASSET_")

# 3. Test _collect_asset_files 
def test_collect_asset_files(tmp_path):
    asset_dir = tmp_path / "col"
    asset_dir.mkdir()
    for name in ["foo.ma", "bar.mb", "foo.usd"]: 
        (asset_dir / name).touch()
    files = import_cleanup_prototype._collect_asset_files(str(asset_dir))
    assert len(files) == 2 

# 4. Test batch_import_and_cleanup can run without error (mock Maya cmds)
def test_batch_import_and_cleanup(monkeypatch, tmp_path):
    # Monkeypatch maya.cmds functions for headless test
    monkeypatch.setattr(import_cleanup_prototype, "cmds", DummyCmds())
    asset_dir = tmp_path / "many"
    asset_dir.mkdir()
    for name in ["a.ma", "b.mb", "c.obj"]:
        (asset_dir / name).touch()
    # Should not raise error (this test is just for logic flow)
    import_cleanup_prototype.batch_import_and_cleanup(str(asset_dir))

# DummyCmds: for CI/headless test, can mock as needed
class DummyCmds:
    def ls(self, **kwargs): return ["node1", "node2"]
    def pluginInfo(self, *args, **kwargs): return True
    def file(self, *args, **kwargs): pass
    def listRelatives(self, *args, **kwargs): return []
    def delete(self, *args, **kwargs): pass
    def objExists(self, *args, **kwargs): return True
    def rename(self, node, new): return new
    def filePathEditor(self, *args, **kwargs): return []
    def namespaceInfo(self, **kwargs): return []
    def namespace(self, **kwargs): pass
    def referenceQuery(self, node, **kwargs): return False

# 5. Test edge case: empty dir
def test_preview_empty(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    preview = import_cleanup_prototype.preview_renaming(str(empty))
    assert preview == {}

