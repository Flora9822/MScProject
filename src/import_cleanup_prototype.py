import os
import json
import re
import maya.cmds as cmds

# Load pipeline rules from JSON
default_rules_path = os.path.join(os.path.dirname(__file__), 'rules', 'pipeline_rules.json')
with open(default_rules_path, 'r') as f:
    pipeline_rules = json.load(f)


def reload_rules(rules_file_path):
    """
    Dynamically reload pipeline_rules from the given JSON file.
    """
    global pipeline_rules
    with open(rules_file_path, 'r') as f:
        pipeline_rules = json.load(f)
    print(f"Reloaded pipeline_rules from: {rules_file_path}")


def batch_import_and_cleanup(folder_path=None):
    # Read settings from pipeline_rules
    naming_prefix    = pipeline_rules['naming']['prefix']
    sanitize_pattern = pipeline_rules['naming']['sanitizePattern']
    do_delete_groups = pipeline_rules['cleanup']['deleteEmptyGroups']
    do_ns_cleanup    = pipeline_rules['cleanup']['namespaceCleanup']
    do_path_repair   = pipeline_rules['pathRepair']['autoFix']
    use_naming       = bool(naming_prefix)

    # Determine assets directory
    assets_dir = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )

    # Ensure USD plugin is loaded
    if not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        try:
            cmds.loadPlugin('mayaUsdPlugin', quiet=True)
        except:
            pass

    # Collect and dedupe asset files
    seen = set()
    asset_files = []
    for fname in os.listdir(assets_dir):
        if fname.lower().endswith(('.fbx', '.abc', '.ma', '.mb', '.usd', '.obj')):
            base = os.path.splitext(fname)[0]
            if base not in seen:
                seen.add(base)
                asset_files.append(os.path.join(assets_dir, fname))
            else:
                print(f"Skipping duplicate asset: {base}")

    # Record transforms before import
    before = set(cmds.ls(type='transform'))

    # Import each file into its own namespace
    for fp in asset_files:
        base = os.path.splitext(os.path.basename(fp))[0]
        ext  = os.path.splitext(fp)[1].lower()
        try:
            if ext == '.usd':
                cmds.file(fp, i=True, type='USD Import', namespace=base, ignoreVersion=True)
            elif ext == '.obj':
                cmds.file(fp, i=True, type='OBJ', namespace=base, ignoreVersion=True)
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
    after     = set(cmds.ls(type='transform'))
    new_nodes = after - before

    # Delete empty transform groups
    if do_delete_groups:
        for node in new_nodes:
            children = cmds.listRelatives(node, children=True) or []
            shapes   = cmds.listRelatives(node, shapes=True)   or []
            if not children and not shapes:
                try:
                    cmds.delete(node)
                    print(f"Deleted empty group: {node}")
                except:
                    pass
    else:
        print("Delete empty groups skipped.")

    # Optional renaming
    if use_naming:
        for node in new_nodes:
            if not cmds.objExists(node):
                continue
            try:
                short_name = node.split(':')[-1]
                safe       = re.sub(sanitize_pattern, '_', short_name)
                new_name   = f"{naming_prefix}{safe}"
                cmds.rename(node, new_name)
                print(f"Renamed {node} → {new_name}")
            except Exception as e:
                print(f"Failed to rename {node} → {e}")
    else:
        print("Naming convention skipped.")

    # Optional path checking & fix
    if do_path_repair:
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

    # Optional namespace cleanup
    if do_ns_cleanup:
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

if __name__ == "__main__":
    batch_import_and_cleanup()
