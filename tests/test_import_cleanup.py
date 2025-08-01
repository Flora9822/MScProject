import os
import json
import pytest
import import_cleanup_prototype

# 1. Test rules reload
def test_reload_rules():
    rules_path = os.path.join(
        os.path.dirname(__file__),
        '../src/rules/pipeline_rules.json'
    )
    import_cleanup_prototype.reload_rules(rules_path)
    assert 'naming' in import_cleanup_prototype.pipeline_rules

# 2. Test preview renaming basic
def test_preview_renaming(tmp_path):
    # Setup: create dummy assets
    asset_dir = tmp_path / "assets"
    asset_dir.mkdir()
    for name in ["cube.ma", "sphere.obj", "cone.usd"]:
        (asset_dir / name).touch()

    preview = import_cleanup_prototype.preview_renaming(str(asset_dir))
    # Keys should be base names without extensions
    assert set(preview.keys()) == {"cube", "sphere", "cone"}
    # Values should start with prefix from pipeline_rules.json
    prefix = import_cleanup_prototype.pipeline_rules['naming']['prefix']
    for v in preview.values():
        assert v.startswith(prefix)

# 3. Test _collect_asset_files deduplication
def test_collect_asset_files(tmp_path):
    """
    _collect_asset_files should dedupe by base name and return full paths.
    """
    asset_dir = tmp_path / "col"
    asset_dir.mkdir()
    # foo.ma and foo.usd share base "foo"
    for name in ["foo.ma", "bar.mb", "foo.usd"]:
        (asset_dir / name).touch()

    files = import_cleanup_prototype._collect_asset_files(str(asset_dir))
    bases = set(os.path.splitext(os.path.basename(f))[0] for f in files)
    assert bases == {"foo", "bar"}
    assert len(files) == 2

# 4. Test preview renaming for various extensions
def test_preview_renaming_various(tmp_path):
    asset_dir = tmp_path / "preview"
    asset_dir.mkdir()
    for name in ["alpha.ma", "beta.mb", "gamma.obj"]:
        (asset_dir / name).touch()

    mapping = import_cleanup_prototype.preview_renaming(str(asset_dir))
    assert set(mapping.keys()) == {"alpha", "beta", "gamma"}
    prefix = import_cleanup_prototype.pipeline_rules['naming']['prefix']
    for newname in mapping.values():
        assert newname.startswith(prefix)

# --- Boundary & Exception Tests ---

def test_collect_asset_files_nonexistent(tmp_path):
    """
    _collect_asset_files should raise FileNotFoundError for a missing folder.
    """
    bad = str(tmp_path / "no_such_dir")
    with pytest.raises(FileNotFoundError) as exc:
        import_cleanup_prototype._collect_asset_files(bad)
    assert "Asset folder not found" in str(exc.value)

def test_preview_renaming_nonexistent():
    """
    preview_renaming should raise FileNotFoundError when folder does not exist.
    """
    bad = "/unlikely/to/exist/12345"
    with pytest.raises(FileNotFoundError) as exc:
        import_cleanup_prototype.preview_renaming(bad)
    assert "Preview folder not found" in str(exc.value)

def test_batch_import_nonexistent():
    """
    batch_import_and_cleanup should raise FileNotFoundError for a missing import folder.
    """
    bad = "/still/does/not/exist"
    with pytest.raises(FileNotFoundError) as exc:
        import_cleanup_prototype.batch_import_and_cleanup(bad)
    assert "Import folder not found" in str(exc.value)

def test_reload_rules_invalid_json(tmp_path):
    """
    reload_rules should raise JSONDecodeError when the rules file is malformed.
    """
    bad_file = tmp_path / "bad_rules.json"
    bad_file.write_text("{ invalid json,,, }")
    with pytest.raises(json.JSONDecodeError):
        import_cleanup_prototype.reload_rules(str(bad_file))
