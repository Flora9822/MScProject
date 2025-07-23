import os
import json
import re
import time

try:
    import maya.cmds as cmds
except ImportError:
    # Dummy cmds for testing outside Maya
    class DummyCmds:
        def ls(self, **kwargs): return []
        def pluginInfo(self, *args, **kwargs): return True
        def file(self, *args, **kwargs): pass
        def listRelatives(self, *args, **kwargs): return []
        def delete(self, *args, **kwargs): pass
        def objExists(self, *args, **kwargs): return False
        def rename(self, node, new): return new
        def filePathEditor(self, *args, **kwargs): return []
        def namespaceInfo(self, **kwargs): return []
        def namespace(self, **kwargs): pass
        def referenceQuery(self, *args, **kwargs): return False
        def loadPlugin(self, *args, **kwargs): return True
        def refresh(self): pass

    cmds = DummyCmds()

USD_IMPORT_AS_REF = False
USD_IMPORT_AS_NODES = True

# Load rules
_rules_path = os.path.join(os.path.dirname(__file__), 'rules', 'pipeline_rules.json')
with open(_rules_path, 'r') as f:
    pipeline_rules = json.load(f)


def reload_rules(rules_file_path):
    """Reload pipeline_rules from the given JSON file."""
    global pipeline_rules
    with open(rules_file_path, 'r') as f:
        pipeline_rules = json.load(f)
    print(f"Reloaded pipeline_rules from: {rules_file_path}")


def _collect_asset_files(folder_path, dedupe=True):
    """
    Return list of full paths to supported asset files.
    If dedupe=True (default), only the first occurrence per base name is kept.
    Raises FileNotFoundError if folder does not exist.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Asset folder not found: {folder_path}")

    exts = ('.fbx', '.abc', '.ma', '.mb', '.usd', '.usda', '.obj', '.gltf', '.glb')
    seen = set()
    files = []
    for name in sorted(os.listdir(folder_path)):
        if name.lower().endswith(exts):
            base = os.path.splitext(name)[0]
            if dedupe:
                if base in seen:
                    continue
                seen.add(base)
            files.append(os.path.join(folder_path, name))
    return files


def preview_renaming(folder_path=None):
    """
    Return mapping original base → prefixed sanitized name.
    Raises FileNotFoundError if folder does not exist.
    """
    folder = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Preview folder not found: {folder}")

    rules = pipeline_rules
    prefix = rules['naming']['prefix']
    pattern = re.compile(rules['naming']['sanitizePattern'])
    mapping = {}

    for name in sorted(os.listdir(folder)):
        base, ext = os.path.splitext(name)
        if ext.lower() in ('.fbx','.abc','.ma','.mb','.usd','.usda','.obj','.gltf','.glb'):
            safe = pattern.sub('_', base)
            mapping[base] = prefix + safe

    return mapping


def fix_missing_paths():
    """Fix all missing file paths in the current Maya scene."""
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
    Batch-import assets (no dedupe), delete empty groups, rename with auto-increment,
    fix paths, and merge namespaces. Raises FileNotFoundError if folder missing.
    """
    rules = pipeline_rules
    prefix = rules['naming']['prefix']
    sanitize_pat = re.compile(rules['naming']['sanitizePattern'])
    do_delete = rules['cleanup']['deleteEmptyGroups']
    do_ns = rules['cleanup']['namespaceCleanup']
    do_pr = rules['pathRepair']['autoFix']
    use_naming = bool(prefix)

    print(f">>> DEBUG USD flags – REF: {USD_IMPORT_AS_REF}, NODES: {USD_IMPORT_AS_NODES}\n")

    t0 = time.perf_counter()

    folder = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Import folder not found: {folder}")

    # Load USD plugin if needed
    if (USD_IMPORT_AS_REF or USD_IMPORT_AS_NODES) and not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        try:
            cmds.loadPlugin('mayaUsdPlugin', quiet=True)
            print("Loaded plugin: mayaUsdPlugin")
        except:
            print("Could not load mayaUsdPlugin")

    # **No dedupe here** to import e.g. both cube.fbx and cube.mb
    asset_files = _collect_asset_files(folder, dedupe=False)
    before = set(cmds.ls(type='transform'))
    imported = []

    # Import phase
    for fp in asset_files:
        base, ext = os.path.splitext(os.path.basename(fp))
        ext = ext.lower()
        try:
            if ext in ('.usd', '.usda'):
                if USD_IMPORT_AS_REF:
                    cmds.file(fp, reference=True, namespace=base, ignoreVersion=True)
                    print(f"Referenced USD: {base}")
                elif USD_IMPORT_AS_NODES:
                    cmds.file(fp, i=True, type='USD Import', namespace=base, ignoreVersion=True)
                    print(f"Imported USD as nodes: {base}")
                else:
                    print(f"Skipped USD: {base}")
            elif ext == '.obj':
                cmds.file(fp, i=True, type='OBJ', namespace=base, ignoreVersion=True)
                print(f"Imported OBJ: {base}")
            elif ext == '.ma':
                cmds.file(fp, i=True, type='mayaAscii', namespace=base, ignoreVersion=True)
                print(f"Imported MA: {base}")
            elif ext == '.mb':
                cmds.file(fp, i=True, type='mayaBinary', namespace=base, ignoreVersion=True)
                print(f"Imported MB: {base}")
            elif ext in ('.gltf','.glb'):
                cmds.file(fp, i=True, namespace=base, ignoreVersion=True)
                print(f"Imported GLTF/GLB: {base}")
            else:
                cmds.file(fp, i=True, namespace=base, ignoreVersion=True)
                print(f"Imported: {base}")
        except Exception as e:
            print(f"⚠️ Failed to import {base} → {e}")

        after = set(cmds.ls(type='transform'))
        new_nodes = sorted(after - before)
        imported += new_nodes
        before = after

    # Delete empty groups
    if do_delete:
        for node in imported:
            children = cmds.listRelatives(node, children=True) or []
            shapes = cmds.listRelatives(node, shapes=True) or []
            if not children and not shapes:
                try:
                    cmds.delete(node)
                    print(f"Deleted empty group: {node}")
                except:
                    pass
    else:
        print("Delete empty groups skipped.")

    # Rename with auto-increment
    if use_naming:
        for node in imported:
            if not cmds.objExists(node):
                continue
            short = node.split(':')[-1]
            safe  = sanitize_pat.sub('_', short)
            cand  = prefix + safe
            if not cmds.objExists(cand):
                final = cand
            else:
                i = 1
                while True:
                    num = f"{cand}_{i:03}"
                    if not cmds.objExists(num):
                        final = num
                        break
                    i += 1
            try:
                cmds.rename(node, final)
                print(f"Renamed {node} → {final}")
            except Exception as e:
                print(f"Failed to rename {node} → {e}")
    else:
        print("Naming convention skipped.")

    # Path repair
    if do_pr:
        fix_missing_paths()
    else:
        print("Path repair skipped.")

    # Namespace cleanup
    if do_ns:
        for ns in cmds.namespaceInfo(listOnlyNamespaces=True) or []:
            if ns in ('UI','shared'):
                continue
            try:
                cmds.namespace(setNamespace=':')
                cmds.namespace(moveNamespace=[ns,':'], force=True)
                cmds.namespace(removeNamespace=ns)
                print(f"Merged and removed namespace: {ns}")
            except Exception as e:
                print(f"Namespace cleanup failed for {ns} → {e}")
    else:
        print("Namespace cleanup skipped.")

    try:
        cmds.refresh()
    except:
        pass

    total = time.perf_counter() - t0
    print(f"\n>>> PERFORMANCE SUMMARY\n  Total elapsed time: {total:.2f}s")
    print("Done.")
