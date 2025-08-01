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
        self.original_scales = {}  # Cache original scales to avoid cumulative scaling
        self._build_ui()
        self._update_ui_from_rules()

        try:
            self.script_job_number = cmds.scriptJob(event=["SelectionChanged", self._on_selection_changed], protected=True)
        except Exception:
            self.script_job_number = None

    def closeEvent(self, event):
        if self.script_job_number and cmds.scriptJob(exists=self.script_job_number):
            cmds.scriptJob(kill=self.script_job_number, force=True)
        super(PipelineToolUI, self).closeEvent(event)

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Load Rules and Help buttons
        h_load_help = QtWidgets.QHBoxLayout()
        self.load_rules_btn = QtWidgets.QPushButton("Load Rules…")
        self.load_rules_btn.setFixedWidth(370)
        self.load_rules_btn.clicked.connect(self._on_load_rules)
        h_load_help.addWidget(self.load_rules_btn)
        h_load_help.addStretch()
        self.help_btn = QtWidgets.QPushButton("?")
        self.help_btn.setFixedSize(36, 36)
        self.help_btn.setStyleSheet(
            "background-color: #007acc; color: white; border-radius: 18px; font-weight: bold; font-size: 20px;"
        )
        self.help_btn.clicked.connect(self._on_help)
        h_load_help.addWidget(self.help_btn)
        h_load_help.addStretch()
        layout.addLayout(h_load_help)

        # Directory selection
        h = QtWidgets.QHBoxLayout()
        self.dir_line = QtWidgets.QLineEdit()
        self.dir_line.setMinimumWidth(360)
        btn = QtWidgets.QPushButton("Browse…")
        btn.clicked.connect(self._on_choose_folder)
        h.addWidget(self.dir_line)
        h.addWidget(btn)
        layout.addLayout(h)

        # Preview and Batch Repair buttons
        row = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("Preview Renaming")
        self.preview_btn.clicked.connect(self._on_preview)
        self.batch_repair_btn = QtWidgets.QPushButton("Batch Path Repair")
        self.batch_repair_btn.clicked.connect(self._on_batch_repair)
        row.addWidget(self.preview_btn)
        row.addWidget(self.batch_repair_btn)
        layout.addLayout(row)

        # Preview table
        self.preview_table = QtWidgets.QTableWidget(0, 2)
        self.preview_table.setHorizontalHeaderLabels(["Original", "New Name"])
        self.preview_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.preview_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.preview_table)

        # Naming checkbox + prefix input
        h_naming = QtWidgets.QHBoxLayout()
        self.naming_cb = QtWidgets.QCheckBox("Enable Naming")
        self.naming_cb.stateChanged.connect(self._on_naming_enabled)
        h_naming.addWidget(self.naming_cb)

        self.naming_prefix_edit = QtWidgets.QLineEdit()
        self.naming_prefix_edit.setFixedWidth(150)
        h_naming.addWidget(self.naming_prefix_edit)
        h_naming.addStretch()
        layout.addLayout(h_naming)

        # Path repair and namespace cleanup checkboxes
        self.path_cb = QtWidgets.QCheckBox("Enable Auto Path Repair")
        layout.addWidget(self.path_cb)
        self.ns_cb = QtWidgets.QCheckBox("Enable Namespace Cleanup")
        layout.addWidget(self.ns_cb)

        # Center on import checkbox + scale slider
        h_scale_center = QtWidgets.QHBoxLayout()
        self.center_on_import_cb = QtWidgets.QCheckBox("Center on Import")
        h_scale_center.addWidget(self.center_on_import_cb)
        h_scale_center.addStretch()
        h_scale_center.addWidget(QtWidgets.QLabel("Scale"))
        self.scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scale_slider.setRange(50, 150)
        self.scale_slider.setValue(100)
        self.scale_slider.setFixedWidth(120)
        self.scale_slider.valueChanged.connect(self._on_scale_slider_changed)
        h_scale_center.addWidget(self.scale_slider)
        layout.addLayout(h_scale_center)

        # USD import mode selection
        box = QtWidgets.QGroupBox("USD Import Mode")
        hb = QtWidgets.QHBoxLayout(box)
        self.radio_nodes = QtWidgets.QRadioButton("Import as Nodes")
        self.radio_ref = QtWidgets.QRadioButton("Import as Reference")
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

        # Export button
        self.export_btn = QtWidgets.QPushButton("Export Selection to USD")
        self.export_btn.clicked.connect(self._on_usd_export)
        layout.addWidget(self.export_btn)

        # Run button
        self.run_btn = QtWidgets.QPushButton("Import & Clean")
        self.run_btn.clicked.connect(self._on_run)
        layout.addWidget(self.run_btn)

        # Log output
        self.log_output = QtWidgets.QPlainTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Progress bar at bottom
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

    def _update_ui_from_rules(self):
        rules = import_cleanup_prototype.pipeline_rules
        pfx = rules['naming']['prefix']
        self.naming_cb.setChecked(bool(pfx))
        self.naming_prefix_edit.setText(pfx)
        self.naming_prefix_edit.setEnabled(self.naming_cb.isChecked())
        self.path_cb.setChecked(rules['pathRepair']['autoFix'])
        self.ns_cb.setChecked(rules['cleanup']['namespaceCleanup'])

    def _on_naming_enabled(self, state):
        enabled = state == QtCore.Qt.Checked
        self.naming_prefix_edit.setEnabled(enabled)

    def _on_scale_slider_changed(self, value):
        scale_factor = value / 100.0
        selected = cmds.ls(selection=True, long=True)
        if not selected:
            print("No object selected for scaling.")
            return

        for node in selected:
            if node not in self.original_scales:
                try:
                    sx = cmds.getAttr(f"{node}.scaleX")
                    sy = cmds.getAttr(f"{node}.scaleY")
                    sz = cmds.getAttr(f"{node}.scaleZ")
                    self.original_scales[node] = (sx, sy, sz)
                except Exception as e:
                    print(f"Failed to get original scale for {node}: {e}")
                    continue

            try:
                ox, oy, oz = self.original_scales[node]
                cmds.setAttr(f"{node}.scaleX", ox * scale_factor)
                cmds.setAttr(f"{node}.scaleY", oy * scale_factor)
                cmds.setAttr(f"{node}.scaleZ", oz * scale_factor)
            except Exception as e:
                print(f"Failed to scale {node}: {e}")

    def _on_selection_changed(self):
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(100)
        self.scale_slider.blockSignals(False)
        self.original_scales.clear()

    def _on_load_rules(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Rules JSON", "", "JSON Files (*.json)")
        if not path:
            return
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
                cnt = sum(1 for _ in stage.Traverse())
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
                    sel = vset.GetVariantSelection()
                    si = QtWidgets.QTreeWidgetItem([sn, "VariantSet", sel])
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
        set_item = item.parent()
        prim_item = set_item.parent()
        prim_path = prim_item.text(0)
        set_name = set_item.text(0)
        variant = item.text(0)

        stage = Usd.Stage.Open(self.current_usd)
        prim = stage.GetPrimAtPath(prim_path)
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

        import_cleanup_prototype.USD_IMPORT_AS_REF = self.radio_ref.isChecked()
        import_cleanup_prototype.USD_IMPORT_AS_NODES = self.radio_nodes.isChecked()

        prefix = self.naming_prefix_edit.text() if self.naming_cb.isChecked() else ""
        import_cleanup_prototype.pipeline_rules['naming']['prefix'] = prefix

        import_cleanup_prototype.pipeline_rules['pathRepair']['autoFix'] = self.path_cb.isChecked()
        import_cleanup_prototype.pipeline_rules['cleanup']['namespaceCleanup'] = self.ns_cb.isChecked()

        # Pass center_on_import and scale value to the batch import function
        import_cleanup_prototype.batch_import_and_cleanup(
            self.dir_line.text().strip() or None,
            center_on_import=self.center_on_import_cb.isChecked(),
            scale_factor=self.scale_slider.value() / 100.0,
            progress_callback=self._on_progress_update
        )

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
        self.progress_bar.setValue(0)

    def _on_progress_update(self, percent):
        self.progress_bar.setValue(percent)

    def _on_help(self):
        QtWidgets.QMessageBox.information(self, "Help", "Asset Import & Prep Tool\n\n"
            "1. Load Rules: Load a JSON file with naming and cleanup rules.\n"
            "2. Select Asset Folder: Choose the folder containing your assets.\n"
            "3. Preview Renaming: See proposed renaming before import.\n"
            "4. Enable Naming: Toggle automatic naming with prefix.\n"
            "5. Enter Prefix: Customize your naming prefix here.\n"
            "6. Enable Path Repair: Auto fix missing texture/cache paths.\n"
            "7. Enable Namespace Cleanup: Flatten namespaces.\n"
            "8. Center on Import: Move imported assets to world origin (0,0,0).\n"
            "9. Scale Assets: Adjust scale of imported assets (slider: 50% to 150%, default 100%).\n"
            "10. USD Import Mode: Choose node or reference import for USD files.\n"
            "11. Import & Clean: Run batch import and cleanup.\n"
            "12. Export Selection to USD: Export current selection.\n"
            "13. Batch Path Repair: Fix broken paths without re-importing.\n"
            "\nFor detailed documentation, please see the project README.")

def show_pipeline_ui():
    global _pipeline_tool
    try:
        _pipeline_tool.close()
    except:
        pass
    _pipeline_tool = PipelineToolUI()
    _pipeline_tool.show()
