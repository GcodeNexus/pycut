# This Python file uses the following encoding: utf-8

from typing import List

import math

from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

from PySide6 import QtSvg
from PySide6 import QtSvgWidgets

import lxml.etree as ET

import svgpathutils

# https://stackoverflow.com/questions/53288926/qgraphicssvgitem-event-propagation-interactive-svg-viewer

class SvgItem(QtSvgWidgets.QGraphicsSvgItem):
    def __init__(self, id, renderer, parent=None):
        super(SvgItem, self).__init__(parent)
        self.setSharedRenderer(renderer)
        self.setElementId(id)
        bounds = renderer.boundsOnElement(id)
        print("bounds on id=", bounds)
        print("bounds  rect=", self.boundingRect())
        self.setPos(bounds.topLeft())
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)

        self.selected_effect = None
        self.makeGraphicsEffect()

    def makeGraphicsEffect(self):
        if self.selected_effect is None:
            self.selected_effect = QtWidgets.QGraphicsColorizeEffect()    
            self.selected_effect.setColor(QtCore.Qt.darkYellow)
            self.selected_effect.setStrength(1)
    
    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        print('svg item: ' + self.elementId() + ' - mousePressEvent()' + str(self.isSelected()))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        print('svg item: ' + self.elementId() + ' - mouseReleaseEvent()' + str(self.isSelected()))
        super().mouseReleaseEvent(event)

    def colorizeWhenSelected(self):
        if self.isSelected():
            self.makeGraphicsEffect()
            self.setGraphicsEffect(self.selected_effect) 
        else:
            self.setGraphicsEffect(None) 
            self.selected_effect = None


class SvgViewer(QtWidgets.QGraphicsView):
    '''
    The SvgViewer can 'only' load full svg files. 
    It cannot increment the view with single "Paths
    
    So when augmenting the view, we have to pass all cnc operations
    and build a custom svg file on its own.
    This is possible with the help of the svgpathtools.

    Note that still only the paths from the original svg are selectable.
    '''
    zoomChanged = QtCore.Signal()

    def __init__(self, parent):
        super(SvgViewer, self).__init__(parent)
        self.scene = QtWidgets.QGraphicsScene(self,0,0,100,100)
        self.renderer = QtSvg.QSvgRenderer()
        self.renderer.setViewBox(QtCore.QRect(0,0,100,100))
        self.setScene(self.scene)

        self.svg = None
        self.path_d = {}

        self.items = []
        # ordered list of items - TODO
        self.selected_items = []

        #self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)

    def set_svg(self, svg: str):
        '''
        This sets the 'real' svg file data, not the later 'augmented' svg
        '''
        self.svg = svg
        self.fill_svg_viewer(self.svg)

    def fill_svg_viewer(self, svg: str):
        '''
        '''
        self.scene.clear()
        self.resetTransform()

        self.items = []
        self.selected_items = []

        self.renderer.load(bytes(svg, 'utf-8'))

        root = ET.fromstring(svg)

        paths = root.findall(".//{http://www.w3.org/2000/svg}path")
        for path in paths:
            print("svg : found path %s" % path.attrib['id'])
            id = path.attrib['id']
            dd = path.attrib['d']

            self.path_d[id] = dd

            item = SvgItem(id, self.renderer)
            self.scene.addItem(item)

            self.items.append(item)

    def get_path_d(self, p_id):
        return self.path_d[p_id]
    
    def clean(self):
        for item in self.items:
            self.scene.removeItem(item)

        self.items = []
        self.selected_items = []

    def mousePressEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):
        print('SvgViewer - mousePressEvent()')
        super().mousePressEvent(event)
        print("    --> List of selected items")
        for item in self.items:
            print("    item %s -> %s" % (item.elementId(), item.isSelected()))
            item.colorizeWhenSelected()

    def mouseReleaseEvent(self, event: 'QtWidgets.QGraphicsSceneMouseEvent'):
        print('SvgViewer - mouseReleaseEvent()')
        super().mouseReleaseEvent(event)
        print("    --> List of selected items")
        for item in self.items:
            print("    item %s -> %s" % (item.elementId(), item.isSelected()))
            item.colorizeWhenSelected()


    def wheelEvent(self, event):
        self.zoomBy(math.pow(1.2, event.angleDelta().y() / 240.0))

    def zoomFactor(self):
        return self.transform().m11()

    def zoomIn(self):
        self.zoomBy(2)

    def zoomOut(self):
        self.zoomBy(0.5)

    def resetZoom(self):
        if self.zoomFactor() != 1 :
            self.resetTransform()
            self.zoomChanged.emit()

    def zoomBy(self, factor):
        currentZoom = self.zoomFactor()
        if (factor < 1 and currentZoom < 0.1) or (factor > 1 and currentZoom > 10) :
            return
        self.scale(factor, factor)
        self.zoomChanged.emit()

    def display_cnc_op(self, combined_svg_paths: List['SvgPath']):
        '''
        '''
        tr = svgpathutils.SvgTransformer(self.svg)
        aug_svg = tr.augment(combined_svg_paths)

        self.fill_svg_viewer(aug_svg)

    #def display_cnc_job(self, cnc_job):
    #    '''
    #    '''
    #    svg = self.make_svg_from_cnc_job(cnc_job)
    #    self.fill_svg_viewer(svg)

    #def make_svg_from_cnc_job(self, cnc_job):
    #    '''
    #    '''
    #    all_svg_paths = []

    #    for cnc_op in cnc_job:
    #        all_svg_paths += cnc_op.svg_paths

    #  self.display_cnc_op(all_svg_paths)


            
