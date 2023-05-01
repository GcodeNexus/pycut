# This Python file uses the following encoding: utf-8

VERSION = "0_5_0_RC2"

import sys
import os
import json
import argparse
import pathlib

import posixpath
import ntpath

from typing import List
from typing import Dict

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from PySide6 import QtWebEngineWidgets

from PySide6.QtUiTools import QUiLoader

# TEST simulator with python
# from gcodesimulator.python.parser.gcodeminiparser import GcodeMiniParser
#import gcodesimulator.python.widgets.glwidget_container as glwidget_simulator_container

import shapely_svgpath_io

from val_with_unit import ValWithUnit

import svgviewer
import gcodeviewer.widgets.glwidget_container as glwidget_container
import gcodesimulator.webglviewer as webglviewer
import gcodesimulator.gcodefileviewer as gcodefileviewer

import operations_tableview
import tabs_tableview
import settings.colorpicker as colorpicker

import material_widget

from gcode_generator import GcodeModel
from gcode_generator import ToolModel
from gcode_generator import SvgModel
from gcode_generator import MaterialModel
from gcode_generator import TabsModel
from gcode_generator import CncOp
from gcode_generator import JobModel
from gcode_generator import Tab

from gcode_generator import GcodeGenerator

import resources_rc
from ui_mainwindow import Ui_mainwindow

class PyCutMainWindow(QtWidgets.QMainWindow):
    '''
    '''
    default_settings = {
        "svg": {
            "px_per_inch" : 96,
        },
        "Tabs": {
            "units"       : "mm",
            "height"      : 1.0,
            "tabs"        : []
        },
        "Tool" : {
            "units"       : "mm",
            "diameter"    : 1.0,
            "angle"       : 180,
            "passdepth"   : 3.0,
            "overlap"     : 0.4,
            "rapid"       : 500,
            "plunge"      : 100,
            "cut"         : 200,
        },
        "Material" : {
            "units"       : "mm",
            "thickness"   : 50.0,
            "z_origin"    : "Top",
            "clearance"   : 10.0,
        },
        "CurveToLineConversion" : {
            "minimum_segments"        : 5,
            "minimum_segments_length" : 0.01,
        },
        "GCodeConversion" : {
            "units"         : "mm",
            "flip_xy"       : False,
            "x_offset"      : 0.0,
            "y_offset"      : 0.0,
            "xy_reference"  : "ZERO_TOP_LEFT_OF_MATERIAL"
        },
        "GCodeGeneration" : {
            "return_to_zero_at_end" : True,
            "spindle_control"       : True,
            "spindle_speed"         : 1000,
            "program_end"           : True 
        }
    }
    
    def __init__(self, options):
        '''
        '''
        super(PyCutMainWindow, self).__init__()

        self.recent_jobs = self.read_recent_jobs()

        self.ui = Ui_mainwindow()
        self.ui.setupUi(self)

        self.setWindowTitle("PyCut")
        self.setWindowIcon(QtGui.QIcon(":/images/tango/32x32/categories/applications-system.png"))

        self.build_recent_jobs_submenu()

        self.operations = []
        self.tabs : List[Dict[str,any]] = []

        # a job to keep the generated gcode in memory (and save it)
        self.job = None

        # open/read/write job settings
        self.jobfilename = None

        self.webgl_viewer = None
        self.gcode_textviewer = None

        self.svg_viewer = self.setup_svg_viewer()
        self.svg_material_viewer = self.setup_material_viewer()
        self.webgl_viewer = self.setup_webgl_viewer()
        self.candle_viewer = self.setup_candle_viewer()

        self.ui.tabsview_manager.set_svg_viewer(self.svg_viewer)
        self.ui.operationsview_manager.set_svg_viewer(self.svg_viewer)

        # callbacks
        self.ui.pushButton_SaveGcode.setIcon(QtGui.QIcon(':/images/tango/22x22/actions/document-save-as.png'))
        self.ui.pushButton_SaveGcode.clicked.connect(self.cb_save_gcode)

        self.ui.actionOpenSvg.triggered.connect(self.cb_open_svg)
        self.ui.actionNewJob.triggered.connect(self.cb_new_job)
        self.ui.actionOpenJob.triggered.connect(self.cb_open_job)
        self.ui.actionSaveJobAs.triggered.connect(self.cb_save_job_as)
        self.ui.actionSaveJob.triggered.connect(self.cb_save_job)

        self.ui.actionSettings.triggered.connect(self.cb_open_settings_dialog)

        self.ui.actionTutorial.triggered.connect(self.cb_show_tutorial)
        self.ui.actionAboutQt.triggered.connect(self.cb_show_about_qt)
        self.ui.actionAboutPyCut.triggered.connect(self.cb_show_about_pycut)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                statusTip="Show the Qt library's About box",
                triggered=QtWidgets.QApplication.instance().aboutQt)

        # display material thickness/clearance
        self.ui.doubleSpinBox_Material_Thickness.valueChanged.connect(self.cb_display_material_thickness)
        self.ui.doubleSpinBox_Material_Clearance.valueChanged.connect(self.cb_display_material_clearance)


        default_thickness = self.ui.doubleSpinBox_Material_Thickness.value()
        default_clearance = self.ui.doubleSpinBox_Material_Clearance.value()
        self.svg_material_viewer.display_material(thickness=default_thickness, clearance=default_clearance)
        
        self.ui.spinBox_CurveToLineConversion_MinimumNbSegments.valueChanged.connect(self.cb_curve_min_segments)
        self.ui.doubleSpinBox_CurveToLineConversion_MinimumSegmentsLength.valueChanged.connect(self.cb_curve_min_segments_length)

        self.display_svg(None)
        
        self.ui.comboBox_Tabs_Units.currentTextChanged.connect(self.cb_update_tabs_display)
        self.ui.comboBox_Tool_Units.currentTextChanged.connect(self.cb_update_tool_display)
        self.ui.comboBox_Material_Units.currentTextChanged.connect(self.cb_update_material_display)
        self.ui.comboBox_GCodeConversion_Units.currentTextChanged.connect(self.cb_update_gcodeconversion_display)

        self.ui.checkBox_GCodeGeneration_SpindleControl.clicked.connect(self.cb_spindle_control)

        self.ui.pushButton_GCodeConversion_ZeroTopLeftOfMaterial.clicked.connect(self.cb_generate_gcode)
        self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfMaterial.clicked.connect(self.cb_generate_gcode)
        self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfOp.clicked.connect(self.cb_generate_gcode)
        self.ui.pushButton_GCodeConversion_ZeroCenterOfOp.clicked.connect(self.cb_generate_gcode)


        self.ui.pushButton_GCodeConversion_ZeroTopLeftOfMaterial.setIcon(QtGui.QIcon(':/images/tango/22x22/actions/view-refresh.png'))
        self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfMaterial.setIcon(QtGui.QIcon(':/images/tango/22x22/actions/view-refresh.png'))
        self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfOp.setIcon(QtGui.QIcon(':/images/tango/22x22/actions/view-refresh.png'))
        self.ui.pushButton_GCodeConversion_ZeroCenterOfOp.setIcon(QtGui.QIcon(':/images/tango/22x22/actions/view-refresh.png'))

        self.ui.buttonGroup_GCodeConversion.setId(self.ui.pushButton_GCodeConversion_ZeroTopLeftOfMaterial, GcodeModel.ZERO_TOP_LEFT_OF_MATERIAL)
        self.ui.buttonGroup_GCodeConversion.setId(self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfMaterial, GcodeModel.ZERO_LOWER_LEFT_OF_MATERIAL)
        self.ui.buttonGroup_GCodeConversion.setId(self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfOp, GcodeModel.ZERO_LOWER_LEFT_OF_OP)
        self.ui.buttonGroup_GCodeConversion.setId(self.ui.pushButton_GCodeConversion_ZeroCenterOfOp, GcodeModel.ZERO_CENTER_OF_OP)
        
        self.ui.checkBox_Tabs_hideAllTabs.clicked.connect(self.cb_tabs_hide_all)
        self.ui.checkBox_Tabs_hideDisabledTabs.clicked.connect(self.cb_tabs_hide_disabled)

        self.init_gui()

        if options.job is not None:
            if os.path.exists(options.job):
                self.open_job(options.job)
            else:
                # alert
                msgBox = QtWidgets.QMessageBox()
                msgBox.setWindowTitle("PyCut")
                msgBox.setText("Job File %s not found" % options.job)
                msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
                msgBox.exec()


        self.menubarToggleLeftSideButton = QtGui.QAction(QtGui.QIcon(":/images/left-area.png"), "hide/show",
                self, shortcut=QtGui.QKeySequence.Back,
                statusTip="Show/Hide Left Side", triggered=self.toggle_left_side)
        self.menubarToggleLeftSideButton.setCheckable(True)
        self.menubarToggleLeftSideButton.setToolTip("Show/Hide Left Side View") # still not shown

        self.menubarToggleMiddleAreaButton = QtGui.QAction(QtGui.QIcon(":/images/bellow-area.png"), "hide/show",
                self, shortcut=QtGui.QKeySequence.Forward,
                statusTip="Show/Hide Op. Table", triggered=self.toggle_middle_area)
        self.menubarToggleMiddleAreaButton.setCheckable(True)
        self.menubarToggleMiddleAreaButton.setToolTip("Show/Hide Op. Table View") # still not shown

        self.menubarToggleRightSideButton = QtGui.QAction(QtGui.QIcon(":/images/right-area.png"), "hide/show",
                self, shortcut=QtGui.QKeySequence.Forward,
                statusTip="Show/Hide Right Side", triggered=self.toggle_right_side)
        self.menubarToggleRightSideButton.setCheckable(True)
        self.menubarToggleRightSideButton.setToolTip("Show/Hide Right Side View") # still not shown

        self.menuBar().addAction(self.menubarToggleLeftSideButton)
        self.menuBar().addAction(self.menubarToggleMiddleAreaButton)
        self.menuBar().addAction(self.menubarToggleRightSideButton)
        
        # how set add a combobox to the menu bar ??
        # self.comboBoxGeomPreviewColor = QtWidgets.QComboBox(self.menuBar())
        # self.comboBoxGeomPreviewColor.setItemData(0, QtGui.QColor.red, QtGui.Qt.DecorationRole)
        # self.comboBoxGeomPreviewColor.setItemData(1, QtGui.QColor.blue, QtGui.Qt.DecorationRole)
        # self.comboBoxGeomPreviewColor.setItemData(1, QtGui.QColor.green, QtGui.Qt.DecorationRole)
        # self.menubarChangeGeomPreviewColorAction = QtWidgets.QWidgetAction(self.menuBar())
        # self.menubarChangeGeomPreviewColorAction.setDefaultWidget(self.comboBoxGeomPreviewColor)
        # self.menuBar().addAction(self.menubarChangeGeomPreviewColorAction)


        # these callbacks only after have loading a job
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.connect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.connect(self.cb_generate_gcode_y_offset)
        self.ui.checkBox_GCodeConversion_FlipXY.clicked.connect(self.cb_generate_gcode)


        self.setWindowState(QtCore.Qt.WindowMaximized)

    def toggle_left_side(self):
        '''
        '''
        if self.menubarToggleLeftSideButton.isChecked():
            self.ui.scrollArea_left.hide()
        else:
            self.ui.scrollArea_left.show()

    def toggle_middle_area(self):
        '''
        '''
        if self.menubarToggleMiddleAreaButton.isChecked():
            self.ui.operationsview_manager.hide()
        else:
            self.ui.operationsview_manager.show()

    def toggle_right_side(self):
        '''
        '''
        if self.menubarToggleRightSideButton.isChecked():
            self.ui.scrollArea_right.hide()
        else:
            self.ui.scrollArea_right.show()

    def cb_open_settings_dialog(self):
        '''
        '''
        global settings_dialog

        def fill_dialog():
            settings_dialog.colorpicker_Tabs_fill.setColor(QtGui.QColor(svgviewer.SvgViewer.TABS["fill"]))
            settings_dialog.doubleSpinBox_Tabs_fill_opacity.setValue(float(svgviewer.SvgViewer.TABS["fill-opacity"]))
            settings_dialog.doubleSpinBox_Tabs_fill_opacity_disabled.setValue(float(svgviewer.SvgViewer.TABS["fill-opacity-disabled"]))

            settings_dialog.colorpicker_Toolpath_stroke.setColor(QtGui.QColor(svgviewer.SvgViewer.TOOLPATHS["stroke"]))
            settings_dialog.doubleSpinBox_Toolpath_stroke_width.setValue(float(svgviewer.SvgViewer.TOOLPATHS["stroke-width"]))

            settings_dialog.colorpicker_GeometryPreview_fill.setColor(QtGui.QColor(svgviewer.SvgViewer.GEOMETRY_PREVIEW_CLOSED_PATHS["fill"]))
            settings_dialog.doubleSpinBox_GeometryPreview_fill_opacity.setValue(float(svgviewer.SvgViewer.GEOMETRY_PREVIEW_CLOSED_PATHS["fill-opacity"]))

            settings_dialog.colorpicker_GeometryPreview_stroke.setColor(QtGui.QColor(svgviewer.SvgViewer.GEOMETRY_PREVIEW_OPENED_PATHS["stroke"]))
            settings_dialog.doubleSpinBox_GeometryPreview_stroke_opacity.setValue(float(svgviewer.SvgViewer.GEOMETRY_PREVIEW_OPENED_PATHS["stroke-opacity"]))
            settings_dialog.doubleSpinBox_GeometryPreview_stroke_width.setValue(float(svgviewer.SvgViewer.GEOMETRY_PREVIEW_OPENED_PATHS["stroke-width"]))

        def set_defaults():
            self.svg_viewer.set_default_settings()
            fill_dialog()

        def set_ok():
            settings = {
                "TABS" : {
                    "stroke": "#aa4488",
                    "stroke-width": "0",
                    "fill": settings_dialog.colorpicker_Tabs_fill.color().name(),
                    "fill-opacity": str(settings_dialog.doubleSpinBox_Tabs_fill_opacity.value()),
                    "fill-opacity-disabled": str(settings_dialog.doubleSpinBox_Tabs_fill_opacity_disabled.value()),
                },
                "GEOMETRY_PREVIEW_CLOSED_PATHS" : {
                    "stroke": "#ff0000",
                    "stroke-width": "0",
                    "stroke-opacity": "1.0",
                    "fill": settings_dialog.colorpicker_GeometryPreview_fill.color().name(),
                    "fill-opacity": str(settings_dialog.doubleSpinBox_GeometryPreview_fill_opacity.value()),
                },
                "GEOMETRY_PREVIEW_OPENED_PATHS" : {
                    "stroke": settings_dialog.colorpicker_GeometryPreview_stroke.color().name(),
                    "stroke-width": str(settings_dialog.doubleSpinBox_GeometryPreview_stroke_width.value()),
                    "stroke-opacity": str(settings_dialog.doubleSpinBox_GeometryPreview_stroke_opacity.value()),
                    "fill": "none",
                    "fill-opacity": "1.0"
                },
                "TOOLPATHS" : {
                    "stroke": settings_dialog.colorpicker_Toolpath_stroke.color().name(),
                    "stroke-width": str(settings_dialog.doubleSpinBox_Toolpath_stroke_width.value()),
                }
            }
            self.svg_viewer.set_settings(settings)
            settings_dialog.close()

        def set_cancel():
            settings_dialog.close()

        loader = QUiLoader(None)
        loader.registerCustomWidget(colorpicker.ColorPicker)

        settings_dialog = loader.load("./settings/settings.ui")
        fill_dialog()
        settings_dialog.cmdDefaults.clicked.connect(set_defaults)
        settings_dialog.cmdOK.clicked.connect(set_ok)
        settings_dialog.cmdCancel.clicked.connect(set_cancel)

        settings_dialog.exec()

    '''
    def cb_show_tutorial(self):
        dlg = QtWidgets.QDialog(self)

        view = QtWidgets.QTextBrowser(dlg)
        view.setReadOnly(True)
        view.setMinimumSize(800,500)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(view)

        dlg.setLayout(mainLayout)
        dlg.setWindowTitle("PyCut Tutorial")
        dlg.setModal(True)

        try:
            view.setSource(QtCore.QUrl.fromLocalFile(":/doc/tutorial.html"))
        except Exception as msg:
            view.setHtml(self.notfound % {'message':str(msg)})

        dlg.show()
    '''

    def cb_show_tutorial(self):
        '''
        in test
        '''
        dlg = QtWidgets.QDialog(self)


        htmlView = QtWebEngineWidgets.QWebEngineView(dlg)
        htmlView.setMinimumSize(1100,600)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(htmlView)

        dlg.setLayout(mainLayout)
        dlg.setWindowTitle("PyCut Tutorial")
        dlg.setModal(True)

        fileName = ":/doc/tutorial.html"
        file = QtCore.QFile(fileName)
        if file.open(QtCore.QIODevice.ReadOnly):
            data = str(file.readAll(), 'utf-8') # explicit encoding
        else:
            data = "ERROR"

        file.close()

        htmlView.setHtml(data)

        dlg.show()

    def cb_show_about_qt(self):
        QtWidgets.QApplication.instance().aboutQt()

    def cb_show_about_pycut(self):
        dlg = QtWidgets.QDialog(self)

        view = QtWidgets.QTextBrowser(dlg)
        view.setReadOnly(True)
        view.setMinimumSize(800,500)

        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(view)

        dlg.setLayout(mainLayout)
        dlg.setWindowTitle("PyCut Relnotes")
        dlg.setModal(True)

        try:
            view.setSource(QtCore.QUrl.fromLocalFile(":/doc/about.html"))
        except Exception as msg:
            view.setHtml(self.notfound % {'message':str(msg)})

        dlg.show()

    def cb_save_gcode(self):
        '''
        '''
        if self.job:
            jobname = os.path.basename(self.jobfilename)
            jobname = os.path.splitext(jobname)[0]

            opname = self.job.operations[0].name

            filename = "%s_%s.nc" % (jobname, opname)

            gcode = self.job.gcode

            if os.path.exists(filename):
                k = 1
                filename = "%s_%s_%d.nc" % (jobname, opname, k)
                while os.path.exists(filename):
                    k += 1
                    filename = "%s_%s_%d.nc" % (jobname, opname, k)

            fp = open(filename, "w")
            fp.write(gcode)
            fp.close()

            # status bar -> msg
            self.statusBar().showMessage("Saved GCode to \"%s\"" % filename, 3000)

    def display_gcode(self, gcode: str):
        '''
        display gcode in webgl!
        '''
        simulator_data =  {
            "gcode": gcode,
            "cutterHeight": 3 * 4.0,
            "cutterDiameter": self.ui.doubleSpinBox_Tool_Diameter.value(),
            "cutterAngle": self.ui.spinBox_Tool_Angle.value(),
        }
        
        self.webgl_viewer.set_data(simulator_data)
        self.webgl_viewer.show_gcode()

        self.gcode_textviewer.load_data(gcode)

        self.candle_viewer.loadData(gcode)

    def load_ui(self, uifile: str):
        '''
        old method th load ui, not OK when a QMainWindow ui file
        has to be loaded, OK when simple widget.
        Kept here to remember how it works (quite well infact, and
        no need to generate an Ui_XXXX.py file)
        '''
        loader = QUiLoader(self)
        loader.registerCustomWidget(operations_tableview.PyCutOperationsTableViewManager)
        loader.registerCustomWidget(tabs_tableview.PyCutTabsTableViewManager)
        
        widget = loader.load(uifile)

        return widget

    def init_gui(self):
        '''
        set the default settings in the gui 
        '''
        self.apply_settings(self.default_settings)

        #self.cb_update_tabs_display()
        #self.cb_update_tool_display()
        #self.cb_update_material_display()
        #self.cb_update_gcodeconversion_display()
    
    def get_current_settings(self):
        '''
        '''
        settings = {
            "svg": {
                "px_per_inch" : 96,
            }, 
            "Tabs": {
                "units"      : self.ui.comboBox_Tabs_Units.currentText(),
                "height"     : self.ui.doubleSpinBox_Tabs_Height.value(),
                "tabs"       : self.tabs
            },
            "Tool" : {
                "units"      : self.ui.comboBox_Tool_Units.currentText(),
                "diameter"   : self.ui.doubleSpinBox_Tool_Diameter.value(),
                "angle"      : self.ui.spinBox_Tool_Angle.value(),
                "passdepth"  : self.ui.doubleSpinBox_Tool_PassDepth.value(),
                "overlap"    : self.ui.doubleSpinBox_Tool_Overlap.value(),
                "rapid"      : self.ui.spinBox_Tool_Rapid.value(),
                "plunge"     : self.ui.spinBox_Tool_Plunge.value(),
                "cut"        : self.ui.spinBox_Tool_Cut.value()
            },
            "Material" : {
                "units"      : self.ui.comboBox_Material_Units.currentText(),
                "thickness"  : self.ui.doubleSpinBox_Material_Thickness.value(),
                "z_origin"    : self.ui.comboBox_Material_ZOrigin.currentText(),
                "clearance"  : self.ui.doubleSpinBox_Material_Clearance.value(),
            },
            "CurveToLineConversion" : {
                "minimum_segments"       : self.ui.spinBox_CurveToLineConversion_MinimumNbSegments.value(),
                "minimum_segments_length" : self.ui.doubleSpinBox_CurveToLineConversion_MinimumSegmentsLength.value(),
            },
            "GCodeConversion" : {
                "units"            : self.ui.comboBox_GCodeConversion_Units.currentText(),
                "flip_xy"          : self.ui.checkBox_GCodeConversion_FlipXY.isChecked(),
                "x_offset"         : self.ui.doubleSpinBox_GCodeConversion_XOffset.value(),
                "y_offset"         : self.ui.doubleSpinBox_GCodeConversion_YOffset.value(),
                "xy_reference"     : GcodeModel.XYRef[self.ui.buttonGroup_GCodeConversion.checkedId()]
            },
            "GCodeGeneration" : {
                "return_to_zero_at_end" : self.ui.checkBox_GCodeGeneration_ReturnToZeroAtEnd.isChecked(),
                "spindle_control"    : self.ui.checkBox_GCodeGeneration_SpindleControl.isChecked(),
                "spindle_speed"      : self.ui.spinBox_GCodeGeneration_SpindleSpeed.value(),
                "program_end"        : self.ui.checkBox_GCodeGeneration_ProgramEnd.isChecked(),
            }
        }
        
        return settings

    def apply_settings(self, settings):
        '''
        '''
        # Tabs
        self.ui.comboBox_Tabs_Units.setCurrentText(settings["Tabs"]["units"])
        self.ui.doubleSpinBox_Tabs_Height.setValue(settings["Tabs"]["height"])
            
        # Tool
        self.ui.comboBox_Tool_Units.setCurrentText(settings["Tool"]["units"])
        self.ui.doubleSpinBox_Tool_Diameter.setValue(settings["Tool"]["diameter"])
        self.ui.spinBox_Tool_Angle.setValue(settings["Tool"]["angle"])
        self.ui.doubleSpinBox_Tool_PassDepth.setValue(settings["Tool"]["passdepth"])
        self.ui.doubleSpinBox_Tool_Overlap.setValue(settings["Tool"]["overlap"])
        self.ui.spinBox_Tool_Rapid.setValue(settings["Tool"]["rapid"])
        self.ui.spinBox_Tool_Plunge.setValue(settings["Tool"]["plunge"])
        self.ui.spinBox_Tool_Cut.setValue(settings["Tool"]["cut"])
        
        # Material
        self.ui.comboBox_Material_Units.setCurrentText(settings["Material"]["units"])
        self.ui.doubleSpinBox_Material_Thickness.setValue(settings["Material"]["thickness"])
        self.ui.comboBox_Material_ZOrigin.setCurrentText(settings["Material"]["z_origin"])
        self.ui.doubleSpinBox_Material_Clearance.setValue(settings["Material"]["clearance"])
            
        # CurveToLineConversion 
        self.ui.spinBox_CurveToLineConversion_MinimumNbSegments.setValue(settings["CurveToLineConversion"]["minimum_segments"]),
        self.ui.doubleSpinBox_CurveToLineConversion_MinimumSegmentsLength.setValue(settings["CurveToLineConversion"]["minimum_segments_length"]),
            
        # GCodeConversion
        self.ui.comboBox_GCodeConversion_Units.setCurrentText(settings["GCodeConversion"]["units"])
        self.ui.checkBox_GCodeConversion_FlipXY.setChecked(settings["GCodeConversion"]["flip_xy"])
        self.ui.doubleSpinBox_GCodeConversion_XOffset.setValue(settings["GCodeConversion"]["x_offset"])
        self.ui.doubleSpinBox_GCodeConversion_YOffset.setValue(settings["GCodeConversion"]["y_offset"])
            
        if settings["GCodeConversion"]["xy_reference"] == "ZERO_TOP_LEFT_OF_MATERIAL":
            self.ui.pushButton_GCodeConversion_ZeroTopLeftOfMaterial.setChecked(True)
        elif settings["GCodeConversion"]["xy_reference"] == "ZERO_LOWER_LEFT_OF_MATERIAL":
            self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfMaterial.setChecked(True)
        elif settings["GCodeConversion"]["xy_reference"] == "ZERO_LOWER_LEFT_OF_OP":
            self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfOp.setChecked(True)
        elif settings["GCodeConversion"]["xy_reference"] == "ZERO_CENTER_OF_OP":
            self.ui.pushButton_GCodeConversion_ZeroCenterOfOp.setChecked(True)

        # GCodeGeneration 
        self.ui.checkBox_GCodeGeneration_ReturnToZeroAtEnd.setChecked(settings["GCodeGeneration"]["return_to_zero_at_end"])
        self.ui.checkBox_GCodeGeneration_SpindleControl.setChecked(settings["GCodeGeneration"]["spindle_control"])
        self.ui.spinBox_GCodeGeneration_SpindleSpeed.setValue(settings["GCodeGeneration"]["spindle_speed"])
        self.ui.checkBox_GCodeGeneration_ProgramEnd.setChecked(settings["GCodeGeneration"]["program_end"])

    def cb_open_svg(self):
        '''
        not a job, a svg only -> no operations
        '''
        xfilter = "SVG Files (*.svg)"
        svg_file, _ = QtWidgets.QFileDialog.getOpenFileName(self, caption="open file", dir=".", filter=xfilter)

        if svg_file:
            svg_file = self.minify_path(svg_file)

            self.svg_file = svg_file
            
            # clean current job (table)
            self.operations = []
            self.ui.operationsview_manager.set_operations(self.operations)

            # clean current tabs (table)
            self.tabs = []
            self.ui.tabsview_manager.set_tabs(self.tabs)
            
            self.display_svg(self.svg_file)
 
    def cb_new_job(self):
        '''
        '''
        self.svg_file = None
        self.display_svg(self.svg_file)

        # clean current job (operations table)
        self.operations = []
        self.ui.operationsview_manager.set_operations(self.operations)

        # clean current job (tabs table)
        self.tabs = []
        self.ui.tabsview_manager.set_tabs(self.tabs)

    def cb_open_recent_job_file(self):
        '''
        '''
        sender = self.sender()
        jobfilename = sender.text()

        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.disconnect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.disconnect(self.cb_generate_gcode_y_offset)
        self.ui.checkBox_GCodeConversion_FlipXY.clicked.disconnect(self.cb_generate_gcode)

        self.open_job(jobfilename)
        
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.connect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.connect(self.cb_generate_gcode_y_offset)
        self.ui.checkBox_GCodeConversion_FlipXY.clicked.connect(self.cb_generate_gcode)

    def cb_open_job(self):
        '''
        '''
        # read json
        xfilter = "JSON Files (*.json)"
        jobfilename, _ = QtWidgets.QFileDialog.getOpenFileName(self, caption="open file", dir=".", filter=xfilter)

        jobfilename = self.minify_path(jobfilename)
        
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.disconnect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.disconnect(self.cb_generate_gcode_y_offset)
        self.ui.checkBox_GCodeConversion_FlipXY.clicked.disconnect(self.cb_generate_gcode)

        self.open_job(jobfilename)
        
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.connect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.connect(self.cb_generate_gcode_y_offset)
        self.ui.checkBox_GCodeConversion_FlipXY.clicked.connect(self.cb_generate_gcode)

    def open_job(self, jobfilename: str):
        cwd = os.getcwd()

        common_prefix = [os.path.commonprefix([cwd, jobfilename])]
        jobfilename = os.path.relpath(jobfilename, common_prefix[0])

        with open(jobfilename) as f:
            self.jobfilename = jobfilename

            self.prepend_recent_jobs(jobfilename)

            job = json.load(f)
        
            self.svg_file = job["svg_file"] # relativ to job or absolute
            
            if os.path.isabs(self.svg_file):
                svg_file = self.svg_file
            else:
                if os.path.isabs(jobfilename):
                    jobdir = os.path.dirname(jobfilename)
                    svg_file = os.path.join(jobdir, self.svg_file)
                else:
                    abs_jobfilename = os.path.abspath(jobfilename)
                    abs_jobdir = os.path.dirname(abs_jobfilename)
                    svg_file = os.path.join(abs_jobdir, self.svg_file)

            if not os.path.exists(svg_file):
                msgBox = QtWidgets.QMessageBox()
                msgBox.setWindowTitle("PyCut")
                msgBox.setText("Svg File %s not found" % svg_file)
                msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
                msgBox.exec()
                return 

            self.operations = job["operations"]
            self.tabs = job["settings"]["Tabs"].get("tabs", [])
        
            # display
            self.display_svg(svg_file)
            
            # and fill the whole gui
            self.apply_settings(job["settings"])

            # fill operations table
            self.ui.operationsview_manager.set_operations(self.operations)

            # fill tabs table
            self.ui.tabsview_manager.set_tabs(self.tabs)
        
    def cb_save_job(self):
        '''
        '''
        operations = self.ui.operationsview_manager.get_operations()

        job = {
            "svg_file" : self.svg_file,
            "operations": operations,
            "settings": self.get_current_settings()
        }
        
        with open(self.jobfilename, 'w') as json_file:
            json.dump(job, json_file, indent=2)   

    def cb_save_job_as(self):
        '''
        '''
        xfilter = "JSON Files (*.json)"
        
        operations = self.ui.operationsview_manager.get_operations()

        job = {
            "svg_file" : self.svg_file,
            "operations": operations,
            "settings": self.get_current_settings()
        }
            
        # open file dialog for a file name
        jobfilename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption="Save As", dir=".", filter=xfilter)

        if jobfilename:
            jobfilename = self.minify_path(jobfilename)

            with open(jobfilename, 'w') as json_file:
                json.dump(job, json_file, indent=2)

            self.jobfilename = jobfilename
    
    def cb_curve_min_segments(self):
        '''
        what is it good for ?
        seems to be redundant with cb_curve_min_segments_length
        '''
        value = self.ui.spinBox_CurveToLineConversion_MinimumNbSegments.value()
        shapely_svgpath_io.SvgPathDiscretizer.set_arc_min_nb_segments(value)

    def cb_curve_min_segments_length(self):
        '''
        '''
        value = self.ui.doubleSpinBox_CurveToLineConversion_MinimumSegmentsLength.value()
        shapely_svgpath_io.SvgPathDiscretizer.set_arc_precision(value)

    def cb_update_tabs_display(self):
        '''
        This updates the legends of the tsbs model widget **and** the values
        '''
        tabs_units = self.ui.comboBox_Tabs_Units.currentText()
        
        if tabs_units == "inch":
            self.ui.doubleSpinBox_Tabs_Height.setValue( self.ui.doubleSpinBox_Tabs_Height.value() / 25.4 )
            self.ui.doubleSpinBox_Tabs_Height.setSingleStep(0.04)

        if tabs_units == "mm":
            self.ui.doubleSpinBox_Tabs_Height.setValue( self.ui.doubleSpinBox_Tabs_Height.value() * 25.4 )
            self.ui.doubleSpinBox_Tabs_Height.setSingleStep(1.0)

    def cb_update_tool_display(self):
        '''
        This updates the legends of the tool model widget **and** the values
        '''
        tool_units = self.ui.comboBox_Tool_Units.currentText()
        
        if tool_units == "inch":
            self.ui.label_Tool_Diameter_UnitsDescr.setText("inch")
            self.ui.label_Tool_Angle_UnitsDescr.setText("degrees")
            self.ui.label_Tool_PassDepth_UnitsDescr.setText("inch")
            self.ui.label_Tool_Overlap_UnitsDescr.setText("[0:1[")
            self.ui.label_Tool_Rapid_UnitsDescr.setText("inch/min")
            self.ui.label_Tool_Plunge_UnitsDescr.setText("inch/min")
            self.ui.label_Tool_Cut_UnitsDescr.setText("inch/min")

            self.ui.doubleSpinBox_Tool_Diameter.setValue( self.ui.doubleSpinBox_Tool_Diameter.value() / 25.4 )
            self.ui.doubleSpinBox_Tool_PassDepth.setValue( self.ui.doubleSpinBox_Tool_PassDepth.value() / 25.4 )
            self.ui.spinBox_Tool_Rapid.setValue( self.ui.spinBox_Tool_Rapid.value() / 25.4 )
            self.ui.spinBox_Tool_Plunge.setValue( self.ui.spinBox_Tool_Plunge.value() / 25.4 )
            self.ui.spinBox_Tool_Cut.setValue( self.ui.spinBox_Tool_Cut.value() / 25.4 )

        if tool_units == "mm":
            self.ui.label_Tool_Diameter_UnitsDescr.setText("mm")
            self.ui.label_Tool_Angle_UnitsDescr.setText("degrees")
            self.ui.label_Tool_PassDepth_UnitsDescr.setText("mm")
            self.ui.label_Tool_Overlap_UnitsDescr.setText("[0:1[")
            self.ui.label_Tool_Rapid_UnitsDescr.setText("mm/min")
            self.ui.label_Tool_Plunge_UnitsDescr.setText("mm/min")
            self.ui.label_Tool_Cut_UnitsDescr.setText("mm/min")

            self.ui.doubleSpinBox_Tool_Diameter.setValue( self.ui.doubleSpinBox_Tool_Diameter.value() * 25.4 )
            self.ui.doubleSpinBox_Tool_PassDepth.setValue( self.ui.doubleSpinBox_Tool_PassDepth.value() * 25.4 )
            self.ui.spinBox_Tool_Rapid.setValue( self.ui.spinBox_Tool_Rapid.value() * 25.4 )
            self.ui.spinBox_Tool_Plunge.setValue( self.ui.spinBox_Tool_Plunge.value() * 25.4 )
            self.ui.spinBox_Tool_Cut.setValue( self.ui.spinBox_Tool_Cut.value() * 25.4 )

    def cb_update_material_display(self):
        '''
        This updates the legends of the material model widget **and** the values
        '''
        material_units = self.ui.comboBox_Material_Units.currentText()
        
        if material_units == "inch":
            self.ui.doubleSpinBox_Material_Thickness.setValue( self.ui.doubleSpinBox_Material_Thickness.value() / 25.4 )
            self.ui.doubleSpinBox_Material_Clearance.setValue( self.ui.doubleSpinBox_Material_Clearance.value() / 25.4 )

            self.ui.doubleSpinBox_Material_Thickness.setSingleStep(0.04)
            self.ui.doubleSpinBox_Material_Clearance.setSingleStep(0.04)

        if material_units == "mm":
            self.ui.doubleSpinBox_Material_Thickness.setValue( self.ui.doubleSpinBox_Material_Thickness.value() * 25.4 )
            self.ui.doubleSpinBox_Material_Clearance.setValue( self.ui.doubleSpinBox_Material_Clearance.value() * 25.4 )

            self.ui.doubleSpinBox_Material_Thickness.setSingleStep(1.0)
            self.ui.doubleSpinBox_Material_Clearance.setSingleStep(1.0)

    def cb_update_gcodeconversion_display(self):
        '''
        This updates the legends of the gcode_conversion model widget **and** the values
        '''
        gcodeconversion_units = self.ui.comboBox_GCodeConversion_Units.currentText()
        
        if gcodeconversion_units == "inch":
            self.ui.label_GCodeConversion_XOffset_UnitsDescr.setText("inch")
            self.ui.label_GCodeConversion_YOffset_UnitsDescr.setText("inch")
            self.ui.label_GCodeConversion_MinX_UnitsDescr.setText("inch")
            self.ui.label_GCodeConversion_MaxX_UnitsDescr.setText("inch")
            self.ui.label_GCodeConversion_MinY_UnitsDescr.setText("inch")
            self.ui.label_GCodeConversion_MaxY_UnitsDescr.setText("inch")

            self.ui.doubleSpinBox_GCodeConversion_XOffset.setValue( self.ui.doubleSpinBox_GCodeConversion_XOffset.value() / 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_YOffset.setValue(self.ui.doubleSpinBox_GCodeConversion_YOffset.value() / 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MinX.setValue(self.ui.doubleSpinBox_GCodeConversion_MinX.value() / 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MaxX.setValue(self.ui.doubleSpinBox_GCodeConversion_MaxX.value() / 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MinY.setValue(self.ui.doubleSpinBox_GCodeConversion_MinY.value() / 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MaxY.setValue(self.ui.doubleSpinBox_GCodeConversion_MaxY.value() / 25.4 )
            
        if gcodeconversion_units == "mm":
            self.ui.label_GCodeConversion_XOffset_UnitsDescr.setText("mm")
            self.ui.label_GCodeConversion_YOffset_UnitsDescr.setText("mm")
            self.ui.label_GCodeConversion_MinX_UnitsDescr.setText("mm")
            self.ui.label_GCodeConversion_MaxX_UnitsDescr.setText("mm")
            self.ui.label_GCodeConversion_MinY_UnitsDescr.setText("mm")
            self.ui.label_GCodeConversion_MaxY_UnitsDescr.setText("mm")

            self.ui.doubleSpinBox_GCodeConversion_XOffset.setValue( self.ui.doubleSpinBox_GCodeConversion_XOffset.value() * 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_YOffset.setValue(self.ui.doubleSpinBox_GCodeConversion_YOffset.value() * 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MinX.setValue(self.ui.doubleSpinBox_GCodeConversion_MinX.value() * 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MaxX.setValue(self.ui.doubleSpinBox_GCodeConversion_MaxX.value() * 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MinY.setValue(self.ui.doubleSpinBox_GCodeConversion_MinY.value() * 25.4 )
            self.ui.doubleSpinBox_GCodeConversion_MaxY.setValue(self.ui.doubleSpinBox_GCodeConversion_MaxY.value() * 25.4 )
            
    def cb_display_material_thickness(self):
        '''
        svg display only in mm
        '''
        material_units = self.ui.comboBox_Material_Units.currentText()

        thickness = ValWithUnit(self.ui.doubleSpinBox_Material_Thickness.value(), material_units).toMm()
        clearance = ValWithUnit(self.ui.doubleSpinBox_Material_Clearance.value(), material_units).toMm()

        self.svg_material_viewer.display_unit(material_units)
        self.svg_material_viewer.display_material(thickness=thickness, clearance=clearance)

    def cb_display_material_clearance(self):
        '''
        svg display only in mm
        '''
        material_units = self.ui.comboBox_Material_Units.currentText()

        thickness = ValWithUnit(self.ui.doubleSpinBox_Material_Thickness.value(), material_units).toMm()
        clearance = ValWithUnit(self.ui.doubleSpinBox_Material_Clearance.value(), material_units).toMm()

        self.svg_material_viewer.display_material(thickness=thickness, clearance=clearance)

    def cb_spindle_control(self):
        val = self.ui.checkBox_GCodeGeneration_SpindleControl.isChecked()
        self.ui.spinBox_GCodeGeneration_SpindleSpeed.setEnabled(val)

    def setup_material_viewer(self):
        '''
        '''
        return material_widget.MaterialWidget(self.ui.widget_display_material)

    def setup_svg_viewer(self):
        '''
        '''
        svg = self.ui.svg
        layout = svg.layout()
        
        svg_viewer = svgviewer.SvgViewer(svg)
        svg_viewer.set_mainwindow(self)
        
        layout.addWidget(svg_viewer)
        layout.setStretch(0, 1)
        
        return svg_viewer

    def setup_candle_viewer(self):
        '''
        '''
        viewer = self.ui.viewer
        layout = viewer.layout()
        
        candle_viewer = glwidget_container.GLWidgetContainer(viewer)

        layout.addWidget(candle_viewer)
        layout.setStretch(0, 1)
        
        return candle_viewer

    def setup_webgl_viewer(self):
        '''
        '''
        simulator = self.ui.simulator
        layout = simulator.layout()
        
        self.webgl_viewer = webglviewer.WebGlViewer(simulator)
        self.gcode_textviewer = gcodefileviewer.GCodeFileViewer(simulator, self.webgl_viewer)

        self.webgl_viewer.simtime_received_from_js.connect(self.gcode_textviewer.on_simtime_from_js)

        layout.addWidget(self.webgl_viewer)
        layout.addWidget(self.gcode_textviewer)
        layout.setStretch(0, 1)
        layout.setStretch(1, 0)
        
        return self.webgl_viewer

    def display_svg(self, svg_file):
        '''
        '''
        self.svg_viewer.clean()

        if svg_file is None:
            
            svg = '''<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
                width="1091" height="490"
                viewBox="0 0 1091 490"
                version="1.1">
                <g><image href="logo.png" id="splash_screen"/></g>
             </svg>'''
            self.svg_viewer.set_svg(svg)
        else:
            fp = open(svg_file, "r")
            svg = fp.read()
            fp.close()

            # extract dimension of material as global variables in the SvgModel
            size_xstr, size_ystr = svgviewer.extract_svg_dimensions(svg)

            suffix = ""
            
            if "mm" in size_xstr:
                suffix = "mm"
                size_x, size_y = float(size_xstr.split("mm")[0]), float(size_ystr.split("mm")[0])
            elif "in" in size_xstr:
                suffix = "in"
                size_x, size_y = float(size_xstr.split("in")[0]), float(size_ystr.split("in")[0])
            else:
                size_x, size_y = float(size_xstr), float(size_ystr)

            self.ui.doubleSpinBox_SvgModelWidth.setValue(size_x)
            self.ui.doubleSpinBox_SvgModelHeight.setValue(size_y)

            self.ui.doubleSpinBox_SvgModelWidth.setSuffix(suffix)
            self.ui.doubleSpinBox_SvgModelHeight.setSuffix(suffix)

            SvgModel.size_x = size_x
            SvgModel.size_y = size_y

            self.svg_viewer.set_svg(svg)
            # and the tabs if any
            self.svg_viewer.set_tabs(self.tabs)

    def assign_tabs(self, tabs: List[Tab]):
        '''
        '''
        self.tabs = tabs
        self.ui.tabsview_manager.set_tabs(self.tabs)
    
    def display_cnc_tabs(self, tabs: List[Tab]):
        '''
        '''
        self.tabs = tabs
        self.svg_viewer.set_tabs(self.tabs)

    def cb_tabs_hide_disabled(self):
        val = self.ui.checkBox_Tabs_hideDisabledTabs.isChecked()
        self.svg_viewer.SVGVIEWER_HIDE_TABS_DISABLED = val
        self.svg_viewer.reinit()

    def cb_tabs_hide_all(self):
        val = self.ui.checkBox_Tabs_hideAllTabs.isChecked()
        self.svg_viewer.SVGVIEWER_HIDE_TABS_ALL = val
        self.svg_viewer.reinit()

    def display_cnc_ops_geometry(self, operations: List[operations_tableview.OpItem]):
        '''
        '''
        settings = self.get_current_settings()

        tool_model = ToolModel() 
        tool_model.units = settings["Tool"]["units"]
        tool_model.diameter = ValWithUnit(settings["Tool"]["diameter"], tool_model.units)
        tool_model.angle = settings["Tool"]["angle"]
        tool_model.passdepth = ValWithUnit(settings["Tool"]["passdepth"], tool_model.units)
        tool_model.overlap = settings["Tool"]["overlap"]
        tool_model.rapidRate = ValWithUnit(settings["Tool"]["rapid"], tool_model.units)
        tool_model.plungeRate = ValWithUnit(settings["Tool"]["plunge"], tool_model.units)
        tool_model.cutRate = ValWithUnit(settings["Tool"]["cut"], tool_model.units)

        cnc_ops = []

        for op_model in operations:
            if not op_model.enabled:
                continue

            cnc_op = CncOp(
            {
                "units": op_model.units,
                "name": op_model.name,
                "paths": op_model.paths,
                "combinaison": op_model.combinaison,
                "ramp_plunge": op_model.ramp_plunge,
                "type": op_model.cam_op,
                "direction": op_model.direction,
                "cut_depth": op_model.cut_depth,
                "margin": op_model.margin,
                "width": op_model.width,

                "enabled": op_model.enabled
            })

            cnc_ops.append(cnc_op)

        
        for cnc_op in cnc_ops:
            cnc_op.setup(self.svg_viewer)
            cnc_op.calculate_geometry(tool_model)

        self.svg_viewer.reinit()
        self.svg_viewer.display_job_geometry(cnc_ops)

    def get_jobmodel_operations(self) -> List[CncOp]:
        '''
        '''
        cnc_ops : List[CncOp] = []

        for op_model in self.ui.operationsview_manager.get_model_operations():
            if not op_model.enabled:
                continue

            cnc_op = CncOp(
            {
                "units": op_model.units,
                "name": op_model.name,
                "paths": op_model.paths,
                "combinaison": op_model.combinaison,
                "ramp_plunge": op_model.ramp_plunge,
                "type": op_model.cam_op,
                "direction": op_model.direction,
                "cut_depth": op_model.cut_depth,
                "margin": op_model.margin,
                "width": op_model.width,

                "enabled": op_model.enabled
            })

            cnc_ops.append(cnc_op)

        return cnc_ops

    def get_jobmodel(self) -> JobModel:
        '''
        '''
        settings = self.get_current_settings()

        svg_model = SvgModel()
        svg_model.pxPerInch = 96
        material_model = MaterialModel()
        material_model.mat_units = settings["Material"]["units"]
        material_model.mat_thickness = ValWithUnit(settings["Material"]["thickness"], material_model.mat_units)
        material_model.mat_z_origin = settings["Material"]["z_origin"]
        material_model.mat_clearance = ValWithUnit(settings["Material"]["clearance"], material_model.mat_units)
        # the SVG dimensions
        material_model.set_material_size_x(self.svg_viewer.get_svg_size_x())
        material_model.set_material_size_y(self.svg_viewer.get_svg_size_y())

        tool_model = ToolModel()
        tool_model.units = settings["Tool"]["units"]
        tool_model.diameter = ValWithUnit(settings["Tool"]["diameter"], tool_model.units)
        tool_model.angle = settings["Tool"]["angle"]
        tool_model.passdepth = ValWithUnit(settings["Tool"]["passdepth"], tool_model.units)
        tool_model.overlap = settings["Tool"]["overlap"]
        tool_model.rapidRate = ValWithUnit(settings["Tool"]["rapid"], tool_model.units)
        tool_model.plungeRate = ValWithUnit(settings["Tool"]["plunge"], tool_model.units)
        tool_model.cutRate = ValWithUnit(settings["Tool"]["cut"], tool_model.units)
        
        tabsmodel = TabsModel([tab for tab in self.tabs if tab["enabled"] == True])
        tabsmodel.units = settings["Tabs"]["units"]
        tabsmodel.height = ValWithUnit(settings["Tabs"]["height"], tabsmodel.units)

        gcode_model = GcodeModel()
        gcode_model.units = settings["GCodeConversion"]["units"]
        gcode_model.flipXY = settings["GCodeConversion"]["flip_xy"]
        gcode_model.XOffset = settings["GCodeConversion"]["x_offset"]
        gcode_model.YOffset = settings["GCodeConversion"]["y_offset"]
        gcode_model.returnTo00 = settings["GCodeGeneration"]["return_to_zero_at_end"]
        gcode_model.spindleControl = settings["GCodeGeneration"]["spindle_control"]
        gcode_model.spindleSpeed = settings["GCodeGeneration"]["spindle_speed"]
        gcode_model.programEnd = settings["GCodeGeneration"]["program_end"]
        
        gcode_model.gcodeZero = GcodeModel.ZERO_TOP_LEFT_OF_MATERIAL
        if self.ui.pushButton_GCodeConversion_ZeroTopLeftOfMaterial.isChecked():
            gcode_model.gcodeZero = GcodeModel.ZERO_TOP_LEFT_OF_MATERIAL
        if self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfMaterial.isChecked():
            gcode_model.gcodeZero = GcodeModel.ZERO_LOWER_LEFT_OF_MATERIAL
        if self.ui.pushButton_GCodeConversion_ZeroLowerLeftOfOp.isChecked():
            gcode_model.gcodeZero = GcodeModel.ZERO_LOWER_LEFT_OF_OP
        if self.ui.pushButton_GCodeConversion_ZeroCenterOfOp.isChecked():
            gcode_model.gcodeZero = GcodeModel.ZERO_CENTER_OF_OP

        cnc_ops = self.get_jobmodel_operations()

        job = JobModel(self.svg_viewer, cnc_ops, material_model, svg_model, tool_model, tabsmodel, gcode_model)

        return job  

    def cb_generate_gcode(self):
        '''
        '''
        self.job = job = self.get_jobmodel()

        ok = self.jobmodel_check_operations()
        if not ok:
            return

        ok = self.jobmodel_check_toolpaths()
        if not ok:
            return

        generator = GcodeGenerator(job)
        generator.generateGcode()

        self.after_gcode_generation(generator)

    def cb_generate_gcode_x_offset(self):
        '''
        '''
        self.job = job = self.get_jobmodel()

        ok = self.jobmodel_check_toolpaths()
        if not ok:
            return

        generator = GcodeGenerator(job)
        generator.setXOffset(self.ui.doubleSpinBox_GCodeConversion_XOffset.value())
        #generator.generateGcode()

        self.after_gcode_generation(generator)

    def cb_generate_gcode_y_offset(self):
        '''
        '''
        self.job = job = self.get_jobmodel()

        ok = self.jobmodel_check_toolpaths()
        if not ok:
            return

        generator = GcodeGenerator(job)
        generator.setYOffset(self.ui.doubleSpinBox_GCodeConversion_YOffset.value())
        #generator.generateGcode()

        self.after_gcode_generation(generator)

    def jobmodel_check_operations(self):
        '''
        '''
        has_operations = len(self.job.operations) > 0

        if not has_operations:
            # alert
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle("PyCut")
            msgBox.setText("The Job has no operations!")
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
            msgBox.exec()
            
        return has_operations

    def jobmodel_check_toolpaths(self):
        '''
        '''
        has_toolpaths = False
        for op in self.job.operations:
            if len(op.cam_paths) > 0:
                has_toolpaths = True

        if not has_toolpaths:
            # alert
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle("PyCut")
            msgBox.setText("The Job has no toolpaths!")
            msgBox.setInformativeText("Maybe is the geometry too narrow for the cutter?")
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
            msgBox.exec()
            
        return has_toolpaths

    def after_gcode_generation(self, generator: GcodeGenerator):
        '''
        '''
        # with the resulting calculation, we can fill the min/max in X/Y as well as the offsets
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.disconnect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.disconnect(self.cb_generate_gcode_y_offset)

        self.ui.doubleSpinBox_GCodeConversion_XOffset.setValue(generator.offsetX)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.setValue(generator.offsetY)
        
        self.ui.doubleSpinBox_GCodeConversion_XOffset.valueChanged.connect(self.cb_generate_gcode_x_offset)
        self.ui.doubleSpinBox_GCodeConversion_YOffset.valueChanged.connect(self.cb_generate_gcode_y_offset)

        self.ui.doubleSpinBox_GCodeConversion_MinX.setValue(generator.minX)
        self.ui.doubleSpinBox_GCodeConversion_MinY.setValue(generator.minY)
        self.ui.doubleSpinBox_GCodeConversion_MaxX.setValue(generator.maxX)
        self.ui.doubleSpinBox_GCodeConversion_MaxY.setValue(generator.maxY)

        self.svg_viewer.display_job_toolpaths(generator.job.operations)
        
        # gcode viewer/simulator
        gcode = generator.gcode
        self.display_gcode(gcode)

    def read_recent_jobs(self):
        '''
        Returns the list of recent jobs fron the setting file
        '''
        self.recent_jobs = []

        if not os.path.exists("./recent_jobs.json"):
            fp = open("./recent_jobs.json", "w")
            json.dump([], fp, indent=2)  
            fp.close()

        with open("./recent_jobs.json", "r") as f:
            self.recent_jobs = json.load(f)

        return self.recent_jobs

    def write_recent_jobs(self):
        '''
        Write the list of recent jobs to the settings file
        '''
        with open("./recent_jobs.json", 'w') as json_file:
            json.dump(self.recent_jobs, json_file, indent=2)   

    def prepend_recent_jobs(self, jobfile):
        '''
        '''
        # consider unix style if not absolute
        if not os.path.isabs(jobfile):
            jobfile_unix = jobfile.replace(ntpath.sep, posixpath.sep)
        else:
            jobfile_unix = jobfile

        if jobfile_unix.startswith("./"):
            jobfile_unix = jobfile_unix[2:]

        # remove duplicated
        if jobfile_unix in self.recent_jobs:
            self.recent_jobs.remove(jobfile_unix)

        self.recent_jobs.insert(0, jobfile_unix)

        self.recent_jobs = self.recent_jobs[:5]

    def closeEvent(self, event):
        # do stuff
        self.write_recent_jobs()
        event.accept() # let the window close

    def build_recent_jobs_submenu(self):
        '''
        '''
        for jobfilename in self.recent_jobs:
            icon = QtGui.QIcon.fromTheme("edit-paste")
            item = QtGui.QAction(icon, jobfilename, self.ui.menuOpen_Recent_Jobs)
            item.triggered.connect(self.cb_open_recent_job_file)
            self.ui.menuOpen_Recent_Jobs.addAction(item)

    def minify_path(self, apath):
        '''
        '''
        cwd = os.getcwd()
        cwd = pathlib.PurePath(cwd).as_posix()

        if apath.startswith(cwd):
            apath = apath.split(cwd)[1]
            apath = apath[1:]  # remove the leading slash

        return apath


def main():
    parser = argparse.ArgumentParser(prog="PyCut", description="PyCut CAM program - Read the doc!")

    # argument
    parser.add_argument('job', nargs='?', default=None, help="load job file | empty")

    # version info
    parser.add_argument("--version", action='version', version='%s' % VERSION)

    options = parser.parse_args()

    app = QtWidgets.QApplication([])
    app.setApplicationName("PyCut")

    mainwindow = PyCutMainWindow(options)
    mainwindow.show()
    sys.exit(app.exec())

def main_profiled():
    """
    """
    import profile
    import pstats

    outfile = 'prof_pycut.bin'

    profile.run("main()", filename=outfile)
    p = pstats.Stats(outfile)

    # 1.
    p.sort_stats('cumulative')
    p.print_stats(100) # p.print_stats(50)

    # 2.
    p.sort_stats('time')
    p.print_stats(100) # p.print_stats(50)

    # 3.
    p.sort_stats('time', 'cumulative').print_stats(.5) # (.5, 'init')


if __name__ =='__main__':
    '''
    python -m cProfile -o test_parser.prof test_parser.py
    '''
    filename = "pycut_cnc_all_letters_op.nc"

    main()
    #main_profiled()
