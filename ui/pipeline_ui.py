from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
import import_cleanup_prototype

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
        self.setMinimumWidth(400)
        self.build_ui()
        self.update_ui_from_rules()

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Load Rules
        self.load_rules_btn = QtWidgets.QPushButton("Load Rules…")
        self.load_rules_btn.clicked.connect(self.load_rules)
        layout.addWidget(self.load_rules_btn)

        # Directory selector
        dir_layout = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("Browse…")
        browse_btn.clicked.connect(self.choose_folder)
        dir_layout.addWidget(self.dir_line)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        # Naming convention checkbox
        self.naming_cb = QtWidgets.QCheckBox()
        layout.addWidget(self.naming_cb)

        # Path repair checkbox
        self.path_cb = QtWidgets.QCheckBox("Enable Path Repair")
        layout.addWidget(self.path_cb)

        # Namespace cleanup checkbox
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        layout.addWidget(self.ns_cb)

        # USD Import Mode radios
        usd_group = QtWidgets.QGroupBox("USD Import Mode")
        usd_layout = QtWidgets.QHBoxLayout(usd_group)
        self.usd_radio_nodes = QtWidgets.QRadioButton("Import as Nodes")
        self.usd_radio_ref   = QtWidgets.QRadioButton("Import as Reference")
        self.usd_radio_nodes.setChecked(True)
        button_group = QtWidgets.QButtonGroup(self)
        button_group.addButton(self.usd_radio_nodes)
        button_group.addButton(self.usd_radio_ref)
        usd_layout.addWidget(self.usd_radio_nodes)
        usd_layout.addWidget(self.usd_radio_ref)
        layout.addWidget(usd_group)

        # USD Layers & Variants
        self.usd_tree_group = QtWidgets.QGroupBox("USD Layers & Variants")
        self.usd_tree_group.setCheckable(True)
        self.usd_tree_group.setChecked(False)
        tree_layout = QtWidgets.QVBoxLayout(self.usd_tree_group)
        self.usd_tree = QtWidgets.QTreeWidget()
        self.usd_tree.setHeaderLabels(["Path/Name", "Type", "Current"])
        self.usd_tree.itemDoubleClicked.connect(self.on_variant_activate)
        tree_layout.addWidget(self.usd_tree)
        layout.addWidget(self.usd_tree_group)

        # Export Selection to USD
        self.export_btn = QtWidgets.QPushButton("Export Selection to USD")
        self.export_btn.clicked.connect(self.on_usd_export)
        layout.addWidget(self.export_btn)

        # Import & Clean
        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self.on_run)
        layout.addWidget(self.run_btn)

        # Log output
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def update_ui_from_rules(self):
        """Sync checkbox labels and states from pipeline_rules."""
        rules = import_cleanup_prototype.pipeline_rules
        prefix = rules['naming']['prefix']
        self.naming_cb.setText(f"Enable Naming Convention (prefix={prefix})")
        self.naming_cb.setChecked(bool(prefix))
        self.path_cb.setChecked(rules['pathRepair']['autoFix'])
        self.ns_cb.setChecked(rules['cleanup']['namespaceCleanup'])

    def load_rules(self):
        """Allow user to pick a JSON rules file and reload it."""
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
        QtWidgets.QMessageBox.information(self, "Load Rules", f"Loaded rules from:\n{path}")

    def choose_folder(self):
        """Open a folder picker to select the assets directory."""
        sel = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if sel:
            self.dir_line.setText(sel)

    def on_usd_export(self):
        """Export the current selection to USD and verify via pxr.Usd."""
        sel = cmds.ls(selection=True, long=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Export USD", "No selection to export.")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export USD", "", "USD Files (*.usd *.usda)"
        )
        if not path:
            return

        self.log_output.appendPlainText(f">>> Exporting {len(sel)} objects to {path} …")
        try:
            if hasattr(cmds, 'usdExport'):
                cmds.usdExport(file=path, selection=sel)
            else:
                cmds.file(path, exportSelected=True, type='USD Export')

            self.log_output.appendPlainText(f" Export complete: {path}")

            if Usd:
                stage = Usd.Stage.Open(path)
                count = sum(1 for _ in stage.Traverse())
                self.log_output.appendPlainText(f">>> USD stage has {count} prims.")
            else:
                self.log_output.appendPlainText(" pxr.Usd not available; skipped verification.")

        except Exception as e:
            self.log_output.appendPlainText(f" Export failed: {e}")
            QtWidgets.QMessageBox.critical(self, "Export USD Failed", str(e))

    def populate_usd_tree(self, usd_path):
        """Read a USD layer and variant tree into the QTreeWidget."""
        if Usd is None:
            return
        self.usd_tree.clear()
        # Open via pxr.Usd
        stage = Usd.Stage.Open(usd_path)
        if not stage:
            return

        # Layers
        for layer in stage.GetLayerStack():
            item = QtWidgets.QTreeWidgetItem([layer.identifier, "Layer", ""])
            self.usd_tree.addTopLevelItem(item)

        # Prims and Variants
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

        self.usd_tree_group.setChecked(True)
        self.usd_tree.expandAll()

    def on_variant_activate(self, item, column):
        """Handle double-click on a Variant item to switch selection."""
        if item.text(1) != "Variant":
            return

        set_item = item.parent()
        prim_item = set_item.parent()
        prim_path = prim_item.text(0)
        set_name = set_item.text(0)
        variant = item.text(0)

        # Save selection change back to USD layer
        stage = Usd.Stage.Open(self.current_usd_path)
        prim = stage.GetPrimAtPath(prim_path)
        prim.GetVariantSets().GetVariantSet(set_name).SetVariantSelection(variant)
        stage.GetRootLayer().Save()

        # Reload references to force Maya to refresh
        for rn in cmds.ls(type='reference'):
            cmds.file(rn, loadReference=True)

    def on_run(self):
        """Execute import & cleanup with current settings, then update USD tree."""
        self.run_btn.setEnabled(False)
        self.log_output.clear()

        # Redirect stdout to the log widget
        import sys
        class Stream:
            def write(inner, msg):
                self.log_output.appendPlainText(msg)
        sys.stdout = Stream()

        # Clear current scene
        cmds.file(new=True, force=True)

        # Apply USD import mode flags
        import_cleanup_prototype.USD_IMPORT_AS_REF   = self.usd_radio_ref.isChecked()
        import_cleanup_prototype.USD_IMPORT_AS_NODES = self.usd_radio_nodes.isChecked()

        # Read UI options
        folder        = self.dir_line.text().strip() or None
        import_cleanup_prototype.pipeline_rules['pathRepair']['autoFix']    = self.path_cb.isChecked()
        import_cleanup_prototype.pipeline_rules['cleanup']['namespaceCleanup'] = self.ns_cb.isChecked()
        import_cleanup_prototype.pipeline_rules['naming']['prefix']         = (
            import_cleanup_prototype.pipeline_rules['naming']['prefix']
            if self.naming_cb.isChecked()
            else ""
        )

        # Run pipeline
        import_cleanup_prototype.batch_import_and_cleanup(folder)

        # After run, if USD reference mode is on, populate tree
        if self.usd_radio_ref.isChecked() and Usd:
            refs = cmds.file(query=True, reference=True) or []
            usd_refs = [f for f in refs if f.lower().endswith(('.usd', '.usda'))]
            if usd_refs:
                self.current_usd_path = usd_refs[0]
                self.populate_usd_tree(self.current_usd_path)

        # Restore stdout
        sys.stdout = sys.__stdout__
        self.run_btn.setEnabled(True)


def show_pipeline_ui():
    """Create and show the tool window."""
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
