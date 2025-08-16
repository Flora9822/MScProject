import maya.cmds as cmds
import os

def create_shelf_button():
    shelf_name = "Custom"
    button_label = "PipelineTool"
    icon_name = "pythonFamily.png"  # Maya built-in icon

    try:
        project_path = os.path.dirname(__file__)
    except NameError:
        # Fallback: manually set path if __file__ not available (e.g. in Maya Script Editor)
        project_path = "/home/s5722414/Documents/MScProject"  # artist actual path

    run_tool_path = os.path.join(project_path, "run_tool.py")

    if not os.path.isfile(run_tool_path):
        cmds.warning("run_tool.py not found!")
        return

    # Button command
    command = (
        "import os\n"
        f"exec(open(r'{run_tool_path}').read())"
    )

    # Create shelf tab if it doesn't exist
    if not cmds.shelfLayout(shelf_name, exists=True):
        cmds.setParent("ShelfLayout")
        cmds.shelfLayout(shelf_name, p="ShelfLayout")

    # Delete existing button if already exists
    if cmds.shelfButton(button_label, exists=True):
        cmds.deleteUI(button_label)

    # Create new shelf button
    cmds.setParent(shelf_name)
    cmds.shelfButton(label=button_label,
                     command=command,
                     image=icon_name,
                     sourceType="python")

    cmds.inViewMessage(amg="Pipeline Tool shelf button added ✔", pos="topCenter", fade=True)

create_shelf_button()
