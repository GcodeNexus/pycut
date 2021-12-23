﻿

import sys
import ctypes

from typing import List

from PySide6.QtGui import QVector3D
from PySide6.QtGui import QOpenGLFunctions

from PySide6.QtCore import qIsNaN

from PySide6.QtOpenGL import QOpenGLShaderProgram
from PySide6.QtOpenGL import QOpenGLBuffer
from PySide6.QtOpenGL import QOpenGLVertexArrayObject
from PySide6.QtOpenGL import QOpenGLTexture

from OpenGL import GL

from gcodeviewer.util.util import Util

import numpy as np

sNan = 65536.0  # ???
sNaN = float('NaN')


class VertexData:
    def __init__(self):
        self.position = QVector3D()
        self.color = QVector3D()
        self.start = QVector3D()

    @classmethod
    def fromVectors(cls, position: QVector3D, color: QVector3D, start: QVector3D):
        vd = VertexData()
        vd.position = position
        vd.color = color
        vd.start = start
        return vd

    @classmethod
    def fromVertexData(cls, other: 'VertexData'):
        vd = VertexData()
        vd.position = Util.QVector3D_fromVector3D(other.position)
        vd.color = Util.QVector3D_fromVector3D(other.color)
        vd.start = Util.QVector3D_fromVector3D(other.start)
        return vd




class ShaderDrawable(QOpenGLFunctions):
    '''
    '''
    def __init__(self):
        '''
        '''
        QOpenGLFunctions.__init__(self)

        self.m_lineWidth = 1.0
        self.m_pointSize = 1.0
        self.m_visible = True
        self.m_lines : List[VertexData] = []
        self.m_points : List[VertexData] = []
        self.m_triangles : List[VertexData]  = []
        self.m_texture : QOpenGLTexture = None

        self.m_vbo = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        self.m_vao = QOpenGLVertexArrayObject()

        self.m_needsUpdateGeometry = False
    
    def update(self):
        self.m_needsUpdateGeometry = True

    def draw(self, shaderProgram: QOpenGLShaderProgram):
        if not self.m_visible:
            return

        if self.m_vao.isCreated():
            # Prepare vao
            self.m_vao.bind()
        else:
            # Prepare vbo
            self.m_vbo.bind()

            # Offset for position
            offset = 0

            vertexdata_size = 12  # sizeof(VertexData)

            # Tell OpenGL programmable pipeline how to locate vertex position data
            vertexLocation = shaderProgram.attributeLocation("a_position")
            shaderProgram.enableAttributeArray(vertexLocation)
            shaderProgram.setAttributeBuffer(vertexLocation, GL.GL_FLOAT, offset, 3, vertexdata_size)

            # Offset for color
            offset = 12

            # Tell OpenGL programmable pipeline how to locate vertex color data
            color = shaderProgram.attributeLocation("a_color")
            shaderProgram.enableAttributeArray(color)
            shaderProgram.setAttributeBuffer(color, GL.GL_FLOAT, offset, 3, vertexdata_size)

            # Offset for line start point
            offset += 12

            # Tell OpenGL programmable pipeline how to locate vertex line start point
            start = shaderProgram.attributeLocation("a_start")
            shaderProgram.enableAttributeArray(start)
            shaderProgram.setAttributeBuffer(start, GL.GL_FLOAT, offset, 3, vertexdata_size)
    

        if len(self.m_triangles) != 0:
            if self.m_texture:
                self.m_texture.bind()
                shaderProgram.setUniformValue("texture", 0)
        
            self.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.m_triangles))

        if len(self.m_lines) != 0:
            self.glLineWidth(self.m_lineWidth)
            self.glDrawArrays(GL.GL_LINES, len(self.m_triangles), len(self.m_lines))

        if len(self.m_points) != 0:
            self.glDrawArrays(GL.GL_POINTS, len(self.m_triangles) + len(self.m_lines), len(self.m_points))

        if self.m_vao.isCreated():
            self.m_vao.release()
        else:
            self.m_vbo.release()

    def needsUpdateGeometry(self) -> bool:
        return self.m_needsUpdateGeometry

    # -------------------------------------------------------------------
    def vertexes_to_numpy(self, vertexData: List[VertexData]):
        '''
        #https://nrotella.github.io/journal/first-steps-python-qt-opengl.html

        data = numpy.array([2., 2., 2., 0.5, 0.4, 0.4, 1.], dtype = numpy.float32).toString()
        # Write
        buffer.allocate(120) # How many bytes to allocate
        buffer.write(0, data, len(data))
        '''
        def NaN_to_Val(val):
            if qIsNaN(val):
                return 65536.0
            return val

        np_array = np.empty(9*len(vertexData), dtype=ctypes.c_float)
        
        for k, vdata in enumerate(vertexData):
            np_array[9*k+0] = NaN_to_Val(vdata.position.x())
            np_array[9*k+1] = NaN_to_Val(vdata.position.y())
            np_array[9*k+2] = NaN_to_Val(vdata.position.z())

            np_array[9*k+3] = NaN_to_Val(vdata.color.x())
            np_array[9*k+4] = NaN_to_Val(vdata.color.y())
            np_array[9*k+5] = NaN_to_Val(vdata.color.z())

            np_array[9*k+6] = NaN_to_Val(vdata.start.x())
            np_array[9*k+7] = NaN_to_Val(vdata.start.y())
            np_array[9*k+8] = NaN_to_Val(vdata.start.z())

        return np_array
    # -------------------------------------------------------------------

    def updateGeometry(self, shaderProgram : QOpenGLShaderProgram = None):
        # Init in context
        if not self.m_vbo.isCreated():
            self.init()

        if self.m_vao.isCreated():
            # Prepare vao
            self.m_vao.bind()

        # Prepare vbo
        self.m_vbo.bind()

        # Update vertex buffer
        if self.updateData():
            # Fill vertices buffer
            vertexData = []
            vertexData += self.m_triangles
            vertexData += self.m_lines
            vertexData += self.m_points

            np_array = self.vertexes_to_numpy(vertexData)
            np_bytes = np_array.tobytes()

            # demo
            self.m_vbo.allocate(len(np_bytes))
            self.m_vbo.write(0, np_bytes, len(np_bytes))

            # demo
            self.m_vbo.bind()
        else:
            self.m_vbo.release()        
            if self.m_vao.isCreated():
                self.m_vao.release()
            self.m_needsUpdateGeometry = False
            return

        if self.m_vao.isCreated():
            # Offset for position
            offset = 0

            vertexdata_size = 12  # sizeof(VertexData)

            # Tell OpenGL programmable pipeline how to locate vertex position data
            vertexLocation = shaderProgram.attributeLocation("a_position")
            shaderProgram.enableAttributeArray(vertexLocation)
            shaderProgram.setAttributeBuffer(vertexLocation, GL.GL_FLOAT, offset, 3, vertexdata_size)

            # Offset for color
            offset = vertexdata_size

            # Tell OpenGL programmable pipeline how to locate vertex color data
            color = shaderProgram.attributeLocation("a_color")
            shaderProgram.enableAttributeArray(color)
            shaderProgram.setAttributeBuffer(color, GL.GL_FLOAT, offset, 3, vertexdata_size)

            # Offset for line start point
            offset += vertexdata_size

            # Tell OpenGL programmable pipeline how to locate vertex line start point
            start = shaderProgram.attributeLocation("a_start")
            shaderProgram.enableAttributeArray(start)
            shaderProgram.setAttributeBuffer(start, GL.GL_FLOAT, offset, 3, vertexdata_size)

            self.m_vao.release()

        self.m_vbo.release()

        self.m_needsUpdateGeometry = False

    def getSizes(self) -> QVector3D:
        return QVector3D(0, 0, 0)

    def getMinimumExtremes(self) -> QVector3D:
        return QVector3D(0, 0, 0)

    def getMaximumExtremes(self) -> QVector3D:
        return QVector3D(0, 0, 0)

    def getVertexCount(self) -> int:
        return len(self.m_lines) + len(self.m_points) + len(self.m_triangles)

    def lineWidth(self) -> float:
        return self.m_lineWidth

    def setLineWidth(self, lineWidth: float):
        self.m_lineWidth = lineWidth

    def visible(self) -> bool:
        return self.m_visible

    def setVisible(self, visible: bool):
        self.m_visible = visible

    def pointSize(self) -> float:
        return self.m_pointSize

    def setPointSize(self, pointSize: float) :
        self.m_pointSize = pointSize

    def updateData(self) -> bool:
        # Test data
        self.m_lineslines = [
            VertexData.fromVectors(QVector3D(0, 0, 0), QVector3D(1, 0, 0), QVector3D(sNaN, 0, 0)),
            VertexData.fromVectors(QVector3D(10, 0, 0), QVector3D(1, 0, 0), QVector3D(sNaN, 0, 0)),
            VertexData.fromVectors(QVector3D(0, 0, 0), QVector3D(0, 1, 0), QVector3D(sNaN, 0, 0)),
            VertexData.fromVectors(QVector3D(0, 10, 0), QVector3D(0, 1, 0), QVector3D(sNaN, 0, 0)),
            VertexData.fromVectors(QVector3D(0, 0, 0), QVector3D(0, 0, 1), QVector3D(sNaN, 0, 0)),
            VertexData.fromVectors(QVector3D(0, 0, 10), QVector3D(0, 0, 1), QVector3D(sNaN, 0, 0))
        ]

        return True

    def init(self):
        # Init openGL functions
        self.initializeOpenGLFunctions()

        # Create buffers
        self.m_vao.create()
        vao_binder = QOpenGLVertexArrayObject.Binder(self.m_vao)

        self.m_vbo.create()



