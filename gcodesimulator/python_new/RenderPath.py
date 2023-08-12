
import sys
import math
import time

import numpy as np

from typing import List
from typing import Dict

from PySide6.QtCore import QSize, QPoint
from PySide6.QtGui import (
    QOpenGLFunctions,
    QVector2D,
    QVector3D,
    QVector4D,
    QMatrix4x4,
    QImage,
)
from PySide6.QtWidgets import QApplication, QMainWindow

from PySide6 import QtWidgets
from PySide6 import QtCore
from PySide6 import QtGui

from PySide6.QtOpenGL import (
    QOpenGLVertexArrayObject,
    QOpenGLBuffer,
    QOpenGLFramebufferObject,
    QOpenGLShaderProgram,
    QOpenGLShader,
    QOpenGLTexture,
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget

from OpenGL import GL

from PySide6.QtUiTools import QUiLoader

from gcodeminiparser import GcodeAtomicMvt
from gcodeminiparser import GcodeMiniParser

sNaN = float('NaN')

ZOOMSTEP = 2.0



class Scene:
    class VertexData:
        #NB_FLOATS_PER_VERTEX = 12
        NB_FLOATS_PER_VERTEX = 9 

        def __init__(self):
            self.pos1 = QVector3D()
            self.pos2 = QVector3D()
        
            self.startTime = sNaN
            self.endTime = sNaN
            self.command = sNaN

            # VBit
            # self.rawPos = QVector3D()

    def __init__(self, gcode):
        """ """
        self.gcode = gcode
        self.parser = GcodeMiniParser()
        self.parser.parse_gcode(self.gcode)

        self.topZ = 0.0
        self.cutterDiameter = 0.125 * 25.4
        self.cutterAngle = 180.0
        self.cutterHeight = 1.0 * 25.4

        self.isVBit = self.cutterAngle < 180

        self.pathNumPoints = 0
        self.pathStride = 9
        self.pathVertexesPerLine = 18
        self.pathNumVertexes = 0
    
        self.totalTime = 0.0

        self.pathXOffset = 0.0
        self.pathYOffset = 0.0
        self.pathScale = 0.0
        self.pathMinZ = 0.0

        # make a scene
        self.vertices: List[Scene.VertexData] = self.make_scene()

        self.array = None  # all vertices as  np float array
        # fill the numpy array from the scene ("path") and gets its buffer
        self.pathBufferContent = self.make_buffer()
    
    def make_scene(self):
        vertices : List[Scene.VertexData] = []

        # fill the numpy array - each vertex is composed of 9 float
        startTime = time.time()

        pathTopZ = self.topZ
        cutterDia = self.cutterDiameter
        if self.cutterAngle <= 0 or self.cutterAngle > 180:
            self.cutterAngle = 180
        cutterAngleRad = self.cutterAngle * math.pi / 180
        self.isVBit = isVBit = self.cutterAngle < 180
        cutterH = self.cutterHeight
        needToCreatePathTexture = True
        #requestFrame()
        inputStride = 4
        
        self.pathNumPoints = len(self.parser.path)

        numHalfCircleSegments = 5

        if isVBit:
            self.pathStride = 12
            self.pathVertexesPerLine = 12 + numHalfCircleSegments * 6
        else:
            self.pathStride = 9
            self.pathVertexesPerLine = 18

        self.pathNumVertexes = self.pathNumPoints * self.pathVertexesPerLine
        #self.pathBufferContent = bufferContent = np.empty(self.pathNumVertexes, dtype=np.float32)

        path = self.parser.path

        minX = path[0].pos.x()
        maxX = path[0].pos.x()
        minY = path[0].pos.y()
        maxY = path[0].pos.y()
        minZ = path[0].pos.z()

        total_time = 0
        for idx, point in enumerate(path):
            prevIdx = max(idx - 1, 0)
            prevPoint = path[prevIdx]
           
            x = point.pos.x()
            y = point.pos.y()
            z = point.pos.z()
            f = point.feedrate
            
            prevX = prevPoint.pos.x()
            prevY = prevPoint.pos.y()
            prevZ = prevPoint.pos.z()
            
            dist = math.sqrt((x - prevX) * (x - prevX) + (y - prevY) * (y - prevY) + (z - prevZ) * (z - prevZ))
            beginTime = total_time
            total_time = total_time + dist / f * 60

            minX = min(minX, x)
            maxX = max(maxX, x)
            minY = min(minY, y)
            maxY = max(maxY, y)
            minZ = min(minZ, z)

            if isVBit:
                coneHeight = -min(z, prevZ, 0) + 0.1
                coneDia = coneHeight * 2 * math.sin(cutterAngleRad / 2) / math.cos(cutterAngleRad / 2)

                if x == prevX and y == prevY:
                    rotAngle = 0
                else:
                    rotAngle = math.atan2(y - prevY, x - prevX)
                
                xyDist = math.sqrt((x - prevX) * (x - prevX) + (y - prevY) * (y - prevY))

                # --------------------------------------------------------------------------------------------------
                def f(command, rawX, rawY, rawZ, rotCos, rotSin, zOffset=None):
                    if zOffset is None:
                        zOffset = 0
                   
                    vertex = Scene.VertexData()
                    vertex.pos1 = QVector3D(prevX, prevY, prevZ + zOffset)
                    vertex.pos2 = QVector3D(x, y, z + zOffset)
                    vertex.startTime = beginTime
                    vertex.endTime = total_time
                    vertex.command = command
                    
                    if isVBit:
                        vertex.rawPos = QVector3D(rawX * rotCos - rawY * rotSin, rawY * rotCos + rawX * rotSin, rawZ)
                
                    vertices.append(vertex)
                # --------------------------------------------------------------------------------------------------

                if math.abs(z - prevZ) >= xyDist * math.pi / 2 * math.cos(cutterAngleRad / 2) / math.sin(cutterAngleRad / 2):
                    #console.log("plunge or retract")
                    #plunge or retract
                    index = 0

                    command = 100 if prevZ < z else 101
                    for circleIndex in range(1, numHalfCircleSegments*2):
                        a1 = 2 * math.pi * circleIndex / numHalfCircleSegments/2
                        a2 = 2 * math.pi * (circleIndex + 1) / numHalfCircleSegments/2
                        f(command, coneDia / 2 * math.cos(a2), coneDia / 2 * math.sin(a2), coneHeight, 1, 0)
                        index += 1
                        f(command, 0, 0, 0, 1, 0)
                        index += 1
                        f(command, coneDia / 2 * math.cos(a1), coneDia / 2 * math.sin(a1), coneHeight, 1, 0)
                        index += 1

                    while index < self.pathVertexesPerLine:
                        f(200, 0, 0, 0, 1, 0)
                        index += 1
        
                else:
                    # cut
                    planeContactAngle = math.asin((prevZ - z) / xyDist * math.sin(cutterAngleRad / 2) / math.cos(cutterAngleRad / 2))

                    index = 0
                    if True:
                        f(100, 0, -coneDia / 2, coneHeight, math.cos(rotAngle - planeContactAngle), math.sin(rotAngle - planeContactAngle))
                        f(101, 0, -coneDia / 2, coneHeight, math.cos(rotAngle - planeContactAngle), math.sin(rotAngle - planeContactAngle))
                        f(100, 0, 0, 0, 1, 0)
                        f(100, 0, 0, 0, 1, 0)
                        f(101, 0, -coneDia / 2, coneHeight, math.cos(rotAngle - planeContactAngle), math.sin(rotAngle - planeContactAngle))
                        f(101, 0, 0, 0, 1, 0)
                        f(100, 0, 0, 0, 1, 0)
                        f(101, 0, 0, 0, 1, 0)
                        f(100, 0, coneDia / 2, coneHeight, math.cos(rotAngle + planeContactAngle), math.sin(rotAngle + planeContactAngle))
                        f(100, 0, coneDia / 2, coneHeight, math.cos(rotAngle + planeContactAngle), math.sin(rotAngle + planeContactAngle))
                        f(101, 0, 0, 0, 1, 0)
                        f(101, 0, coneDia / 2, coneHeight, math.cos(rotAngle + planeContactAngle), math.sin(rotAngle + planeContactAngle))
                     
                        index += 12
       
                    startAngle = rotAngle + math.pi / 2 - planeContactAngle
                    endAngle = rotAngle + 3 * math.pi / 2 + planeContactAngle
                    for circleIndex in range(1,numHalfCircleSegments):
                        a1 = startAngle + circleIndex / numHalfCircleSegments * (endAngle - startAngle)
                        a2 = startAngle + (circleIndex + 1) / numHalfCircleSegments * (endAngle - startAngle)
                        #console.log("a1,a2: " + (a1 * 180 / math.pi) + ", " + (a2 * 180 / math.pi))

                        f(100, coneDia / 2 * math.cos(a2), coneDia / 2 * math.sin(a2), coneHeight, 1, 0)
                        f(100, 0, 0, 0, 1, 0)
                        f(100, coneDia / 2 * math.cos(a1), coneDia / 2 * math.sin(a1), coneHeight, 1, 0)
                        f(101, coneDia / 2 * math.cos(a2 + math.pi), coneDia / 2 * math.sin(a2 + math.pi), coneHeight, 1, 0)
                        f(101, 0, 0, 0, 1, 0)
                        f(101, coneDia / 2 * math.cos(a1 + math.pi), coneDia / 2 * math.sin(a1 + math.pi), coneHeight, 1, 0)

                        index += 16
                
            else :

                for virtex in range(self.pathVertexesPerLine):
                    vertex = Scene.VertexData()
                    vertex.pos1 = QVector3D(prevX, prevY, prevZ)
                    vertex.pos2 = QVector3D(x, y, z)
                    vertex.startTime = beginTime
                    vertex.endTime = total_time
                    vertex.command = virtex

                    vertices.append(vertex)

        self.totalTime = total_time

        self.pathXOffset = -(minX + maxX) / 2
        self.pathYOffset = -(minY + maxY) / 2
        size = max(maxX - minX + 4 * cutterDia, maxY - minY + 4 * cutterDia)
        self.pathScale = 2 / size
        self.pathMinZ = minZ
        
        return vertices

    def make_buffer(self):
        self.array = np.empty(len(self.vertices) * Scene.VertexData.NB_FLOATS_PER_VERTEX, dtype=np.float32)

        for k, vertex in enumerate(self.vertices):
            self.array[9 * k + 0] = vertex.pos1.x()
            self.array[9 * k + 1] = vertex.pos1.y()
            self.array[9 * k + 2] = vertex.pos1.z()
            self.array[9 * k + 3] = vertex.pos2.x()
            self.array[9 * k + 4] = vertex.pos2.y()
            self.array[9 * k + 5] = vertex.pos2.z()
            self.array[9 * k + 6] = vertex.startTime
            self.array[9 * k + 7] = vertex.endTime
            self.array[9 * k + 8] = vertex.command

        return self.array.tobytes() 

    def buffer_size(self) -> int:
        """in bytes"""
        return len(self.vertices) * Scene.VertexData.NB_FLOATS_PER_VERTEX * np.float32().itemsize


class SceneCutter:
    class VertexData:
        NB_FLOATS_PER_VERTEX = 6

        def __init__(self):
            self.vPos = QVector3D()
            self.vColor = QVector3D()

    def __init__(self):
        self.numDivisions = 40
        self.numTriangles = self.numDivisions * 4

        # make a scene
        self.vertices: List[SceneCutter.VertexData] = self.make_scene()

        # fill the numpy array from the scene and gets its buffer
        self.buffer = self.make_buffer()

    def make_scene(self) -> List[VertexData]:
        r = 0.7
        g = 0.7
        b = 0.0

        vertices: List[SceneCutter.VertexData] = []

        def addVertex(x: float, y: float, z: float):
            vertex = SceneCutter.VertexData()
            vertex.vPos.setX(x)
            vertex.vPos.setY(y)
            vertex.vPos.setZ(z)

            vertex.vColor.setX(r)
            vertex.vColor.setY(g)
            vertex.vColor.setZ(b)
        
            vertices.append(vertex)

        # define vertices
        lastX = 0.5 * math.cos(0)
        lastY = 0.5 * math.sin(0)
        for i in range(self.numDivisions):
            j = i + 1
            if j == self.numDivisions:
                j = 0
            x = 0.5 * math.cos(j * 2 * math.pi / self.numDivisions)
            y = 0.5 * math.sin(j * 2 * math.pi / self.numDivisions)
 
            addVertex(lastX, lastY, 0)
            addVertex(x, y, 0)
            addVertex(lastX, lastY, 1)
            addVertex(x, y, 0)
            addVertex(x, y, 1)
            addVertex(lastX, lastY, 1)
            addVertex(0, 0, 0)
            addVertex(x, y, 0)
            addVertex(lastX, lastY, 0)
            addVertex(0, 0, 1)
            addVertex(lastX, lastY, 1)
            addVertex(x, y, 1)

            lastX = x
            lastY = y

        return vertices

    def make_buffer(self):
        # fill the numpy array - each vertex is composed of 6 float
        array = np.empty(len(self.vertices) * SceneCutter.VertexData.NB_FLOATS_PER_VERTEX, dtype=np.float32)

        for k, vertex in enumerate(self.vertices):
            array[6 * k + 0] = vertex.vPos.x()
            array[6 * k + 1] = vertex.vPos.y()
            array[6 * k + 2] = vertex.vPos.z()
            array[6 * k + 3] = vertex.vColor.x()
            array[6 * k + 4] = vertex.vColor.y()
            array[6 * k + 5] = vertex.vColor.z()

        return array.tobytes()

    def buffer_size(self) -> int:
        """in bytes"""
        return len(self.vertices) * SceneCutter.VertexData.NB_FLOATS_PER_VERTEX * np.float32().itemsize


class SceneHeightMap:
    class VertexData:
        NB_FLOATS_PER_VERTEX = 9

        def __init__(self):
            self.vPos0 = QVector2D()
            self.vPos1 = QVector2D()
            self.vPos2 = QVector2D()
            self.vThisLoc = QVector2D()
            self.vertex = 0.0

    def __init__(self, resolution: int):
        self.resolution = resolution

        self.numTriangles = self.resolution * (self.resolution - 1)  # ?
        self.meshNumVertexes = self.numTriangles * 3  # ?

        # make a scene
        self.vertices: List[SceneHeightMap.VertexData] = self.make_scene()

        # fill the numpy array from the scene and gets its buffer
        self.buffer = self.make_buffer()

    def make_scene(self) -> List[VertexData]:
        vertices : List[SceneHeightMap.VertexData] = []

        def addVertex(x0: float, y0: float, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float, idx):
            vertex = SceneHeightMap.VertexData()
            vertex.vPos0.setX(x0)
            vertex.vPos0.setY(y0)
            vertex.vPos1.setX(x1)
            vertex.vPos1.setY(y1)
            vertex.vPos2.setX(x2)
            vertex.vPos2.setY(y2)
            vertex.vThisLoc.setX(x3)
            vertex.vThisLoc.setY(y3)
            vertex.vertex = idx
        
            vertices.append(vertex)
        
        
        for y in range(self.resolution - 1):
            for x in range(self.resolution):
                left = x - 1
                if left < 0:
                    left = 0
                right = x + 1
                if right >= self.resolution:
                    right = self.resolution - 1
                if not ((x & 1) ^ (y & 1)):
                    for idx in range(3):
                        if idx == 0 :
                            addVertex(left, y+1, x, y, right, y+1, left, y+1, idx) 
                        elif idx == 1:
                            addVertex(left, y+1, x, y, right, y+1, x, y, idx)
                        else :
                            addVertex(left, y+1, x, y, right, y+1, right, y+1, idx)
                else:
                    for idx in range(3):
                        if idx == 0:
                            addVertex(left, y, right, y, x, y+1, left, y, idx)
                        elif idx == 1:
                            addVertex(left, y, right, y, x, y+1, right, y, idx)
                        else:
                            addVertex(left, y, right, y, x, y+1, x, y+1, idx)

        return vertices

    def make_buffer(self):
        # fill the numpy array - each vertex is composed of 6 float
        array = np.empty(len(self.vertices) * SceneHeightMap.VertexData.NB_FLOATS_PER_VERTEX, dtype=np.float32)

        for k, vertex in enumerate(self.vertices):
            array[9 * k + 0] = vertex.vPos0.x()
            array[9 * k + 1] = vertex.vPos0.y()
            array[9 * k + 2] = vertex.vPos1.x()
            array[9 * k + 3] = vertex.vPos1.y()
            array[9 * k + 4] = vertex.vPos2.x()
            array[9 * k + 5] = vertex.vPos2.y()
            array[9 * k + 6] = vertex.vThisLoc.x()
            array[9 * k + 7] = vertex.vThisLoc.y()
            array[9 * k + 8] = vertex.vertex

        return array.tobytes()

    def buffer_size(self) -> int:
        """in bytes"""
        return len(self.vertices) * SceneHeightMap.VertexData.NB_FLOATS_PER_VERTEX * np.float32().itemsize



class Drawable:
    path_shader_vs = "shaders/rasterizePathVertexShader.txt"
    path_shader_fs = "shaders/rasterizePathFragmentShader.txt"

    height_shader_vs = "shaders/renderHeightMapVertexShader.txt"
    height_shader_fs = "shaders/renderHeightMapFragmentShader.txt"

    #  the cutter
    basic_shader_vs = "shaders/basicVertexShader.txt"
    basic_shader_fs = "shaders/basicFragmentShader.txt"

    TEXTURE_INDEX_0 = 0

    def __init__(self, gcode):
        coeff = 2 # MY GPU

        self.gpuMem = 2 * 1024 * 1024 * coeff * coeff
        self.resolution = 1024 * coeff
        
        print("Scene path...")
        self.scene = Scene(gcode)
        print("Scene cutter...")
        self.scene_cutter = SceneCutter()
        print("Scene heightmap...")
        #self.scene_heightmap = SceneHeightMap(self.resolution)

        self.cutterDia = self.scene.cutterDiameter
        self.cutterAngleRad = self.scene.cutterAngle * math.pi / 180
        self.isVBit = self.scene.isVBit
        self.cutterH = self.scene.cutterHeight
        self.pathXOffset = self.scene.pathXOffset
        self.pathYOffset = self.scene.pathYOffset
        self.pathScale = self.scene.pathScale
        self.pathMinZ = self.scene.pathMinZ
        self.pathTopZ = self.scene.topZ

        self.stopAtTime = 9999999
        self.rotate = QMatrix4x4()
        self.rotate.setToIdentity()

        # -----------------------------------------------

        self.needToCreatePathTexture = False
        self.needToDrawHeightMap = False
        self.requestFrame = None

        self.program_path = QOpenGLShaderProgram()
        self.vao_path = QOpenGLVertexArrayObject()
        self.vbo_path = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
        
        self.program_cutter = QOpenGLShaderProgram()
        self.vao_cutter = QOpenGLVertexArrayObject()
        self.vbo_cutter = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)

        self.program_heightmap = QOpenGLShaderProgram()
        self.vao_heightmap = QOpenGLVertexArrayObject()
        self.vbo_heightmap = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)

        self.texture1 = QOpenGLTexture(QOpenGLTexture.Target2D)
        self.texture2 = QOpenGLTexture(QOpenGLTexture.Target2D)

        self.model = QMatrix4x4()
        self.model.setToIdentity()

        self.proj = QMatrix4x4()
        self.proj.setToIdentity()

        self.view = QMatrix4x4()
        self.view.setToIdentity()
        self.view.translate(QVector3D(0, 0, -5))

    def clean(self):
        self.vbo_path.destroy()
        self.vbo_cutter.destroy()
        self.vbo_heightmap.destroy()
        del self.program_path
        del self.program_cutter
        del self.program_heightmap
        self.program_path = None
        self.program_cutter = None
        self.program_heightmap = None

    def initialize(self):
        """ """
        self.initialize_path()
        self.initialize_cutter()
        #self.initialize_heightmap()

    def draw(self, gl: "GLWidget"):
        self.draw_path(gl)
        self.draw_cutter(gl)
        #self.draw_heightmap(gl)

    # -----------------------------------------------------------------

    def initialize_path(self):
        """ """
        self.program_path.addCacheableShaderFromSourceFile(QOpenGLShader.Vertex, self.path_shader_vs)
        self.program_path.addCacheableShaderFromSourceFile(QOpenGLShader.Fragment, self.path_shader_fs)
        self.program_path.link()

        self.program_path.bind()

        self.vbo_path.create()  # QOpenGLBuffer.VertexBuffer
        self.vbo_path.setUsagePattern(QOpenGLBuffer.DynamicDraw)
        self.vbo_path.bind()

        self.array = np.zeros(self.gpuMem, dtype=np.float32)
        self.vbo_path.allocate(self.array.tobytes(), self.gpuMem * np.float32().itemsize)

        self.setup_vao_path()

        self.program_path.release()

    def setup_vao_path(self):
        self.vao_path.create()
        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_path)

        self.resolutionLocation = self.program_path.uniformLocation("resolution")
        self.cutterDiaLocation = self.program_path.uniformLocation("cutterDia")
        self.pathXYOffsetLocation = self.program_path.uniformLocation("pathXYOffset")
        self.pathScaleLocation = self.program_path.uniformLocation("pathScale")
        self.pathMinZLocation = self.program_path.uniformLocation("pathMinZ")
        self.pathTopZLocation = self.program_path.uniformLocation("pathTopZ")
        self.stopAtTimeLocation = self.program_path.uniformLocation("stopAtTime")

        self.program_path.setUniformValue1f(self.resolutionLocation, float(self.resolution))
        self.program_path.setUniformValue1f(self.cutterDiaLocation, float(self.cutterDia))
        self.program_path.setUniformValue(self.pathXYOffsetLocation, float(self.pathXOffset), float(self.pathYOffset))
        self.program_path.setUniformValue1f(self.pathScaleLocation, float(self.pathScale))
        self.program_path.setUniformValue1f(self.pathMinZLocation, float(self.pathMinZ))
        self.program_path.setUniformValue1f(self.pathTopZLocation, float(self.pathTopZ))
        self.program_path.setUniformValue1f(self.stopAtTimeLocation, float(self.stopAtTime))

        self.vbo_path.bind()

        pos1Location = self.program_path.attributeLocation("pos1")
        pos2Location = self.program_path.attributeLocation("pos2")
        startTimeLocation = self.program_path.attributeLocation("startTime")
        endTimeLocation = self.program_path.attributeLocation("endTime")
        commandLocation = self.program_path.attributeLocation("command")
        rawPosLocation = self.program_path.attributeLocation("rawPos")


        self.program_path.enableAttributeArray(pos1Location)
        self.program_path.enableAttributeArray(pos2Location)
        self.program_path.enableAttributeArray(startTimeLocation)
        self.program_path.enableAttributeArray(endTimeLocation)
        self.program_path.enableAttributeArray(commandLocation)

        if self.isVBit:
            self.program_path.enableAttributeArray(rawPosLocation)


        stride = Scene.VertexData.NB_FLOATS_PER_VERTEX * np.float32().itemsize

        self.program_path.setAttributeBuffer(pos1Location, GL.GL_FLOAT,      0                        , 3, stride)
        self.program_path.setAttributeBuffer(pos2Location, GL.GL_FLOAT,      3 * np.float32().itemsize, 3, stride)
        self.program_path.setAttributeBuffer(startTimeLocation, GL.GL_FLOAT, 6 * np.float32().itemsize, 1, stride)
        self.program_path.setAttributeBuffer(endTimeLocation, GL.GL_FLOAT,   7 * np.float32().itemsize, 1, stride)
        self.program_path.setAttributeBuffer(commandLocation, GL.GL_FLOAT,   8 * np.float32().itemsize, 1, stride)

        self.vbo_path.release()

        vao_binder = None

    def draw_path(self, gl: "GLWidget"):
        """ """
        self.program_path.bind()

        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_path)
        
        self.program_path.setUniformValue1f(self.resolutionLocation, float(self.resolution))
        self.program_path.setUniformValue1f(self.cutterDiaLocation, float(self.cutterDia))
        self.program_path.setUniformValue(self.pathXYOffsetLocation, float(self.pathXOffset), float(self.pathYOffset))
        self.program_path.setUniformValue1f(self.pathScaleLocation, float(self.pathScale))
        self.program_path.setUniformValue1f(self.pathMinZLocation, float(self.pathMinZ))
        self.program_path.setUniformValue1f(self.pathTopZLocation, float(self.pathTopZ))
        self.program_path.setUniformValue1f(self.stopAtTimeLocation, float(self.stopAtTime))

        numTriangles = self.scene.pathNumVertexes // 3
        lastTriangle = 0
        maxTriangles = math.floor(self.gpuMem // self.scene.pathStride // 3 // np.float32().itemsize)
        
        while lastTriangle < numTriangles:
            n = int(min(numTriangles - lastTriangle, maxTriangles))

            """
            b = new Float32Array(pathBufferContent.buffer, lastTriangle * pathStride * 3 * Float32Array.BYTES_PER_ELEMENT, n * pathStride * 3)
            gl.bufferSubData(self.gl.ARRAY_BUFFER, 0, b)
            """

            # TRANSLATE TO

            start = lastTriangle * self.scene.pathStride * 3 * np.float32().itemsize
            length = n * self.scene.pathStride * 3
            
            scene_buffer_window = self.scene.pathBufferContent[start:start + length]

            # -> map to vbo : DOES NOT WORK !
            data = self.vbo_path.map(QOpenGLBuffer.WriteOnly)
    
            print("data = ", data)
            if data :
                data[:] = scene_buffer_window[:]
                self.vbo_path.unmap()
                # -> done
                       
                gl.glDrawArrays(GL.GL_TRIANGLES, 0, n * 3)
            
            lastTriangle += n
        
        
        vao_binder = None

        self.program_path.release()

    # -----------------------------------------------------------------

    def initialize_cutter(self):
        """
        """
        self.program_cutter.addCacheableShaderFromSourceFile(QOpenGLShader.Vertex, self.basic_shader_vs)
        self.program_cutter.addCacheableShaderFromSourceFile(QOpenGLShader.Fragment, self.basic_shader_fs)
        self.program_cutter.link()

        self.program_cutter.bind()

        self.vbo_cutter.create()  # QOpenGLBuffer.VertexBuffer
        self.vbo_cutter.setUsagePattern(QOpenGLBuffer.StaticDraw)
        self.vbo_cutter.bind()

        self.vbo_cutter.allocate(self.scene_cutter.buffer, self.scene_cutter.buffer_size())

        self.setup_vao_cutter()

        self.program_cutter.release()

    def setup_vao_cutter(self):
        self.vao_cutter.create()
        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_cutter)

        self.scaleLocation = self.program_cutter.uniformLocation("scale")
        self.translateLocation = self.program_cutter.uniformLocation("translate")
        self.rotateLocation = self.program_cutter.uniformLocation("rotate")

        self.program_cutter.setUniformValue(self.scaleLocation, self.cutterDia * self.pathScale, self.cutterDia * self.pathScale, self.cutterH * self.pathScale)
        self.program_cutter.setUniformValue(self.translateLocation, (0 + self.pathXOffset) * self.pathScale, (0 + self.pathYOffset) * self.pathScale, (0 - self.pathTopZ) * self.pathScale)
        self.program_cutter.setUniformValue(self.rotateLocation, self.rotate)

        self.vbo_cutter.bind()

        self.posLocation = self.program_cutter.attributeLocation("vPos")
        self.colLocation = self.program_cutter.attributeLocation("vColor")

        self.program_cutter.enableAttributeArray(self.posLocation)
        self.program_cutter.enableAttributeArray(self.colLocation)

        stride = SceneCutter.VertexData.NB_FLOATS_PER_VERTEX * np.float32().itemsize

        self.program_cutter.setAttributeBuffer(self.posLocation, GL.GL_FLOAT, 0,                         3, stride)
        self.program_cutter.setAttributeBuffer(self.colLocation, GL.GL_FLOAT, 3 * np.float32().itemsize, 3, stride)

        self.vbo_cutter.release()

        vao_binder = None

    def draw_cutter(self, gl: "GLWidget"):
        """
        """
        def lowerBound(data, offset: int, stride: int, begin: int, end: int, value: float):
            while begin < end:
                i = math.floor((begin + end) / 2)

                if data[offset + i * stride] < value:
                    begin = i + 1
                else:
                    end = i
        
            return end
        
        def mix(v0, v1, a):
            return v0 + (v1 - v0) * a
    
        
        i = lowerBound(self.scene.array, 7, self.scene.pathStride * self.scene.pathVertexesPerLine, 0, self.scene.pathNumPoints, self.stopAtTime)
        x = 0.0
        y = 0.0
        z = 0.0

        if i < self.scene.pathNumPoints:
            offset = i * self.scene.pathStride * self.scene.pathVertexesPerLine
            beginTime = self.scene.array[offset + 6]
            endTime = self.scene.array[offset + 7]
            ratio = 0
            if endTime == beginTime:
                ratio = 0
            else:
                ratio = (self.stopAtTime - beginTime) / (endTime - beginTime)
            x = mix(self.scene.array[offset + 0], self.scene.array[offset + 3], ratio)
            y = mix(self.scene.array[offset + 1], self.scene.array[offset + 4], ratio)
            z = mix(self.scene.array[offset + 2], self.scene.array[offset + 5], ratio)
        
        else:
            offset = (i-1) * self.scene.pathStride * self.scene.pathVertexesPerLine
            x = self.scene.array[offset + 3]
            y = self.scene.array[offset + 4]
            z = self.scene.array[offset + 5]

        self.program_cutter.bind()

        print("SCALE = ", self.pathScale)

        self.program_cutter.setUniformValue(self.scaleLocation, self.cutterDia * self.pathScale, self.cutterDia * self.pathScale, self.cutterH * self.pathScale)
        self.program_cutter.setUniformValue(self.translateLocation, (x + self.pathXOffset) * self.pathScale, (y + self.pathYOffset) * self.pathScale, (z - self.pathTopZ) * self.pathScale)
        self.program_cutter.setUniformValue(self.rotateLocation, self.rotate)

        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_cutter)

        self.program_cutter.enableAttributeArray(self.posLocation)
        self.program_cutter.enableAttributeArray(self.colLocation)

        gl.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.scene_cutter.vertices))

        self.program_cutter.disableAttributeArray(self.posLocation)
        self.program_cutter.disableAttributeArray(self.colLocation)

        vao_binder = None

        self.program_cutter.release()

    # -----------------------------------------------------------------

    def initialize_heightmap(self):
        """
        """
        self.program_heightmap.addCacheableShaderFromSourceFile(QOpenGLShader.Vertex, self.height_shader_vs)
        self.program_heightmap.addCacheableShaderFromSourceFile(QOpenGLShader.Fragment, self.height_shader_fs)
        self.program_heightmap.link()

        self.program_heightmap.bind()

        self.vbo_heightmap.create()
        #self.vbo_heightmap.setUsagePattern(QOpenGLBuffer.StaticDraw)
        self.vbo_heightmap.bind()

        self.vbo_heightmap.allocate(self.scene_heightmap.buffer, self.scene_heightmap.buffer_size())

        self.setup_vao_heightmap()

        self.program_heightmap.release()

    def setup_vao_heightmap(self):
        self.vao_heightmap.create()
        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_heightmap)

        self.program_heightmap_resolutionLocation = self.program_heightmap.uniformLocation("resolution")
        self.program_heightmap_pathScaleLocation = self.program_heightmap.uniformLocation("pathScale")
        self.program_heightmap_pathMinZLocation = self.program_heightmap.uniformLocation("pathMinZ")
        self.program_heightmap_pathTopZLocation = self.program_heightmap.uniformLocation("pathTopZ")
        self.program_heightmap_rotateLocation = self.program_heightmap.uniformLocation("rotate")
        self.program_heightmap_heightMapLocation = self.program_heightmap.uniformLocation("heightMap")

        self.program_heightmap_pos0Location = self.program_heightmap.attributeLocation("pos0")
        self.program_heightmap_pos1Location = self.program_heightmap.attributeLocation("pos1")
        self.program_heightmap_pos2Location = self.program_heightmap.attributeLocation("pos2")
        self.program_heightmap_thisPos = self.program_heightmap.attributeLocation("thisPos")
        self.program_heightmap_vertex = self.program_heightmap.attributeLocation("vertex")

        self.vbo_heightmap.bind()

        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos0Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos1Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos2Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_thisPos)
        #self.program_heightmap.enableAttributeArray(self.program_heightmap_vertex)

        stride = 9 * np.float32().itemsize

        self.program_heightmap.setAttributeBuffer(self.program_heightmap_pos0Location, GL.GL_FLOAT, 0,                         2, stride)
        self.program_heightmap.setAttributeBuffer(self.program_heightmap_pos1Location, GL.GL_FLOAT, 2 * np.float32().itemsize, 2, stride)
        self.program_heightmap.setAttributeBuffer(self.program_heightmap_pos2Location, GL.GL_FLOAT, 4 * np.float32().itemsize, 2, stride)
        self.program_heightmap.setAttributeBuffer(self.program_heightmap_thisPos,      GL.GL_FLOAT, 6 * np.float32().itemsize, 2, stride)
        #self.program_heightmap.setAttributeBuffer(self.program_heightmap_vertex,       GL.GL_FLOAT, 8 * np.float32().itemsize, 1, stride)


        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos0Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos1Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos2Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_thisPos)
        #self.program_heightmap.disableAttributeArray(self.program_heightmap_vertex)

        self.vbo_heightmap.release()

        vao_binder = None

    def create_heightmap_textures(self, gl: "GLWidget"):
        pass  # TODO
        self.pathFramebuffer = QOpenGLFramebufferObject(
            QSize(self.resolution, self.resolution),
            QOpenGLFramebufferObject.CombinedDepthStencil
        )
        self.pathFramebuffer.bind()

        self.pathRgbaTexture = QOpenGLTexture(QOpenGLTexture.Target2D)
        gl.glActiveTexture(GL.GL_TEXTURE0)

        self.pathRgbaTexture.bind(self.TEXTURE_INDEX_0)
        gl.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGBA, self.resolution, self.resolution, 0, GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, None)
        gl.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        gl.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        gl.glFramebufferTexture2D(GL.GL_FRAMEBUFFER, GL.GL_COLOR_ATTACHMENT0, GL.GL_TEXTURE_2D, self.pathRgbaTexture, 0)
        self.pathRgbaTexture.release()
    
        self.renderbuffer = QOpenGLBuffer() 
        self.renderbuffer.bind(GL.GL_RENDERBUFFER)
        gl.glRenderbufferStorage(GL.GL_RENDERBUFFER, GL.GL_DEPTH_COMPONENT16, self.resolution, self.resolution)
        gl.glFramebufferRenderbuffer(GL.GL_FRAMEBUFFER, GL.GL_DEPTH_ATTACHMENT, GL.GL_RENDERBUFFER, self.renderbuffer)
        self.renderbuffer.release()
    
        self.pathFramebuffer.release()
        
    def draw_heightmap(self, gl: "GLWidget"):
        pass # TODO

        self.program_heightmap.bind()

        self.program_heightmap.setUniformValue(self.program_heightmap_resolutionLocation, self.resolution)
        self.program_heightmap.setUniformValue(self.program_heightmap_pathScaleLocation, self.pathScale)
        self.program_heightmap.setUniformValue(self.program_heightmap_pathMinZLocation, self.pathMinZ)
        self.program_heightmap.setUniformValue(self.program_heightmap_pathTopZLocation, self.pathTopZ)
        self.program_heightmap.setUniformValue(self.program_heightmap_rotateLocation, self.rotate)
        self.program_heightmap.setUniformValue(self.program_heightmap_heightMapLocation, 0)
        
        vao_binder = QOpenGLVertexArrayObject.Binder(self.vao_heightmap)

        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos0Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos1Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_pos2Location)
        self.program_heightmap.enableAttributeArray(self.program_heightmap_thisPos)
        #self.program_heightmap.enableAttributeArray(self.program_heightmap_vertex)

        # bind texture to texture index "TEXTURE_INDEX_0" -> accessible in fragment shader through "texture"
        self.pathRgbaTexture.bind(self.TEXTURE_INDEX_0)

        gl.glDrawArrays(GL.GL_TRIANGLES, 0, len(self.scene_heightmap.vertices))

        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos0Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos1Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_pos2Location)
        self.program_heightmap.disableAttributeArray(self.program_heightmap_thisPos)
        #self.program_heightmap.disableAttributeArray(self.program_heightmap_vertex)

        vao_binder = None

        self.program_heightmap.release()


class GLWidget(QOpenGLWidget, QOpenGLFunctions):
    """ """

    rotationChanged = QtCore.Signal()
    resized = QtCore.Signal()

    def __init__(self, gcode):
        QOpenGLWidget.__init__(self)
        QOpenGLFunctions.__init__(self)

        self.drawable = Drawable(gcode)

        self.m_xRot = 90.0
        self.m_yRot = 0.0
        self.m_xLastRot = 0.0
        self.m_yLastRot = 0.0
        self.m_xPan = 0.0
        self.m_yPan = 0.0
        self.m_xLastPan = 0.0
        self.m_yLastPan = 0.0
        self.m_xLookAt = 0.0
        self.m_yLookAt = 0.0
        self.m_zLookAt = 0.0
        self.m_lastPos = QPoint(0, 0)
        self.m_zoom = 10.0
        self.m_distance = 10.0
        self.m_xMin = 0.0
        self.m_xMax = 0.0
        self.m_yMin = 0.0
        self.m_yMax = 0.0
        self.m_zMin = 0.0
        self.m_zMax = 0.0
        self.m_xSize = 0.0
        self.m_ySize = 0.0
        self.m_zSize = 0.0

        self.m_xRotTarget = 90.0
        self.m_yRotTarget = 0.0
        self.m_xRotStored = 0.0
        self.m_yRotStored = 0.0

        self.updateProjection()
        self.updateView()

        self.cmdFit = QtWidgets.QToolButton(self)
        self.cmdIsometric = QtWidgets.QToolButton(self)
        self.cmdTop = QtWidgets.QToolButton(self)
        self.cmdFront = QtWidgets.QToolButton(self)
        self.cmdLeft = QtWidgets.QToolButton(self)

        self.cmdFit.setMinimumSize(QtCore.QSize(24, 24))
        self.cmdIsometric.setMinimumSize(QtCore.QSize(24, 24))
        self.cmdTop.setMinimumSize(QtCore.QSize(24, 24))
        self.cmdFront.setMinimumSize(QtCore.QSize(24, 24))
        self.cmdLeft.setMinimumSize(QtCore.QSize(24, 24))

        self.cmdFit.setMaximumSize(QtCore.QSize(24, 24))
        self.cmdIsometric.setMaximumSize(QtCore.QSize(24, 24))
        self.cmdTop.setMaximumSize(QtCore.QSize(24, 24))
        self.cmdFront.setMaximumSize(QtCore.QSize(24, 24))
        self.cmdLeft.setMaximumSize(QtCore.QSize(24, 24))

        self.cmdFit.setToolTip("Fit")
        self.cmdIsometric.setToolTip("Isometric view")
        self.cmdTop.setToolTip("Top view")
        self.cmdFront.setToolTip("Front view")
        self.cmdLeft.setToolTip("Left view")

        self.cmdFit.setIcon(QtGui.QIcon("./pics/fit_1.png"))
        self.cmdIsometric.setIcon(QtGui.QIcon("./pics/cube.png"))
        self.cmdTop.setIcon(QtGui.QIcon("./pics/cubeTop.png"))
        self.cmdFront.setIcon(QtGui.QIcon("./pics/cubeFront.png"))
        self.cmdLeft.setIcon(QtGui.QIcon("./pics/cubeLeft.png"))

        self.cmdFit.clicked.connect(self.on_cmdFit_clicked)
        self.cmdIsometric.clicked.connect(self.on_cmdIsometric_clicked)
        self.cmdTop.clicked.connect(self.on_cmdTop_clicked)
        self.cmdFront.clicked.connect(self.on_cmdFront_clicked)
        self.cmdLeft.clicked.connect(self.on_cmdLeft_clicked)

        self.rotationChanged.connect(self.onVisualizatorRotationChanged)
        self.resized.connect(self.placeVisualizerButtons)

    def placeVisualizerButtons(self):
        self.cmdIsometric.move(self.width() - self.cmdIsometric.width() - 8, 8)
        self.cmdTop.move(
            self.cmdIsometric.geometry().left() - self.cmdTop.width() - 8, 8
        )
        self.cmdLeft.move(
            self.width() - self.cmdLeft.width() - 8,
            self.cmdIsometric.geometry().bottom() + 8,
        )
        self.cmdFront.move(
            self.cmdLeft.geometry().left() - self.cmdFront.width() - 8,
            self.cmdIsometric.geometry().bottom() + 8,
        )
        self.cmdFit.move(
            self.width() - self.cmdFit.width() - 8, self.cmdLeft.geometry().bottom() + 8
        )

    def on_cmdTop_clicked(self):
        self.setTopView()
        self.updateView()

        self.onVisualizatorRotationChanged()

    def on_cmdFront_clicked(self):
        self.setFrontView()
        self.updateView()

        self.onVisualizatorRotationChanged()

    def on_cmdLeft_clicked(self):
        self.setLeftView()
        self.updateView()

        self.onVisualizatorRotationChanged()

    def on_cmdIsometric_clicked(self):
        self.setIsometricView()
        self.updateView()

        self.onVisualizatorRotationChanged()

    def on_cmdFit_clicked(self):
        self.fitDrawable()

    def calculateVolume(self, size: QtGui.QVector3D) -> float:
        return size.x() * size.y() * size.z()

    def fitDrawable(self):
        self.updateExtremes()

        a = self.m_ySize / 2 / 0.25 * 1.3 + (self.m_zMax - self.m_zMin) / 2
        b = (
            self.m_xSize / 2 / 0.25 * 1.3 / (self.width() / self.height())
            + (self.m_zMax - self.m_zMin) / 2
        )

        self.m_distance = max(a, b)

        if self.m_distance == 0:
            self.m_distance = 10

        self.m_xLookAt = (self.m_xMax - self.m_xMin) / 2 + self.m_xMin
        self.m_zLookAt = -((self.m_yMax - self.m_yMin) / 2 + self.m_yMin)
        self.m_yLookAt = (self.m_zMax - self.m_zMin) / 2 + self.m_zMin

        self.m_xPan = 0
        self.m_yPan = 0
        self.m_zoom = 1

        self.updateProjection()
        self.updateView()

    def normalizeAngle(self, angle: float) -> float:
        while angle < 0:
            angle += 360
        while angle > 360:
            angle -= 360

        return angle

    def updateExtremes(self):
        self.m_xMin = self.drawable.scene.getMinimumExtremes().x()
        self.m_xMax = self.drawable.scene.getMaximumExtremes().x()

        self.m_yMin = self.drawable.scene.getMinimumExtremes().y()
        self.m_yMax = self.drawable.scene.getMaximumExtremes().y()

        self.m_zMin = self.drawable.scene.getMinimumExtremes().z()
        self.m_zMax = self.drawable.scene.getMaximumExtremes().z()

        self.m_xSize = self.m_xMax - self.m_xMin
        self.m_ySize = self.m_yMax - self.m_yMin
        self.m_zSize = self.m_zMax - self.m_zMin

    def setIsometricView(self):
        """no animation yet"""
        self.m_xRotTarget = 45
        self.m_yRotTarget = 405 if self.m_yRot > 180 else 45

        self.m_xRot = 45
        self.m_yRot = 405 if self.m_yRot > 180 else 45

    def setTopView(self):
        """no animation yet"""
        self.m_xRotTarget = 90
        self.m_yRotTarget = 360 if self.m_yRot > 180 else 0

        self.m_xRot = 90
        self.m_yRot = 360 if self.m_yRot > 180 else 0

    def setFrontView(self):
        """no animation yet"""
        self.m_xRotTarget = 0
        self.m_yRotTarget = 360 if self.m_yRot > 180 else 0

        self.m_xRot = 0
        self.m_yRot = 360 if self.m_yRot > 180 else 0

    def setLeftView(self):
        """no animation yet"""
        self.m_xRotTarget = 0
        self.m_yRotTarget = 450 if self.m_yRot > 270 else 90

        self.m_xRot = 0
        self.m_yRot = 450 if self.m_yRot > 270 else 90

    def updateProjection(self):
        # Reset projection
        self.drawable.proj.setToIdentity()

        asp = self.width() / self.height()
        self.drawable.proj.frustum(
            (-0.5 + self.m_xPan) * asp,
            (0.5 + self.m_xPan) * asp,
            -0.5 + self.m_yPan,
            0.5 + self.m_yPan,
            2,
            self.m_distance * 2,
        )

    def updateView(self):
        # Set view matrix
        self.drawable.view.setToIdentity()

        r = self.m_distance
        angY = math.pi / 180 * self.m_yRot
        angX = math.pi / 180 * self.m_xRot

        eye = QtGui.QVector3D(
            r * math.cos(angX) * math.sin(angY) + self.m_xLookAt,
            r * math.sin(angX) + self.m_yLookAt,
            r * math.cos(angX) * math.cos(angY) + self.m_zLookAt,
        )

        center = QtGui.QVector3D(self.m_xLookAt, self.m_yLookAt, self.m_zLookAt)

        xRot = math.pi if self.m_xRot < 0 else 0

        up = QtGui.QVector3D(
            -math.sin(angY + xRot) if math.fabs(self.m_xRot) == 90 else 0,
            math.cos(angX),
            -math.cos(angY + xRot) if math.fabs(self.m_xRot) == 90 else 0,
        )

        self.drawable.view.lookAt(eye, center, up.normalized())

        self.drawable.view.translate(self.m_xLookAt, self.m_yLookAt, self.m_zLookAt)
        self.drawable.view.scale(self.m_zoom, self.m_zoom, self.m_zoom)
        self.drawable.view.translate(-self.m_xLookAt, -self.m_yLookAt, -self.m_zLookAt)

        self.drawable.view.rotate(-90, 1.0, 0.0, 0.0)

    def set_model_position(self, position: QVector3D):
        self.drawable.model.setToIdentity()
        self.drawable.model.translate(position)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.m_lastPos = event.position()
        self.m_xLastRot = self.m_xRot
        self.m_yLastRot = self.m_yRot
        self.m_xLastPan = self.m_xPan
        self.m_yLastPan = self.m_yPan

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if (
            event.buttons() & QtGui.Qt.MiddleButton
            and (not (event.modifiers() & QtGui.Qt.ShiftModifier))
        ) or event.buttons() & QtCore.Qt.LeftButton:
            self.m_yRot = self.normalizeAngle(
                self.m_yLastRot - (event.position().x() - self.m_lastPos.x()) * 0.5
            )
            self.m_xRot = (
                self.m_xLastRot + (event.position().y() - self.m_lastPos.y()) * 0.5
            )

            if self.m_xRot < -90:
                self.m_xRot = -90
            if self.m_xRot > 90:
                self.m_xRot = 90

            self.updateView()
            self.rotationChanged.emit()

        if (
            event.buttons() & QtCore.Qt.MiddleButton
            and event.modifiers() & QtGui.Qt.ShiftModifier
        ) or event.buttons() & QtCore.Qt.RightButton:
            self.m_xPan = self.m_xLastPan - (
                event.position().x() - self.m_lastPos.x()
            ) * 1 / (float)(self.width())
            self.m_yPan = self.m_yLastPan + (
                event.position().y() - self.m_lastPos.y()
            ) * 1 / (float)(self.height())

            self.updateProjection()

        self.update()

    def wheelEvent(self, we: QtGui.QWheelEvent):
        if self.m_zoom > 0.001 and we.angleDelta().y() < 0:
            self.m_xPan -= (
                (float)(we.position().x() / self.width() - 0.5 + self.m_xPan)
            ) * (1 - 1 / ZOOMSTEP)
            self.m_yPan += (
                (float)(we.position().y() / self.height() - 0.5 - self.m_yPan)
            ) * (1 - 1 / ZOOMSTEP)

            self.m_zoom /= ZOOMSTEP
        elif self.m_zoom < 10 and we.angleDelta().y() > 0:
            self.m_xPan -= (
                (float)(we.position().x() / self.width() - 0.5 + self.m_xPan)
            ) * (1 - ZOOMSTEP)
            self.m_yPan += (
                (float)(we.position().y() / self.height() - 0.5 - self.m_yPan)
            ) * (1 - ZOOMSTEP)

            self.m_zoom *= ZOOMSTEP

        self.updateProjection()
        self.updateView()

        self.update()

    def onVisualizatorRotationChanged(self):
        self.update()

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------

    def sizeHint(self):
        return QSize(800, 800)

    def cleanup(self):
        self.makeCurrent()
        self.drawable.clean()
        self.doneCurrent()

    def initializeGL(self):
        self.context().aboutToBeDestroyed.connect(self.cleanup)
        self.initializeOpenGLFunctions()
        self.glClearColor(0.2, 0.7, 0.7, 1)

        self.drawable.initialize()

    def paintGL(self):
        self.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        self.glEnable(GL.GL_DEPTH_TEST)

        self.drawable.draw(self)

        self.updateProjection()
        self.updateView()

        #self.update()

    def resizeGL(self, width, height):
        self.glViewport(0, 0, width, height)

        ratio = width / float(height)
        self.drawable.proj.perspective(45.0, ratio, 2.0, 100.0)

        self.update()

    def setStopAtTime(self, stopAtTime: float):
        self.drawable.stopAtTime = stopAtTime
        self.update()


class MainWindow(QMainWindow):
    """ """

    update_gl_scene = QtCore.Signal()

    def __init__(self, gcode):
        QMainWindow.__init__(self)

        self.gcode = gcode

        self.layout = QtWidgets.QVBoxLayout()
        self.centralwidget = QtWidgets.QWidget()

        self.gl_widget = GLWidget(gcode)
        self.control = self.loadUi("simcontrolwidget.ui", self)

        self.layout.addWidget(self.gl_widget)
        self.layout.addWidget(self.control)

        self.layout.setStretch(0, 1)

        self.centralwidget.setLayout(self.layout)
        self.setCentralWidget(self.centralwidget)
        self.setWindowTitle(self.tr("Hello GL"))

        #self.control.pushButton_ToEnd.clicked.connect(self.OnSimToEnd)
        #self.control.pushButton_Rewind.clicked.connect(self.OnSimRewind)
        #self.control.pushButton_Run.clicked.connect(self.OnSimRun)
        #self.control.pushButton_Pause.clicked.connect(self.OnSimPause)

        self.slider_start = 0
        self.slider_end = int(self.gl_widget.drawable.scene.totalTime * 1000)
        self.slider_tick = 1

        self.control.horizontalSlider_Position.setMinimum(self.slider_start)
        self.control.horizontalSlider_Position.setMaximum(self.slider_end)
        self.control.horizontalSlider_Position.setSingleStep(self.slider_tick)
        self.control.horizontalSlider_Position.valueChanged.connect(self.OnSimAtTick)

        #self.control.spinBox_SpeedFactor.valueChanged.connect(self.OnSpeedChange)

    def loadUi(self, uifile, baseinstance=None):
        """ """
        loader = QUiLoader(baseinstance)

        widget = loader.load(uifile)

        return widget

    """
    def OnSimToEnd(self):
        timer_on = self.simulation.timer_on
    
        if timer_on:
            self.simulation.stop_timer()
    
        self.simulation.set_current_time(self.sim_end)
    
        if timer_on:
            self.simulation.start_timer()

    def OnSimRewind(self):
        timer_on = self.simulation.timer_on

        if timer_on:
            self.simulation.stop_timer()

        self.simulation.set_current_time(self.sim_start)

        if timer_on:
            self.simulation.start_timer()
    """

    def OnSimAtTick(self, tick: int):
        self.gl_widget.setStopAtTime(tick / 1000.0)

    """
    def OnSimRun(self):
        self.simulation.start_timer()

    def OnSimPause(self):
        self.simulation.stop_timer()

    def OnSpeedChange(self, value: int):
        self.simulation.set_speed(int(value))
    """


if __name__ == "__main__":
    app = QApplication(sys.argv)

    gcodefile = sys.argv[1]

    fp = open(gcodefile, "r")
    gcode = fp.read()
    fp.close()

    main_window = MainWindow(gcode)
    main_window.show()

    res = app.exec()
    sys.exit(res)