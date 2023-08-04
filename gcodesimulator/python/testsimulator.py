
import sys

from PySide6 import QtWidgets

import gcodesimulator.python.widgets.gcodesimulator as gcodesimulator
import resources_rc


class TestMainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(TestMainWindow, self).__init__()

        self.setWindowTitle("Test GL")

        simulator = gcodesimulator.GCODESimulator(self)
        simulator.loadFile("jscut.gcode")

        self.setCentralWidget(simulator)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    mainwindow = TestMainWindow()
    mainwindow.show()
    sys.exit(app.exec())