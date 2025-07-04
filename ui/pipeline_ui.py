from PySide2 import QtWidgets, QtCore
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class PipelineToolUI(QtWidgets.QDialog):
    def __init__(self):
        super(PipelineToolUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Asset Import & Prep Tool")
        self.setMinimumWidth(300)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 1. Directory selection
        self.dir_line_edit = QtWidgets.QLineEdit()
        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self.choose_folder)
        dir_layout = QtWidgets.QHBoxLayout()
        dir_layout.addWidget(self.dir_line_edit)
        dir_layout.addWidget(browse_button)
        layout.addLayout(dir_layout)

        # 2. Import & Clean button
        self.run_button = QtWidgets.QPushButton("Import & Clean")
        self.run_button.clicked.connect(self.on_run)
        layout.addWidget(self.run_button)

        # 3. Log output area
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def choose_folder(self):
        selected_dir = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if selected_dir:
            self.dir_line_edit.setText(selected_dir)

    def on_run(self):
        # Disable the run button to prevent multiple clicks
        self.run_button.setEnabled(False)
        self.log_output.clear()

        # Redirect stdout to the log output widget
        import sys
        class ConsoleStream:
            def write(inner_self, message):
                self.log_output.appendPlainText(message)
        sys.stdout = ConsoleStream()

        # Execute batch import, cleanup, and renaming
        from import_cleanup_prototype import batch_import_and_cleanup
        batch_import_and_cleanup()

        # Restore stdout and re-enable the button
        sys.stdout = sys.__stdout__
        self.run_button.setEnabled(True)

def show_pipeline_ui():
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
