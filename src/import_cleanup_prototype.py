import os
import re
import json
import maya.cmds as cmds

# Load pipeline rules from JSON
rules_path = os.path.join(os.path.dirname(__file__), 'rules', 'pipeline_rules.json')
with open(rules_path, 'r') as f:
    pipeline_rules = json.load(f)

# USD import mode flags (set by UI)
USD_IMPORT_AS_REF = False
USD_IMPORT_AS_NODES = True


def reload_rules(rules_file_path):
    """
    Reload pipeline_rules from the given JSON file.
    """
    global pipeline_rules
    with open(rules_file_path, 'r') as f:
        pipeline_rules = json.load(f)
    print(f"Reloaded pipeline_rules from: {rules_file_path}")


def batch_import_and_cleanup(folder_path=None):
    """
    Batch-import assets, cleanup empty groups, rename, repair paths, and merge namespaces.
    """
    # Read config
    prefix        = pipeline_rules['naming']['prefix']
    sanitize_pat  = pipeline_rules['naming']['sanitizePattern']
    do_delete     = pipeline_rules['cleanup']['deleteEmptyGroups']
    do_ns_clean   = pipeline_rules['cleanup']['namespaceCleanup']
    do_path_fix   = pipeline_rules['pathRepair']['autoFix']
    use_naming    = bool(prefix)

    print(f">>> DEBUG USD flags  REF: {USD_IMPORT_AS_REF}, NODES: {USD_IMPORT_AS_NODES}")

    # Determine assets directory
    assets_dir = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )

    # Ensure USD plugin if needed
    if (USD_IMPORT_AS_REF or USD_IMPORT_AS_NODES) and not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        try:
            cmds.loadPlugin('mayaUsdPlugin', quiet=True)
            print("Loaded plugin: mayaUsdPlugin")
        except:
            print("Could not load mayaUsdPlugin")

    # Gather & dedupe asset files
    seen = set()
    asset_files = []
    for fname in os.listdir(assets_dir):
        if fname.lower().endswith(('.fbx', '.abc', '.ma', '.mb', '.usd', '.usda', '.obj')):
            base = os.path.splitext(fname)[0]
            if base not in seen:
                seen.add(base)
                asset_files.append(os.path.join(assets_dir, fname))
            else:
                print(f"Skipping duplicate asset: {base}")

    # Record existing transforms
    before = set(cmds.ls(type='transform'))

    # Import each asset
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
                    print(f"Skipping USD asset: {base}")
            elif ext == '.obj':
                cmds.file(fp, i=True, type='OBJ', namespace=base, ignoreVersion=True)
                print(f"Imported OBJ: {base}")
            else:
                cmds.file(fp, i=True, namespace=base, ignoreVersion=True)
                print(f"Imported: {base}")
        except Exception as e:
            msg = str(e).lower()
            if 'import chaser' in msg or 'requires' in msg:
                print(f"Ignored renderer plugin error for {base}")
            else:
                print(f"Failed to import {base} → {e}")

    # Identify new nodes
    after = set(cmds.ls(type='transform'))
    new_nodes = after - before

    # Delete empty groups, skipping referenced nodes
    if do_delete:
        for node in new_nodes:
            # skip if node is part of a reference
            try:
                if cmds.referenceQuery(node, isNodeReferenced=True):
                    print(f"  Skipping deletion of referenced node: {node}")
                    continue
            except:
                pass

            children = cmds.listRelatives(node, children=True) or []
            shapes   = cmds.listRelatives(node, shapes=True)   or []
            if not children and not shapes:
                try:
                    cmds.delete(node)
                    print(f"  Deleted empty group: {node}")
                except Exception as e:
                    print(f"⚠️  Could not delete {node}: {e}")
    else:
        print("Delete empty groups skipped.")

    # Rename new nodes
    if use_naming:
        for node in new_nodes:
            if not cmds.objExists(node):
                continue
            try:
                short = node.split(':')[-1]
                safe  = re.sub(sanitize_pat, '_', short)
                new   = f"{prefix}{safe}"
                cmds.rename(node, new)
                print(f"Renamed {node} → {new}")
            except Exception as e:
                print(f"Failed to rename {node} → {e}")
    else:
        print("Naming convention skipped.")

    # Path repair
    if do_path_fix:
        try:
            info    = cmds.filePathEditor(query=True, listFiles="", withAttribute=True, status=True) or []
            missing = [info[i] for i in range(2, len(info), 3) if info[i] == 0]
            if missing:
                print(f"Found {len(missing)} missing paths, fixing…")
                cmds.filePathEditor(edit=True, fixMissingPath=True)
                print("Path repair complete.")
            else:
                print("No missing paths detected.")
        except Exception as e:
            print(f"Path repair failed: {e}")
    else:
        print("Path repair skipped.")

    # Namespace cleanup
    if do_ns_clean:
        all_ns = cmds.namespaceInfo(listOnlyNamespaces=True) or []
        for ns in all_ns:
            if ns in ('UI', 'shared'):
                continue
            try:
                cmds.namespace(setNamespace=':')
                cmds.namespace(moveNamespace=[ns, ':'], force=True)
                cmds.namespace(removeNamespace=ns)
                print(f"Merged and removed namespace: {ns}")
            except Exception as e:
                print(f"Namespace cleanup failed for {ns} → {e}")
    else:
        print("Namespace cleanup skipped.")

    print("Done.")
