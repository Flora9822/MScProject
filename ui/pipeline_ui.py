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
    cmds.warning("pxr.Usd not available; USD variant browsing disabled.")

def maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)

class PipelineToolUI(QtWidgets.QDialog):
    def __init__(self):
        super(PipelineToolUI, self).__init__(parent=maya_main_window())
        self.setWindowTitle("Asset Import & Prep Tool")
        self.setMinimumWidth(480)
        self._build_ui()
        self._update_ui_from_rules()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Top buttons layout: Load Rules  + Help 
        top_btn_layout = QtWidgets.QHBoxLayout()
        
        self.load_rules_btn = QtWidgets.QPushButton("Load Rules…")
        self.load_rules_btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.load_rules_btn.clicked.connect(self._on_load_rules)
        top_btn_layout.addWidget(self.load_rules_btn)

        self.help_btn = QtWidgets.QPushButton("?")
        self.help_btn.setFixedSize(30, 30)
        self.help_btn.setStyleSheet(
            "QPushButton {"
            "border-radius: 15px;"
            "background-color: #007BFF;"
            "color: white;"
            "font-weight: bold;"
            "font-size: 16px;"
            "}"
            "QPushButton:hover { background-color: #0056b3; }"
        )
        self.help_btn.clicked.connect(self._on_help_clicked)
        top_btn_layout.addWidget(self.help_btn)

        layout.addLayout(top_btn_layout)

        h = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        self.dir_line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        btn = QtWidgets.QPushButton("Browse…")
        btn.clicked.connect(self._on_choose_folder)
        h.addWidget(self.dir_line)
        h.addWidget(btn)
        layout.addLayout(h)

        row = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Preview Renaming")
        self.preview_btn.clicked.connect(self._on_preview)
        self.batch_repair_btn = QtWidgets.QPushButton("Batch Path Repair")
        self.batch_repair_btn.clicked.connect(self._on_batch_repair)
        row.addWidget(self.preview_btn)
        row.addWidget(self.batch_repair_btn)
        layout.addLayout(row)

        self.preview_table = QtWidgets.QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Original", "New Name"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.preview_table)

        self.naming_cb = QtWidgets.QCheckBox()
        layout.addWidget(self.naming_cb)
        self.path_cb = QtWidgets.QCheckBox("Enable Auto Path Repair")
        layout.addWidget(self.path_cb)
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        layout.addWidget(self.ns_cb)

        # USD import mode selection
        box = QtWidgets.QGroupBox("USD Import Mode")
        hb = QtWidgets.QHBoxLayout(box)
        self.radio_nodes = QtWidgets.QRadioButton("Import as Nodes")
        self.radio_ref   = QtWidgets.QRadioButton("Import as Reference")
        self.radio_nodes.setChecked(True)
        grp = QtWidgets.QButtonGroup(self)
        grp.addButton(self.radio_nodes)
        grp.addButton(self.radio_ref)
        hb.addWidget(self.radio_nodes)
        hb.addWidget(self.radio_ref)
        layout.addWidget(box)

        # USD layers and variants UI
        self.usd_group = QtWidgets.QGroupBox("USD Layers & Variants")
        self.usd_group.setCheckable(True)
        self.usd_group.setChecked(False)
        vb = QtWidgets.QVBoxLayout(self.usd_group)
        self.usd_tree = QtWidgets.QTreeWidget()
        self.usd_tree.setHeaderLabels(["Path/Name", "Type", "Selected"])
        self.usd_tree.itemDoubleClicked.connect(self._on_variant_activate)
        vb.addWidget(self.usd_tree)
        layout.addWidget(self.usd_group)

        self.export_btn = QtWidgets.QPushButton("Export Selection to USD")
        self.export_btn.clicked.connect(self._on_usd_export)
        layout.addWidget(self.export_btn)

        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self._on_run)
        layout.addWidget(self.run_btn)

        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

    def _update_ui_from_rules(self):
        rules = import_cleanup_prototype.pipeline_rules
        pfx   = rules['naming']['prefix']
        self.naming_cb.setText(f"Enable Naming (prefix={pfx})")
        self.naming_cb.setChecked(bool(pfx))
        self.path_cb.setChecked(rules['pathRepair']['autoFix'])
        self.ns_cb.setChecked(rules['cleanup']['namespaceCleanup'])

    # For testability and possible script access
    def on_preview(self):
        self._on_preview()
    def on_batch_repair(self):
        self._on_batch_repair()
    def on_run(self):
        self._on_run()
    def on_variant_activate(self, *args, **kwargs):
        self._on_variant_activate(*args, **kwargs)

    def _on_load_rules(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Rules JSON", "", "JSON Files (*.json)")
        if not path: return
        try:
            import_cleanup_prototype.reload_rules(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Load Rules Failed", str(e))
            return
        self._update_ui_from_rules()
        QtWidgets.QMessageBox.information(self, "Load Rules", f"Loaded from:\n{path}")

    def _on_choose_folder(self):
        sel = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if sel:
            self.dir_line.setText(sel)

    def _on_preview(self):
        try:
            mapping = import_cleanup_prototype.preview_renaming(self.dir_line.text().strip() or None)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Preview Failed", str(e))
            return

        self.preview_table.setRowCount(0)
        for orig, new in mapping.items():
            r = self.preview_table.rowCount()
            self.preview_table.insertRow(r)
            self.preview_table.setItem(r, 0, QtWidgets.QTableWidgetItem(orig))
            self.preview_table.setItem(r, 1, QtWidgets.QTableWidgetItem(new))

    def _on_batch_repair(self):
        self.log_output.appendPlainText(">>> Running Batch Path Repair…")
        import_cleanup_prototype.fix_missing_paths()

    def _on_usd_export(self):
        sel = cmds.ls(selection=True, long=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Export USD", "No selection.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export USD", "", "USD Files (*.usd *.usda)")
        if not path:
            return

        self.log_output.appendPlainText(f">>> Exporting {len(sel)} to {path} …")
        try:
            if hasattr(cmds, 'usdExport'):
                cmds.usdExport(file=path, selection=sel)
            else:
                cmds.file(path, exportSelected=True, type='USD Export')
            self.log_output.appendPlainText(f" Export complete: {path}")
            if Usd:
                stage = Usd.Stage.Open(path)
                cnt   = sum(1 for _ in stage.Traverse())
                self.log_output.appendPlainText(f">>> USD stage has {cnt} prims.")
        except Exception as e:
            self.log_output.appendPlainText(f" Export failed: {e}")

    def _create_usd_proxy(self, usd_path):
        proxy_name = os.path.basename(usd_path).replace('.', '_') + "_Proxy"
        if cmds.objExists(proxy_name):
            cmds.delete(proxy_name)
        proxy = cmds.createNode("mayaUsdProxyShape", name=proxy_name)
        cmds.setAttr(f"{proxy}.filePath", usd_path, type="string")
        cmds.select(proxy, replace=True)

    def populate_usd_tree(self, usd_path):
        if not Usd:
            return
        self.usd_tree.clear()
        stage = Usd.Stage.Open(usd_path)
        if not stage:
            return

        for lyr in stage.GetLayerStack():
            item = QtWidgets.QTreeWidgetItem([lyr.identifier, "Layer", ""])
            self.usd_tree.addTopLevelItem(item)

        for prim in stage.Traverse():
            vs = prim.GetVariantSets()
            names = vs.GetNames()
            if names:
                pi = QtWidgets.QTreeWidgetItem([prim.GetPath().pathString, "Prim", ""])
                self.usd_tree.addTopLevelItem(pi)
                for sn in names:
                    vset = vs.GetVariantSet(sn)
                    sel  = vset.GetVariantSelection()
                    si   = QtWidgets.QTreeWidgetItem([sn, "VariantSet", sel])
                    pi.addChild(si)
                    for v in vset.GetVariantNames():
                        leaf = QtWidgets.QTreeWidgetItem([v, "Variant", ""])
                        if v == sel:
                            leaf.setSelected(True)
                        si.addChild(leaf)

        self.usd_group.setChecked(True)
        self.usd_tree.expandAll()

    def _on_variant_activate(self, item, _):
        if item.text(1) != "Variant":
            return
        set_item  = item.parent()
        prim_item = set_item.parent()
        prim_path = prim_item.text(0)
        set_name  = set_item.text(0)
        variant   = item.text(0)

        stage = Usd.Stage.Open(self.current_usd)
        prim  = stage.GetPrimAtPath(prim_path)
        prim.GetVariantSets().GetVariantSet(set_name).SetVariantSelection(variant)
        stage.GetRootLayer().Save()
        for rn in cmds.ls(type='reference'):
            cmds.file(rn, loadReference=True)

    def _on_run(self):
        self.run_btn.setEnabled(False)
        self.log_output.clear()

        import sys
        orig_stdout = sys.stdout
        class Stream:
            def write(_, msg):
                if msg.strip():
                    self.log_output.appendPlainText(msg)
            def flush(_): pass
        sys.stdout = Stream()

        cmds.file(new=True, force=True)

        import_cleanup_prototype.USD_IMPORT_AS_REF   = self.radio_ref.isChecked()
        import_cleanup_prototype.USD_IMPORT_AS_NODES = self.radio_nodes.isChecked()
        import_cleanup_prototype.pipeline_rules['naming']['prefix']      = (
            import_cleanup_prototype.pipeline_rules['naming']['prefix']
            if self.naming_cb.isChecked() else ""
        )
        import_cleanup_prototype.pipeline_rules['pathRepair']['autoFix']  = self.path_cb.isChecked()
        import_cleanup_prototype.pipeline_rules['cleanup']['namespaceCleanup'] = self.ns_cb.isChecked()

        import_cleanup_prototype.batch_import_and_cleanup(self.dir_line.text().strip() or None)

        if self.radio_ref.isChecked() and Usd:
            refs = cmds.file(query=True, reference=True) or []
            usd_refs = [f for f in refs if f.lower().endswith(('.usd', '.usda'))]
            chosen = None
            for usd in usd_refs:
                stage = Usd.Stage.Open(usd)
                if any(prim.GetVariantSets().GetNames() for prim in stage.Traverse()):
                    chosen = usd
                    break

            if chosen:
                self.current_usd = chosen
                self._create_usd_proxy(chosen)
                self.populate_usd_tree(chosen)
            else:
                self.log_output.appendPlainText("No variant-enabled USD found among references.")

        sys.stdout = orig_stdout
        self.run_btn.setEnabled(True)

    def _on_help_clicked(self):
        QtWidgets.QMessageBox.information(
            self, "User Guide",
            "Asset Import & Prep Tool\n\n"
            "1. Load your pipeline rules JSON file (optional).\n"
            "2. Choose an asset folder.\n"
            "3. Use 'Preview Renaming' to check names before importing.\n"
            "4. Enable/disable naming, path repair, and namespace cleanup.\n"
            "5. Select USD import mode.\n"
            "6. Click 'Import & Clean' to process assets.\n"
            "7. Use 'Batch Path Repair' to fix missing paths anytime.\n"
            "8. Export selection to USD as needed.\n\n"
            "For more info, see the project 'README' documentation."
        )

def show_pipeline_ui():
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
