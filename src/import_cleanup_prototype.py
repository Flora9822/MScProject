import os
import maya.cmds as cmds

ASSETS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'test_assets')
)

def batch_import_and_cleanup():
    asset_files = [
        os.path.join(ASSETS_DIR, f)
        for f in os.listdir(ASSETS_DIR)
        if f.lower().endswith(('.fbx', '.abc', '.ma', '.mb', '.usd', '.obj'))
    ]
    before = set(cmds.ls(type='transform'))
    for f in asset_files:
        try:
            cmds.file(f, i=True, ignoreVersion=True)
            print(f"Imported: {os.path.basename(f)}")
        except Exception as e:
            print(f"Failed to import {os.path.basename(f)} → {e}")
    after = set(cmds.ls(type='transform'))
    new_nodes = after - before
    # delete empty groups
    for node in new_nodes:
        children = cmds.listRelatives(node, children=True) or []
        shapes   = cmds.listRelatives(node, shapes=True)  or []
        if not children and not shapes:
            try:
                cmds.delete(node)
                print(f"Deleted empty group: {node}")
            except:
                pass
    # rename new nodes
    for node in new_nodes:
        if cmds.objExists(node):
            try:
                new_name = f"ASSET_{node}"
                cmds.rename(node, new_name)
                print(f"Renamed {node} → {new_name}")
            except:
                pass
    print("Done.")

if __name__ == "__main__":
    batch_import_and_cleanup()
