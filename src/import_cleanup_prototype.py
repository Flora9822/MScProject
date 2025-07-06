import os
import re
import maya.cmds as cmds

def batch_import_and_cleanup(
    folder_path=None,
    use_naming=True,
    use_path_repair=True,
    use_ns_cleanup=True
):
    # determine assets directory
    assets_dir = folder_path or os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'test_assets')
    )

    # ensure USD plugin is loaded
    if not cmds.pluginInfo('mayaUsdPlugin', query=True, loaded=True):
        try:
            cmds.loadPlugin('mayaUsdPlugin', quiet=True)
        except:
            pass

    # collect & dedupe files
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

    # record existing transforms
    before = set(cmds.ls(type='transform'))

    # import each into its own namespace
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
            msg = str(e)
            if 'import chaser' in msg or 'requires' in msg:
                print(f"Ignored renderer plugin error for {base}")
            else:
                print(f"Failed to import {base} → {e}")

    # identify newly created transforms
    after = set(cmds.ls(type='transform'))
    new_nodes = after - before

    # delete empty groups
    for node in new_nodes:
        children = cmds.listRelatives(node, children=True) or []
        shapes   = cmds.listRelatives(node, shapes=True)   or []
        if not children and not shapes:
            try:
                cmds.delete(node)
                print(f"Deleted empty group: {node}")
            except:
                pass

    # optional renaming
    if use_naming:
        for node in new_nodes:
            if cmds.objExists(node):
                try:
                    short_name = node.split(':')[-1]
                    safe = re.sub(r'[^A-Za-z0-9_]', '_', short_name)
                    new_name = f"ASSET_{safe}"
                    cmds.rename(node, new_name)
                    print(f"Renamed {node} → {new_name}")
                except Exception as e:
                    print(f"Failed to rename {node} → {e}")
    else:
        print("Naming convention skipped.")

    # optional path checking
    if use_path_repair:
        try:
            info = cmds.filePathEditor(
                query=True, listFiles="", withAttribute=True, status=True
            ) or []
            missing = [info[i] for i in range(2, len(info), 3) if info[i] == 0]
            if missing:
                print(f"Found {len(missing)} missing paths.")
            else:
                print("No missing paths detected.")
        except Exception as e:
            print(f"Path checking failed: {e}")
    else:
        print("Path repair skipped.")

    # optional namespace cleanup
    if use_ns_cleanup:
        # move everything back to root and delete empty namespaces
        all_ns = cmds.namespaceInfo(listOnlyNamespaces=True) or []
        for ns in all_ns:
            if ns in ('UI', 'shared'):  # skip Maya defaults
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
