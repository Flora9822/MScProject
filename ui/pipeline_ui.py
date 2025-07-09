from PySide2 import QtWidgets
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from import_cleanup_prototype import batch_import_and_cleanup, reload_rules, pipeline_rules
import import_cleanup_prototype

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class PipelineToolUI(QtWidgets.QDialog):
    def __init__(self):
        super(PipelineToolUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Asset Import & Prep Tool")
        self.setMinimumWidth(320)
        self.build_ui()
        self.update_ui_from_rules()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Load Rules button
        self.load_rules_btn = QtWidgets.QPushButton("Load Rules…")
        self.load_rules_btn.clicked.connect(self.load_rules)
        layout.addWidget(self.load_rules_btn)

        # Directory selection
        hl = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        browse = QtWidgets.QPushButton("Browse…")
        browse.clicked.connect(self.choose_folder)
        hl.addWidget(self.dir_line)
        hl.addWidget(browse)
        layout.addLayout(hl)

        # Naming convention checkbox
        self.naming_cb = QtWidgets.QCheckBox()
        layout.addWidget(self.naming_cb)

        # Path repair checkbox
        self.path_cb = QtWidgets.QCheckBox("Enable Path Repair")
        layout.addWidget(self.path_cb)

        # Namespace cleanup checkbox
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        layout.addWidget(self.ns_cb)

        # Run button
        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self.on_run)
        layout.addWidget(self.run_btn)

        # Log output
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def update_ui_from_rules(self):
        """Sync UI controls with current pipeline_rules."""
        rules = import_cleanup_prototype.pipeline_rules
        prefix = rules['naming']['prefix']
        self.naming_cb.setText(f"Enable Naming Convention (prefix={prefix})")
        self.naming_cb.setChecked(bool(prefix))
        self.path_cb.setChecked(rules['pathRepair']['autoFix'])
        self.ns_cb.setChecked(rules['cleanup']['namespaceCleanup'])

    def load_rules(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Rules JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            reload_rules(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Load Rules Failed", str(e))
            return
        self.update_ui_from_rules()
        QtWidgets.QMessageBox.information(self, "Load Rules", f"Loaded rules from:\n{path}")

    def choose_folder(self):
        sel = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if sel:
            self.dir_line.setText(sel)

    def on_run(self):
        self.run_btn.setEnabled(False)
        self.log_output.clear()

        # redirect stdout to log widget
        import sys
        class Stream:
            def write(inner, m):
                self.log_output.appendPlainText(m)
        sys.stdout = Stream()

        folder = self.dir_line.text().strip() or None
        # run pipeline with current rules
        batch_import_and_cleanup(folder)

        # restore stdout
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
