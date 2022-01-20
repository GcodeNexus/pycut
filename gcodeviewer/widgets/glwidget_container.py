
from typing import List

from PySide6.QtCore import QElapsedTimer
from PySide6.QtCore import QTime
from PySide6.QtCore import Qt
from PySide6.QtCore import QFile
from PySide6.QtCore import QTextStream
from PySide6.QtCore import QIODevice
from PySide6.QtCore import qIsNaN

from PySide6.QtGui import QVector3D

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from PySide6.QtWidgets import QProgressDialog, QTableView
from PySide6.QtWidgets import QMessageBox
from PySide6.QtWidgets import QApplication

from gcodeviewer.drawers.gcodedrawer import GcodeDrawer
from gcodeviewer.drawers.origindrawer import OriginDrawer
from gcodeviewer.drawers.tooldrawer import ToolDrawer
from gcodeviewer.drawers.selectiondrawer import SelectionDrawer

from gcodeviewer.parser.gcodeviewparse import GcodeViewParse 
from gcodeviewer.parser.gcodepreprocessorutils import  GcodePreprocessorUtils  
from gcodeviewer.parser.gcodeparser import  GcodeParser 

from gcodeviewer.tables.gcodetablemodel import GCodeItem
from gcodeviewer.tables.gcodetablemodel import GCodeTableModel

from gcodeviewer.parser.linesegment import LineSegment

from gcodeviewer.util.util import qQNaN

from gcodeviewer.widgets.glwidget import GLWidget

sNan = float('NaN')

PROGRESSMINLINES = 10000
PROGRESSSTEP     =  1000


class GLWidgetContainer(QtWidgets.QWidget):
    '''
    '''
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.setHandleWidth(6)

        self.glwVisualizer = GLWidget(self.splitter)
        self.tblProgram = QTableView(self.splitter)

        # table properties
        self.tblProgram.setObjectName(u"tblProgram")
        font = QtGui.QFont()
        font.setPointSize(9)
        self.tblProgram.setFont(font)
        self.tblProgram.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tblProgram.setEditTriggers(QtWidgets.QAbstractItemView.AnyKeyPressed|QtWidgets.QAbstractItemView.DoubleClicked|QtWidgets.QAbstractItemView.EditKeyPressed|QtWidgets.QAbstractItemView.SelectedClicked)
        self.tblProgram.setSelectionMode(QtWidgets.QAbstractItemView.ContiguousSelection)
        self.tblProgram.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblProgram.setGridStyle(Qt.DashLine)
        self.tblProgram.horizontalHeader().setMinimumSectionSize(50)
        self.tblProgram.horizontalHeader().setHighlightSections(False)
        self.tblProgram.verticalHeader().setVisible(False)
        #self.tblProgram.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        #self.tblProgram.verticalHeader().setDefaultSectionSize(12)
        self.tblProgram.setStyleSheet("background-color: rgb(255,255,255); gridline-color: rgb(255,255,255);" )

        self.splitter.addWidget(self.glwVisualizer)
        self.splitter.addWidget(self.tblProgram)

        self.glwVisualizer.setMinimumHeight(100)
        self.tblProgram.setMinimumHeight(100)
        
        self.setLayout(QtWidgets.QVBoxLayout())

        layout = self.layout()

        layout.addWidget(self.splitter)



        self.m_programFileName = None

        self.m_viewParser = GcodeViewParse()
        self.m_programModel = GCodeTableModel()

        self.m_codeDrawer = GcodeDrawer()
        self.m_codeDrawer.setViewParser(self.m_viewParser)
        self.m_codeDrawer.update()

        self.m_originDrawer = OriginDrawer()
        self.m_originDrawer.setLineWidth(2.0)
        self.m_originDrawer.update()

        self.m_toolDrawer = ToolDrawer()
        self.m_toolDrawer.setToolPosition(QVector3D(0, 0, 0))
        self.m_toolDrawer.update()

        self.m_selectionDrawer = SelectionDrawer()
        self.m_selectionDrawer.update()



        self.glwVisualizer.addDrawable(self.m_originDrawer)
        self.glwVisualizer.addDrawable(self.m_codeDrawer)
        #self.glwVisualizer.addDrawable(self.m_probeDrawer)
        self.glwVisualizer.addDrawable(self.m_toolDrawer)
        self.glwVisualizer.addDrawable(self.m_selectionDrawer)
        #self.glwVisualizer.addDrawable(self.m_heightMapBorderDrawer)
        #self.glwVisualizer.addDrawable(self.m_heightMapGridDrawer)
        #self.glwVisualizer.addDrawable(self.m_heightMapInterpolationDrawer)
        
        self.glwVisualizer.fitDrawable()

        self.m_programModel.dataChanged.connect(self.onTableCellChanged)

        self.tblProgram.setModel(self.m_programModel)
        self.tblProgram.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.tblProgram.verticalScrollBar().actionTriggered.connect(self.onScroolBarAction)
        self.tblProgram.selectionModel().currentChanged.connect(self.onTableCurrentChanged)    

        self.tblProgram.hideColumn(2)
        self.tblProgram.hideColumn(3)
        self.tblProgram.hideColumn(4)
        self.tblProgram.hideColumn(5)
    
        self.clearTable()

    def loadFile(self, fileName):
        file = QFile(fileName)

        if not file.open(QIODevice.ReadOnly):
            QMessageBox.critical(self, self.windowTitle(), "Can't open file:\n" + fileName)
            return

        # Set filename
        self.m_programFileName = fileName

        # Prepare text stream
        textStream = QTextStream(file)

        # Read lines
        data = []
        while not textStream.atEnd():
            data.append(textStream.readLine())

        # Load lines
        self.loadData(data)

    def loadData(self, data: List[str]):
        time = QElapsedTimer()
        time.start()

        # Reset tables
        self.clearTable()
        #self.m_probeModel.clear()
        #self.m_programHeightmapModel.clear()
        self.m_currentModel = self.m_programModel

        # Reset parsers
        self.m_viewParser.reset()
        #self.m_probeParser.reset()

        # Reset code drawer
        self.m_currentDrawer = self.m_codeDrawer
        self.m_codeDrawer.update()
        self.glwVisualizer.fitDrawable(self.m_codeDrawer)
        self.updateProgramEstimatedTime([])

        # Update interface
        #self.chkHeightMapUse.setChecked(False)
        #self.grpHeightMap.setProperty("overrided", False)
        #self.style().unpolish(self.grpHeightMap)
        #self.grpHeightMap.ensurePolished()

        # Reset tableview
        headerState = self.tblProgram.horizontalHeader().saveState()
        self.tblProgram.setModel(None)

        # Prepare parser
        gp = GcodeParser()
        ####gp.setTraverseSpeed(self.m_settings.rapidSpeed())
        gp.setTraverseSpeed(100)

        if self.m_codeDrawer.getIgnoreZ(): 
            gp.reset(QVector3D(qQNaN(), qQNaN(), 0))

        print("Prepared to load: %s" % time.elapsed())
        time.start()

        # Block parser updates on table changes
        self.m_programLoading = True

        # Prepare model
        self.m_programModel.m_data.clear()
        self.m_programModel.m_data = []

        progress = QProgressDialog ("Parsing GCode...", "Abort", 0, len(data), self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setFixedSize(progress.sizeHint())
        if len(data) > PROGRESSMINLINES:
            progress.show()
            progress.setStyleSheet("QProgressBar {text-align: center qproperty-format: \"\"}")

        while len(data) > 0:
    
            command = data.pop(0)

            # Trim command
            trimmed = command.strip()

            if len(trimmed) > 0:
                # Split command
                stripped = GcodePreprocessorUtils.removeComment(command)
                args = GcodePreprocessorUtils.splitCommand(stripped)

                gp.addCommand(args)

                item = GCodeItem()

                item.command = trimmed
                item.state = GCodeItem.States.InQueue
                item.line = gp.getCommandNumber()
                item.args = args

                self.m_programModel.m_data.append(item)

            if progress.isVisible() and (len(data) % PROGRESSSTEP == 0) :
                progress.setValue(progress.maximum() - len(data))
                QApplication.instance().processEvents()
                if progress.wasCanceled() :
                    break
            
        progress.close()

        self.m_programModel.insertRow(self.m_programModel.rowCount())
        print("model filled: %s ms." % time.elapsed())

        time.start()

        arcPrecision = 0.0 # TODO self.m_settings.arcPrecision()
        arcDegreeMode = True # TODO self.m_settings.arcDegreeMode()

        all_lines = self.m_viewParser.getLinesFromParser(gp, arcPrecision, arcDegreeMode)

        self.updateProgramEstimatedTime(all_lines)
        print("view parser filled: %s ms" % time.elapsed())

        self.m_programLoading = False

        # Set table model
        self.tblProgram.setModel(self.m_programModel)
        self.tblProgram.horizontalHeader().restoreState(headerState)

        # connect this model
        self.tblProgram.selectionModel().currentChanged.connect(self.onTableCurrentChanged) 

        # Update tableview
        self.tblProgram.selectRow(0)

        # Update code drawer
        self.m_codeDrawer.update()
        self.glwVisualizer.fitDrawable(self.m_codeDrawer)

        #self.resetHeightmap()
        #self.updateControlsState()

        self.update()

    def clearTable(self):
        self.m_programModel.clear()
        self.m_programModel.insertRow(0)

    def updateProgramEstimatedTime(self, lines: List[LineSegment]) -> QTime:
        time = 0

        for ls in lines:
            length = (ls.getEnd() - ls.getStart()).length()

            if not qIsNaN(length) and not qIsNaN(ls.getSpeed()) and ls.getSpeed() != 0 :
                speed = ls.getSpeed()
                
                '''
                cond1 = self.slbFeedOverride.isChecked() and not ls.isFastTraverse()
                cond2 = self.slbRapidOverride.isChecked() and ls.isFastTraverse()
                
                val1 = speed * self.slbFeedOverride.value() / 100.0
                val2 = speed * self.slbRapidOverride.value() / 100.0
                
                if cond1:
                    speed = val1
                elif cond2:
                    speed = val2
                '''
                time += length / speed

        time *= 60

        t = QTime()

        t.setHMS(0, 0, 0)
        t = t.addSecs(time)

        self.glwVisualizer.setSpendTime(QTime(0, 0, 0))
        self.glwVisualizer.setEstimatedTime(t)

        return t

    def onScroolBarAction(self):
        '''
        '''
        pass 
    
    def onTableCurrentChanged(self, idx1: QtCore.QModelIndex, idx2: QtCore.QModelIndex) :
        # Update toolpath hightlighting
        if idx1.row() > self.m_currentModel.rowCount() - 2:
            idx1 = self.m_currentModel.index(self.m_currentModel.rowCount() - 2, 0)
        if idx2.row() > self.m_currentModel.rowCount() - 2:
            idx2 = self.m_currentModel.index(self.m_currentModel.rowCount() - 2, 0)

        parser = self.m_currentDrawer.viewParser()
        list = parser.getLineSegmentList()
        lineIndexes = parser.getLinesIndexes()

        # Update linesegments on cell changed
        if not self.m_currentDrawer.geometryUpdated():
            for i in range(len(list)):
                jdx1 = list[i].getLineNumber()
                jdx2 = int(self.m_currentModel.data(self.m_currentModel.index(idx1.row(), 4)))
                list[i].setIsHightlight(jdx1 <= jdx2)
            
        # Update vertices on current cell changed
        else:
            lineFirst = int(self.m_currentModel.data(self.m_currentModel.index(idx1.row(), 4)))
            lineLast = int(self.m_currentModel.data(self.m_currentModel.index(idx2.row(), 4)))
            if lineLast < lineFirst:
                lineLast, lineFirst = lineFirst, lineLast

            indexes = []
            for i in range(lineFirst + 1, lineLast+1):
                for l in  lineIndexes[i]:
                    list[l].setIsHightlight(idx1.row() > idx2.row())
                    indexes.append(l)

            if len(indexes) == 0:
                self.m_selectionDrawer.setEndPosition(QVector3D(sNan, sNan, sNan))
            else:
                if self.m_codeDrawer.getIgnoreZ():
                    self.m_selectionDrawer.setEndPosition(QVector3D( \
                        list[indexes[-1]].getEnd().x(), \
                        list[indexes[-1]].getEnd().y(), \
                        0))
                else:
                    self.m_selectionDrawer.setEndPosition(list[indexes[-1]].getEnd())
            self.m_selectionDrawer.update()

            if len(indexes) > 0:
                self.m_currentDrawer.update_indexes(indexes)
        
        # Update selection marker
        
        line = int(self.m_currentModel.data(self.m_currentModel.index(idx1.row(), 4)))
        if line > 0 and lineIndexes[line] != "":
            pos = list[lineIndexes[line][-1]].getEnd()
            if self.m_codeDrawer.getIgnoreZ():
                self.m_selectionDrawer.setEndPosition(QVector3D(pos.x(), pos.y(), 0))
            else:
                self.m_selectionDrawer.setEndPosition(pos)

            # >>>> PYCUT: and position the tool at the current position
            self.m_toolDrawer.setToolPosition(pos)
            self.m_toolDrawer.update()
            # >>>> PYCUT: and position the tool at the current position

        else:
            self.m_selectionDrawer.setEndPosition(QVector3D(sNan, sNan, sNan))
        
        self.m_selectionDrawer.update()

    def onTableCellChanged(self, i1: QtCore.QModelIndex, i2: QtCore.QModelIndex):

        model : GCodeTableModel = self.sender()

        if i1.column() != 1:
            return

        # Inserting new line at end
        if i1.row() == (model.rowCount() - 1) and str(model.data(model.index(i1.row(), 1))) != "":
            model.setData(model.index(model.rowCount() - 1, 2), GCodeItem.States.InQueue)
            model.insertRow(model.rowCount())
            
            if not self.m_programLoading:
                self.tblProgram.setCurrentIndex(model.index(i1.row() + 1, 1))
        # Remove last line
        '''elif (i1.row() != (model.rowCount() - 1) and str(model.data(model.index(i1.row(), 1))) == "": 
            self.tblProgram.setCurrentIndex(model.index(i1.row() + 1, 1))
            self.m_tableModel.removeRow(i1.row())
        '''

        if not self.m_programLoading:

            # Clear cached args
            model.setData(model.index(i1.row(), 5), None)

            # Drop heightmap cache
            #if self.m_currentModel == self.m_programModel:
            #    self.m_programHeightmapModel.clear()

            # Update visualizer
            self.updateParser()

            # Hightlight w/o current cell changed event (double hightlight on current cell changed)
            alist = self.m_viewParser.getLineSegmentList()
            
            #for (int i = 0 i < list.count() and list[i].getLineNumber() <= m_currentModel.data(m_currentModel.index(i1.row(), 4)).toInt() i++):
            #    alist[i].setIsHightlight(True)

            k = 0
            while True:
                if not (k < len(alist) and alist[k].getLineNumber() <= (int)(self.m_currentModel.data(self.m_currentModel.index(i1.row(), 4)))):
                    break

                alist[k].setIsHightlight(True)

                k += 1

    def updateParser(self):
        '''
        rapidSpeed set to 100  --- in Candle: set "rapidSpeed" settings
        '''

        time = QElapsedTimer()

        print("updating parser:")
        time.start()

        parser = self.m_currentDrawer.viewParser()

        gp = GcodeParser()
        #gp.setTraverseSpeed(m_settings.rapidSpeed())
        gp.setTraverseSpeed(100)
        if self.m_codeDrawer.getIgnoreZ():
            gp.reset(QVector3D(qQNaN(), qQNaN(), 0))

        self.tblProgram.setUpdatesEnabled(False)

        progress = QProgressDialog("Updating...", "Abort", 0, self.m_currentModel.rowCount() - 2, self)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setFixedSize(progress.sizeHint())

        if self.m_currentModel.rowCount() > PROGRESSMINLINES:
            progress.show()
            progress.setStyleSheet("QProgressBar {text-align: center qproperty-format: \"\"}")

        for i in range(self.m_currentModel.rowCount()):
            # Get stored args
            args = self.m_currentModel.m_data[i].args

            # Store args if none
            if len(args) == 0: 
                stripped = GcodePreprocessorUtils.removeComment(self.m_currentModel.m_data[i].command)
                args = GcodePreprocessorUtils.splitCommand(stripped)
                self.m_currentModel.m_data[i].args = args

            # Add command to parser
            gp.addCommand(args)

            # Update table model
            self.m_currentModel.m_data[i].state = GCodeItem.States.InQueue
            self.m_currentModel.m_data[i].response = ""
            self.m_currentModel.m_data[i].line = gp.getCommandNumber()

            if progress.isVisible() and (i % PROGRESSSTEP == 0):
                progress.setValue(i)
                QApplication.instance().processEvents()
                if progress.wasCanceled():
                    break
        
        progress.close()

        self.tblProgram.setUpdatesEnabled(True)

        parser.reset()

        arcPrecision = 0.0 # TODO self.m_settings.arcPrecision()
        arcDegreeMode = True # TODO self.m_settings.arcDegreeMode()
        
        all_lines = parser.getLinesFromParser(gp, arcPrecision, arcDegreeMode)
        
        self.updateProgramEstimatedTime(all_lines)

        self.m_currentDrawer.update()
        self.glwVisualizer.updateExtremes(self.m_currentDrawer)
        #self.updateControlsState()

        if self.m_currentModel == self.m_programModel:
            self.m_fileChanged = True

        print("Update parser time: %s" % time.elapsed())
