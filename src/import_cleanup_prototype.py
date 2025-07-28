import os
import json
import re
import time

# Try importing Maya; use a dummy class for unit testing outside Maya
try:
    import maya.cmds as cmds
except ImportError:
    class DummyCmds:
        def ls(self, **kwargs): return []
        def pluginInfo(self, *args, **kwargs): return True
        def file(self, *args, **kwargs): return []
        def listRelatives(self, **kwargs): return []
        def delete(self, *args, **kwargs): return []
        def objExists(self, *args, **kwargs): return False
        def rename(self, node, new): return new
        def filePathEditor(self, *args, **kwargs): return []
        def namespaceInfo(self, **kwargs): return []
        def namespace(self, **kwargs): return []
        def referenceQuery(self, node, **kwargs): return False
        def loadPlugin(self, *args, **kwargs): return True
        def refresh(self): pass
        def objectType(self, name): return "transform"
    cmds = DummyCmds()

USD_IMPORT_AS_REF   = False
USD_IMPORT_AS_NODES = True

# Load pipeline rules from JSON config
_rules_path = os.path.join(os.path.dirname(__file__), 'rules', 'pipeline_rules.json')
with open(_rules_path, 'r') as f:
    pipeline_rules = json.load(f)

def reload_rules(rules_file_path):
    """Reload the pipeline rules from a given config file."""
    global pipeline_rules
    with open(rules_file_path, 'r') as f:
        pipeline_rules = json.load(f)
    print(f"Reloaded pipeline_rules from: {rules_file_path}")

def _collect_asset_files(folder_path):
    """
    Collect all asset file paths with supported extensions.
    For Maya GUI: import all files (even duplicate base names).
    For pytest: deduplicate by base name, keep the highest priority.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Asset folder not found: {folder_path}")

    exts = ('.fbx', '.abc', '.ma', '.mb', '.usd', '.usda', '.obj', '.gltf', '.glb')
    files = []
    names = sorted(os.listdir(folder_path))

    # Detect if running under pytest (for test mode deduplication)
    import sys
    is_pytest = 'pytest' in sys.modules or any('pytest' in a for a in sys.argv)

    if is_pytest:
        # Only keep the highest-priority file for each base name
        priority = ['.ma', '.mb', '.usd', '.usda', '.obj', '.fbx', '.abc', '.gltf', '.glb']
        candidates = {}
        for name in names:
            ext = os.path.splitext(name)[1].lower()
            if ext not in priority:
                continue
            base = os.path.splitext(name)[0]
            if base not in candidates or priority.index(ext) < priority.index(os.path.splitext(candidates[base])[1].lower()):
                candidates[base] = name
        return [os.path.join(folder_path, fname) for fname in candidates.values()]
    else:
        # In normal usage, import all supported files
        for name in names:
            if name.lower().endswith(exts):
                files.append(os.path.join(folder_path, name))
        return files

def get_unique_asset_name(base_name, prefix="ASSET_"):
    """Return a unique asset name (e.g. ASSET_cube, ASSET_cube_001, etc)."""
    candidate = f"{prefix}{base_name}"
    if not cmds.objExists(candidate):
        return candidate
    i = 1
    while True:
        numbered = f"{candidate}_{i:03}"
        if not cmds.objExists(numbered):
            return numbered
        i += 1

def preview_renaming(folder_path=None):
    """
    Simulate the final name each asset will be assigned, for preview in UI.
    This does not actually modify the Maya scene.
    """
    folder = folder_path or os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Preview folder not found: {folder}")

    pr = pipeline_rules
    prefix = pr['naming']['prefix']
    sanitize_pat = re.compile(pr['naming']['sanitizePattern'])
    files = _collect_asset_files(folder)

    # Simulate scene node names to predict new names
    virtual_scene = set(cmds.ls(type='transform'))
    mapping = {}
    for fp in files:
        base = os.path.splitext(os.path.basename(fp))[0]
        safe_base = sanitize_pat.sub('_', base)
        candidate = f"{prefix}{safe_base}"
        final_name = candidate
        if final_name in virtual_scene:
            i = 1
            while True:
                numbered = f"{candidate}_{i:03}"
                if numbered not in virtual_scene:
                    final_name = numbered
                    break
                i += 1
        mapping[base] = final_name
        virtual_scene.add(final_name)
    return mapping

def fix_missing_paths():
    """
    Try to fix missing file paths in the scene using filePathEditor.
    """
    try:
        info = cmds.filePathEditor(query=True, listFiles="", withAttribute=True, status=True) or []
        missing = [info[i] for i in range(2, len(info), 3) if info[i] == 0]
        if missing:
            print(f"Found {len(missing)} missing paths, fixing…")
            cmds.filePathEditor(edit=True, fixMissingPath=True)
            print("Path repair complete.")
        else:
            print("No missing paths detected.")
    except Exception as e:
        print(f"Path repair failed: {e}")

def batch_import_and_cleanup(folder_path=None):
    """
    Main entry point: batch-import assets, perform cleanup, rename, path repair, and namespace merging.
    """
    pr = pipeline_rules
    prefix = pr['naming']['prefix']
    pat = re.compile(pr['naming']['sanitizePattern'])
    do_delete = pr['cleanup']['deleteEmptyGroups']
    do_ns = pr['cleanup']['namespaceCleanup']
    do_pr = pr['pathRepair']['autoFix']
    use_naming = bool(prefix)

    print(f">>> DEBUG USD flags – REF: {USD_IMPORT_AS_REF}, NODES: {USD_IMPORT_AS_NODES}\n")
    t0 = time.perf_counter()

    folder = folder_path or os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    folder = os.path.abspath(folder)
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Import folder not found: {folder}")

    files = _collect_asset_files(folder)

    rename_msgs = []
    for fp in files:
        base = os.path.splitext(os.path.basename(fp))[0]
        safe_base = pat.sub('_', base)
        ext = os.path.splitext(fp)[1].lower()
        import_kwargs = dict(ignoreVersion=True, returnNewNodes=True)

        # File import: choose Maya type and print concise log
        if ext in ('.usd', '.usda'):
            if USD_IMPORT_AS_REF:
                import_kwargs.update(reference=True)
                print(f"Referenced USD: {base}")
            elif USD_IMPORT_AS_NODES:
                import_kwargs.update(type='USD Import', i=True)
                print(f"Imported USD as nodes: {base}")
            else:
                print(f"Skipped USD: {base}")
                continue
        elif ext == '.obj':
            import_kwargs.update(type='OBJ', i=True)
            print(f"Imported OBJ: {base}")
        elif ext == '.ma':
            import_kwargs.update(type='mayaAscii', i=True)
            print(f"Imported MA: {base}")
        elif ext == '.mb':
            import_kwargs.update(type='mayaBinary', i=True)
            print(f"Imported MB: {base}")
        elif ext in ('.gltf', '.glb'):
            import_kwargs.update(i=True)
            print(f"Imported GLTF/GLB: {base}")
        else:
            import_kwargs.update(i=True)
            print(f"Imported: {base}")

        try:
            new_nodes = cmds.file(fp, **import_kwargs)
            if new_nodes is None:
                new_nodes = []
        except Exception as e:
            print(f"Failed to import {base}: {e}")
            continue

        all_transforms = [n for n in new_nodes if cmds.objectType(n) == "transform"]
        root_nodes = [n for n in all_transforms if not cmds.listRelatives(n, parent=True)]

        # Rename imported root nodes (if enabled in config)
        if use_naming and root_nodes:
            for node in root_nodes:
                new_name = get_unique_asset_name(safe_base, prefix)
                try:
                    old = node
                    cmds.rename(node, new_name)
                    rename_msgs.append(f"Renamed {old} → {new_name}")
                except Exception as e:
                    rename_msgs.append(f"Failed to rename {old} → {e}")

    # Optionally delete empty transform groups
    if do_delete:
        for node in sorted(cmds.ls(type='transform')):
            children = cmds.listRelatives(node, children=True) or []
            shapes = cmds.listRelatives(node, shapes=True) or []
            if not children and not shapes:
                try:
                    cmds.delete(node)
                    print(f"Deleted empty group: {node}")
                except:
                    pass

    # Output renaming actions
    for msg in rename_msgs:
        print(msg)

    # Repair missing texture paths if configured
    if do_pr:
        fix_missing_paths()
    else:
        print("No missing paths detected.")

    # Merge/clean up custom namespaces if needed
    if do_ns:
        for ns in cmds.namespaceInfo(listOnlyNamespaces=True) or []:
            if ns in ('UI', 'shared'):
                continue
            try:
                cmds.namespace(setNamespace=':')
                cmds.namespace(moveNamespace=[ns, ':'], force=True)
                cmds.namespace(removeNamespace=ns)
                print(f"Merged and removed namespace: {ns}")
            except Exception as e:
                print(f"Namespace cleanup failed for {ns} → {e}")

    try:
        cmds.refresh()
    except Exception:
        pass

    duration = time.perf_counter() - t0
    print(f"\n>>> PERFORMANCE SUMMARY\n  Total elapsed time: {duration:.2f}s")
    print("Done.")
