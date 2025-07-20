import os
import re
import json

try:
    import maya.cmds as cmds
except ImportError:
    class _DummyCmds:
        def ls(self, **k): return []
        def pluginInfo(self, *a, **k): return True
        def loadPlugin(self, *a, **k): return True
        def file(self, *a, **k): pass
        def listRelatives(self, *a, **k): return []
        def delete(self, *a, **k): pass
        def objExists(self, *a, **k): return False
        def rename(self, node, new): return new
        def filePathEditor(self, *a, **k): return []
        def namespaceInfo(self, **k): return []
        def namespace(self, **k): pass
        def referenceQuery(self, *a, **k): return False
        def refresh(self): pass
    cmds = _DummyCmds()

# UI-controlled USD import flags
USD_IMPORT_AS_REF   = False
USD_IMPORT_AS_NODES = True

# Load pipeline rules
_rules_path = os.path.join(os.path.dirname(__file__), 'rules', 'pipeline_rules.json')
with open(_rules_path, 'r') as f:
    pipeline_rules = json.load(f)


def reload_rules(rules_file_path):
    """
    Reload pipeline_rules from the given JSON file.
    """
    global pipeline_rules
    with open(rules_file_path, 'r') as f:
        pipeline_rules = json.load(f)
    print(f"Reloaded pipeline_rules from: {rules_file_path}")


def _collect_asset_files(folder_path):
    """
    Return deduped list of full paths to supported asset files,
    one per base name. Raises FileNotFoundError if folder missing.
    """
    if not os.path.isdir(folder_path):
        raise FileNotFoundError(f"Asset folder not found: {folder_path}")
    exts = ('.fbx', '.abc', '.ma', '.mb',
            '.usd', '.usda', '.obj',
            '.gltf', '.glb')
    seen, files = set(), []
    for fn in os.listdir(folder_path):
        if fn.lower().endswith(exts):
            base = os.path.splitext(fn)[0]
            if base not in seen:
                seen.add(base)
                files.append(os.path.join(folder_path, fn))
    return files


def preview_renaming(folder_path=None):
    """
    Compute mapping {base_name: new_name} using current rules,
    with collision resolution. Raises FileNotFoundError if folder missing.
    """
    pr = pipeline_rules
    prefix = pr['naming']['prefix']
    pat    = pr['naming']['sanitizePattern']

    folder = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Preview folder not found: {folder}")

    existing = set()
    mapping  = {}
    for fp in _collect_asset_files(folder):
        base = os.path.splitext(os.path.basename(fp))[0]
        safe = re.sub(pat, '_', base)
        raw  = prefix + safe
        final = raw
        if final in existing:
            i = 1
            while True:
                cand = f"{raw}_{i:03d}"
                if cand not in existing:
                    final = cand
                    break
                i += 1
        existing.add(final)
        mapping[base] = final

    return mapping


def fix_missing_paths():
    """
    Fix all missing file paths in the current Maya scene.
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
    Batch-import all supported asset files (including duplicates),
    cleanup empty groups, rename with collision resolution,
    repair paths, and cleanup namespaces.
    Raises FileNotFoundError if import folder missing.
    """
    pr = pipeline_rules
    prefix         = pr['naming']['prefix']
    pat            = pr['naming']['sanitizePattern']
    do_delete      = pr['cleanup']['deleteEmptyGroups']
    do_ns_cleanup  = pr['cleanup']['namespaceCleanup']
    do_path_repair = pr['pathRepair']['autoFix']
    use_naming     = bool(prefix)

    print(f">>> DEBUG USD flags – REF: {USD_IMPORT_AS_REF}, NODES: {USD_IMPORT_AS_NODES}\n")

    folder = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Import folder not found: {folder}")

    #  USD plugin 
    if (USD_IMPORT_AS_REF or USD_IMPORT_AS_NODES) \
       and not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        try:
            cmds.loadPlugin('mayaUsdPlugin', quiet=True)
            print("Loaded plugin: mayaUsdPlugin")
        except:
            print("Could not load mayaUsdPlugin")

    before = set(cmds.ls(type='transform'))

    # Gather ALL files (no dedupe)
    exts = ('.fbx', '.abc', '.ma', '.mb',
            '.usd', '.usda', '.obj',
            '.gltf', '.glb')
    files = [os.path.join(folder, fn)
             for fn in os.listdir(folder)
             if fn.lower().endswith(exts)]

    # Import phase
    for fp in files:
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
            elif ext in ('.gltf', '.glb'):
                cmds.file(fp, i=True, namespace=base, ignoreVersion=True)
                print(f"Imported GLTF/GLB: {base}")
            else:
                cmds.file(fp, i=True, namespace=base, ignoreVersion=True)
                print(f"Imported: {base}")
        except Exception as e:
            print(f"⚠️  Failed to import {base} → {e}")

    after = set(cmds.ls(type='transform'))
    new_nodes = after - before

    # Delete empty groups
    if do_delete:
        for node in new_nodes:
            kids = cmds.listRelatives(node, children=True) or []
            shps = cmds.listRelatives(node, shapes=True)   or []
            if not kids and not shps:
                try:
                    cmds.delete(node)
                    print(f"Deleted empty group: {node}")
                except:
                    pass
    else:
        print("Delete empty groups skipped.")

    # Rename with collision resolution
    if use_naming:
        existing = set(cmds.ls())
        for node in new_nodes:
            if not cmds.objExists(node):
                continue
            short = node.split(':')[-1]
            safe  = re.sub(pat, '_', short)
            raw   = prefix + safe
            final = raw
            if raw in existing:
                i = 1
                while True:
                    cand = f"{raw}_{i:03d}"
                    if cand not in existing:
                        final = cand
                        break
                    i += 1
            try:
                cmds.rename(node, final)
                print(f"Renamed {node} → {final}")
                existing.add(final)
            except Exception as e:
                print(f"Failed to rename {node} → {e}")
    else:
        print("Naming convention skipped.")

    # Path repair
    if do_path_repair:
        fix_missing_paths()
    else:
        print("Path repair skipped.")

    # Namespace cleanup
    if do_ns_cleanup:
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

    # Refresh viewport
    try:
        cmds.refresh()
    except:
        pass

    print("Done.")
