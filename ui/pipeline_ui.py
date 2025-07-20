from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
import import_cleanup_prototype
import os
import re

try:
    from pxr import Usd
except ImportError:
    Usd = None
    cmds.warning("pxr.Usd not available; USD export verification disabled.")


def maya_main_window():
    """Return Maya's main window as a QWidget."""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class PipelineToolUI(QtWidgets.QDialog):
    def __init__(self):
        super(PipelineToolUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Asset Import & Prep Tool")
        self.setMinimumWidth(480)
        self.build_ui()
        self.update_ui_from_rules()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Rules loader
        self.load_rules_btn = QtWidgets.QPushButton("Load Rules…")
        self.load_rules_btn.clicked.connect(self.load_rules)
        layout.addWidget(self.load_rules_btn)

        # Asset folder selector
        folder_layout = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.clicked.connect(self.choose_folder)
        folder_layout.addWidget(self.dir_line)
        folder_layout.addWidget(browse_btn)
        layout.addLayout(folder_layout)

        # Preview Renaming & Batch Path Repair
        control_layout = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Preview Renaming")
        self.preview_btn.clicked.connect(self.on_preview)
        self.batch_repair_btn = QtWidgets.QPushButton("Batch Path Repair")
        self.batch_repair_btn.clicked.connect(self.on_batch_repair)
        control_layout.addWidget(self.preview_btn)
        control_layout.addWidget(self.batch_repair_btn)
        layout.addLayout(control_layout)

        # Preview table
        self.preview_table = QtWidgets.QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Original", "New Name"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.preview_table)

        # Option checkboxes
        self.naming_cb = QtWidgets.QCheckBox()
        layout.addWidget(self.naming_cb)
        self.path_cb = QtWidgets.QCheckBox("Enable Auto Path Repair")
        layout.addWidget(self.path_cb)
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        layout.addWidget(self.ns_cb)

        # USD import mode radios
        usd_group = QtWidgets.QGroupBox("USD Import Mode")
        usd_layout = QtWidgets.QHBoxLayout(usd_group)
        self.radio_nodes = QtWidgets.QRadioButton("Import as Nodes")
        self.radio_ref = QtWidgets.QRadioButton("Import as Reference")
        self.radio_nodes.setChecked(True)
        button_group = QtWidgets.QButtonGroup(self)
        button_group.addButton(self.radio_nodes)
        button_group.addButton(self.radio_ref)
        usd_layout.addWidget(self.radio_nodes)
        usd_layout.addWidget(self.radio_ref)
        layout.addWidget(usd_group)

        # USD layers & variants tree
        self.usd_group = QtWidgets.QGroupBox("USD Layers & Variants")
        self.usd_group.setCheckable(True)
        self.usd_group.setChecked(False)
        tree_layout = QtWidgets.QVBoxLayout(self.usd_group)
        self.usd_tree = QtWidgets.QTreeWidget()
        self.usd_tree.setHeaderLabels(["Path/Name", "Type", "Selected"])
        self.usd_tree.itemDoubleClicked.connect(self.on_variant_activate)
        tree_layout.addWidget(self.usd_tree)
        layout.addWidget(self.usd_group)

        # Export selection to USD
        self.export_btn = QtWidgets.QPushButton("Export Selection to USD")
        self.export_btn.clicked.connect(self.on_usd_export)
        layout.addWidget(self.export_btn)

        # Import & clean button
        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self.on_run)
        layout.addWidget(self.run_btn)

        # Log output widget
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def update_ui_from_rules(self):
        rules = import_cleanup_prototype.pipeline_rules
        prefix = rules['naming']['prefix']
        self.naming_cb.setText(f"Enable Naming (prefix={prefix})")
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
            import_cleanup_prototype.reload_rules(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Load Rules Failed", str(e))
            return
        self.update_ui_from_rules()
        QtWidgets.QMessageBox.information(self, "Load Rules", f"Loaded from:\n{path}")

    def choose_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if folder:
            self.dir_line.setText(folder)

    def on_preview(self):
        folder = self.dir_line.text().strip() or None
        try:
            mapping = import_cleanup_prototype.preview_renaming(folder)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Preview Failed", str(e))
            return

        self.preview_table.setRowCount(0)
        for original, new_name in mapping.items():
            row = self.preview_table.rowCount()
            self.preview_table.insertRow(row)
            self.preview_table.setItem(row, 0, QtWidgets.QTableWidgetItem(original))
            self.preview_table.setItem(row, 1, QtWidgets.QTableWidgetItem(new_name))

    def on_batch_repair(self):
        self.log_output.appendPlainText(">>> Batch Path Repair Start")

        import sys
        class Stream:
            def write(inner, msg):
                if msg.strip():
                    self.log_output.appendPlainText(msg)
            def flush(inner): pass

        old_stdout = sys.stdout
        sys.stdout = Stream()
        try:
            import_cleanup_prototype.fix_missing_paths()
        except Exception as e:
            self.log_output.appendPlainText(f"❌ Path repair failed: {e}")
        sys.stdout = old_stdout

        self.log_output.appendPlainText(">>> Batch Path Repair End\n")

    def on_usd_export(self):
        selection = cmds.ls(selection=True, long=True)
        if not selection:
            QtWidgets.QMessageBox.warning(self, "Export USD", "No selection.")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export USD", "", "USD Files (*.usd *.usda)"
        )
        if not path:
            return

        self.log_output.appendPlainText(f">>> Exporting {len(selection)} to {path} …")
        try:
            if hasattr(cmds, 'usdExport'):
                cmds.usdExport(file=path, selection=selection)
            else:
                cmds.file(path, exportSelected=True, type='USD Export')
            self.log_output.appendPlainText(f"✅ Export complete: {path}")
            if Usd:
                stage = Usd.Stage.Open(path)
                count = sum(1 for _ in stage.Traverse())
                self.log_output.appendPlainText(f">>> USD stage has {count} prims.")
        except Exception as e:
            self.log_output.appendPlainText(f"❌ Export failed: {e}")

    def populate_usd_tree(self, usd_path):
        if not Usd:
            return
        self.usd_tree.clear()
        stage = Usd.Stage.Open(usd_path)
        if not stage:
            return

        for layer in stage.GetLayerStack():
            item = QtWidgets.QTreeWidgetItem([layer.identifier, "Layer", ""])
            self.usd_tree.addTopLevelItem(item)

        for prim in stage.Traverse():
            vs = prim.GetVariantSets()
            names = vs.GetNames()
            if names:
                prim_item = QtWidgets.QTreeWidgetItem([prim.GetPath().pathString, "Prim", ""])
                self.usd_tree.addTopLevelItem(prim_item)
                for set_name in names:
                    vset = vs.GetVariantSet(set_name)
                    sel = vset.GetVariantSelection()
                    set_item = QtWidgets.QTreeWidgetItem([set_name, "VariantSet", sel])
                    prim_item.addChild(set_item)
                    for variant in vset.GetVariantNames():
                        leaf = QtWidgets.QTreeWidgetItem([variant, "Variant", ""])
                        if variant == sel:
                            leaf.setSelected(True)
                        set_item.addChild(leaf)

        self.usd_group.setChecked(True)
        self.usd_tree.expandAll()

    def on_variant_activate(self, item, _):
        if item.text(1) != "Variant":
            return
        set_item = item.parent()
        prim_item = set_item.parent()
        prim_path = prim_item.text(0)
        set_name = set_item.text(0)
        variant = item.text(0)

        stage = Usd.Stage.Open(self.current_usd)
        prim = stage.GetPrimAtPath(prim_path)
        prim.GetVariantSets().GetVariantSet(set_name).SetVariantSelection(variant)
        stage.GetRootLayer().Save()

        for ref in cmds.ls(type='reference'):
            cmds.file(ref, loadReference=True)

    def on_run(self):
        """Run the full import & cleanup pipeline."""
        self.run_btn.setEnabled(False)
        self.log_output.clear()

        import sys
        class Stream:
            def write(inner, msg):
                if msg.strip():
                    self.log_output.appendPlainText(msg)
            def flush(inner): pass

        old_stdout = sys.stdout
        sys.stdout = Stream()

        cmds.file(new=True, force=True)

        import_cleanup_prototype.USD_IMPORT_AS_REF = self.radio_ref.isChecked()
        import_cleanup_prototype.USD_IMPORT_AS_NODES = self.radio_nodes.isChecked()
        import_cleanup_prototype.pipeline_rules['naming']['prefix'] = (
            import_cleanup_prototype.pipeline_rules['naming']['prefix'] if self.naming_cb.isChecked() else ""
        )
        import_cleanup_prototype.pipeline_rules['pathRepair']['autoFix'] = self.path_cb.isChecked()
        import_cleanup_prototype.pipeline_rules['cleanup']['namespaceCleanup'] = self.ns_cb.isChecked()

        import_cleanup_prototype.batch_import_and_cleanup(self.dir_line.text() or None)

        if self.radio_ref.isChecked() and Usd:
            refs = cmds.file(query=True, reference=True) or []
            usd_refs = [f for f in refs if f.lower().endswith(('.usd', '.usda'))]
            if usd_refs:
                self.current_usd = usd_refs[0]
                self.populate_usd_tree(self.current_usd)

        sys.stdout = old_stdout
        self.run_btn.setEnabled(True)


def show_pipeline_ui():
    """Instantiate and show the pipeline tool UI."""
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
