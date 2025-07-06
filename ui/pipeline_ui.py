from PySide2 import QtWidgets
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from import_cleanup_prototype import batch_import_and_cleanup

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class PipelineToolUI(QtWidgets.QDialog):
    def __init__(self):
        super(PipelineToolUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Asset Import & Prep Tool")
        self.setMinimumWidth(320)
        self.build_ui()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Directory selection
        hl = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        browse = QtWidgets.QPushButton("Browse...")
        browse.clicked.connect(self.choose_folder)
        hl.addWidget(self.dir_line)
        hl.addWidget(browse)
        layout.addLayout(hl)

        # Naming convention
        self.naming_cb = QtWidgets.QCheckBox("Enable Naming Convention")
        self.naming_cb.setChecked(True)
        layout.addWidget(self.naming_cb)

        # Path repair
        self.path_cb = QtWidgets.QCheckBox("Enable Path Repair")
        self.path_cb.setChecked(True)
        layout.addWidget(self.path_cb)

        # Namespace cleanup
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        self.ns_cb.setChecked(True)
        layout.addWidget(self.ns_cb)

        # Run button
        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self.on_run)
        layout.addWidget(self.run_btn)

        # Log output
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def choose_folder(self):
        sel = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if sel:
            self.dir_line.setText(sel)

    def on_run(self):
        self.run_btn.setEnabled(False)
        self.log_output.clear()

        # Redirect print to log widget
        import sys
        class Stream:
            def write(inner, m): 
                self.log_output.appendPlainText(m)
        sys.stdout = Stream()

        # Gather options
        folder = self.dir_line.text().strip() or None
        naming = self.naming_cb.isChecked()
        path_repair = self.path_cb.isChecked()
        ns_cleanup = self.ns_cb.isChecked()

        # Run the pipeline
        batch_import_and_cleanup(folder, naming, path_repair, ns_cleanup)

        # Restore and finish
        sys.stdout = sys.__stdout__
        self.run_btn.setEnabled(True)

def show_pipeline_ui():
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
