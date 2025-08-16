import os

tool_path = os.path.join(os.path.dirname(__file__), "run_tool.py")
exec(open(tool_path).read())
