# Copyright 2014 Xavier
#
# This file is part of pycut.
#
# pycut is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pycut is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pycut.  If not, see <http:#www.gnu.org/licenses/>.

import sys

from typing import List
from typing import Dict
from typing import Tuple

from val_with_unit import ValWithUnit

import shapely.geometry
import shapely.ops

from shapely_utils import ShapelyUtils
from shapely_ext import ShapelyMultiPolygonOffset
from shapely_ext import ShapelyMultiPolygonOffsetInteriors

from matplotlib_utils import MatplotLibUtils


class CamPath:
    '''
    CamPath has this format: {
      path:               Shapely LineString
      safeToClose:        Is it safe to close the path without retracting?
    }
    '''
    def __init__(self, path: shapely.geometry.LineString, safeToClose: bool = True):
        # shapely linestring
        self.path = path
        # is it safe to close the path without retracting?
        self.safeToClose = safeToClose


class cam:
    '''
    '''
    @classmethod
    def pocket(cls, multipoly: shapely.geometry.MultiPolygon, cutter_dia: float, overlap: float, climb: bool) -> List[CamPath] :
        '''
        Compute paths for pocket operation on Shapely multipolygon. 
        
        Returns array of CamPath.
        
        cutter_dia is in "UserUnit" units. 
        overlap is in the range [0, 1).
        '''
        pc = pocket_calculator(multipoly, cutter_dia, overlap, climb)
        pc.pocket()
        return pc.cam_paths

    @classmethod
    def outline(cls, geometry: shapely.geometry.MultiPolygon, cutter_dia: float, isInside: bool, width: float, overlap: float, climb: bool) -> List[CamPath] :
        '''
        Compute paths for outline operation on Shapely geometry. 
        
        Returns array of CamPath.
        
        cutter_dia and width are in Shapely units. 
        overlap is in the  range [0, 1).
        '''
        # use lines, not polygons
        multiline = ShapelyUtils.multiPolyToMultiLine(geometry)

        currentWidth = cutter_dia
        allPaths  : List[shapely.geometry.LineString] = []
        eachWidth = cutter_dia * (1 - overlap)

        if isInside :
            # because we always start from the outer ring -> we go "inside"
            current = ShapelyUtils.offsetMultiLine(multiline, cutter_dia /2, 'left')
            offset = ShapelyUtils.offsetMultiLine(multiline, width - cutter_dia / 2, 'left')
            #bounds = ShapelyUtils.diff(current, offset)
            bounds = current
            eachOffset = eachWidth
            needReverse = climb
        else :
            direction = "inner2outer"
            #direction = "outer2inner"

            if direction == "inner2outer":
                # because we always start from the inner ring -> we go "outside"
                current = ShapelyUtils.offsetMultiLine(multiline, cutter_dia /2, 'right')
                offset = ShapelyUtils.offsetMultiLine(multiline, width - cutter_dia / 2, 'right')
                #bounds = ShapelyUtils.diff(current, offset)
                bounds = current
            else:
                # because we always start from the outer ring -> we go "inside"
                current = ShapelyUtils.offsetMultiLine(multiline, cutter_dia /2, 'left')
                offset = ShapelyUtils.offsetMultiLine(multiline, width - cutter_dia / 2, 'left')
                #bounds = ShapelyUtils.diff(current, offset)
                bounds = current

            eachOffset = eachWidth
            needReverse = not climb

            # TEST
            #allPaths = [p for p in current.geoms] 

        while True and currentWidth <= width :
            if needReverse:
                reversed = []
                for path in current.geoms:
                    coords = list(path.coords)  # is a tuple!  JSCUT current reversed in place
                    coords.reverse()
                    reversed.append(shapely.geometry.LineString(coords))
                allPaths = reversed + allPaths  # JSCUT: allPaths = current.concat(allPaths)
            else:
                allPaths = [p for p in current.geoms] + allPaths  # JSCUT: allPaths = current.concat(allPaths)

            nextWidth = currentWidth + eachWidth
            if nextWidth > width and (width - currentWidth) > 0 :
                # >>> XAM fix
                last_delta = width - currentWidth
                # <<< XAM fix
                current = ShapelyUtils.offsetMultiLine(current, last_delta, 'left')
                if current :
                    current = ShapelyUtils.simplifyMultiLine(current, 0.01)
                
                if current:
                    if needReverse:
                        reversed = []
                        for path in current.geoms:
                            coords = list(path.coords)  # is a tuple!  JSCUT current reversed in place
                            coords.reverse()
                            reversed.append(shapely.geometry.LineString(coords))
                        allPaths = reversed + allPaths # JSCUT: allPaths = current.concat(allPaths)
                    else:
                        allPaths = [p for p in current.geoms] + allPaths # JSCUT: allPaths = current.concat(allPaths)
                    break
            
            currentWidth = nextWidth

            if not current:
                break

            current = ShapelyUtils.offsetMultiLine(current, eachOffset, 'left', resolution=16)
            if current:
                current = ShapelyUtils.simplifyMultiLine(current, 0.01)
                print("--- next toolpath")
            else:
                break

        if len(allPaths) == 0: 
            # no possible paths! TODO . inform user
            return []

        # mergePaths need MultiPolygon
        bounds = ShapelyUtils.multiLineToMultiPoly(bounds)

        return cls.mergePaths(bounds, allPaths)
        
    @classmethod
    def engrave(cls, geometry: shapely.geometry.MultiPolygon, climb: bool) -> List[CamPath] :
        '''
        Compute paths for engrave operation on Shapely multipolygon. 
        
        Returns array of CamPath.
        '''
        # use lines, not polygons
        multiline_ext = ShapelyUtils.multiPolyToMultiLine(geometry)
        multiline_int = ShapelyUtils.multiPolyIntToMultiLine(geometry)

        full_line = shapely.ops.linemerge(list(multiline_ext.geoms) + list(multiline_int.geoms))

        if full_line.geom_type == 'LineString':
            camPaths = [ CamPath( full_line, False) ]
            return camPaths

        allPaths = []
        for line in full_line.geoms:
            coords = list(line.coords)  # JSCUT: path = paths.slice(0)
            if not climb:
                coords.reverse()
        
            coords.append(coords[0])
            allPaths.append(shapely.geometry.LineString(coords))
            
        camPaths = [ CamPath(path, False)  for path in allPaths ]
        return camPaths

    @classmethod
    def mergePaths(cls, _bounds: shapely.geometry.MultiPolygon, paths: List[shapely.geometry.LineString]) -> List[CamPath] :
        '''
        Try to merge paths. A merged path doesn't cross outside of bounds AND the interior polygons
        '''
        #MatplotLibUtils.MatplotlibDisplay("mergePath", shapely.geometry.MultiLineString(paths), force=True)

        if _bounds and len(_bounds.geoms) > 0:
            bounds = _bounds
        else: 
            bounds = shapely.geometry.MultiPolygon()
 
 
        ext_lines = ShapelyUtils.multiPolyToMultiLine(bounds)
        int_polys = []
        for poly in bounds.geoms:
            if poly.interiors:
                for interior in poly.interiors:
                    int_poly = shapely.geometry.Polygon(interior)
                    int_polys.append(int_poly)
        if int_polys:
            int_multipoly = shapely.geometry.MultiPolygon(int_polys)
        else:
            int_multipoly = None

        # std list
        thepaths = [ list(path.coords) for path in paths ]

        #####
        #thepaths = thepaths[19:22]
        #####

        paths = thepaths

        currentPath = paths[0]
        
        pathEndPoint = currentPath[-1]
        pathStartPoint = currentPath[0]

        # close if start/end point not equal - why ? I could have simple lines!
        if pathEndPoint[0] != pathStartPoint[0] or pathEndPoint[1] != pathStartPoint[1]:
            currentPath = currentPath + [pathStartPoint]
        
        currentPoint = currentPath[-1]
        paths[0] = [] # empty

        mergedPaths : List[shapely.geometry.LineString] = [] 
        numLeft = len(paths) - 1

        while numLeft > 0 :
            closestPathIndex = None
            closestPointIndex = None
            closestPointDist = sys.maxsize
            for pathIndex, path in enumerate(paths):
                for pointIndex, point in enumerate(path):
                    dist = cam.distP(currentPoint, point)
                    if dist < closestPointDist:
                        closestPathIndex = pathIndex
                        closestPointIndex = pointIndex
                        closestPointDist = dist

            path = paths[closestPathIndex]
            paths[closestPathIndex] = [] # empty
            numLeft -= 1
            needNew = ShapelyUtils.crosses(ext_lines, currentPoint, path[closestPointIndex])
            if (not needNew) and int_multipoly:
                needNew = ShapelyUtils.crosses(int_multipoly, currentPoint, path[closestPointIndex])

            # JSCUT path = path.slice(closestPointIndex, len(path)).concat(path.slice(0, closestPointIndex))
            path = path[closestPointIndex:] + path[:closestPointIndex]
            path.append(path[0])

            if needNew:
                mergedPaths.append(currentPath)
                currentPath = path
                currentPoint = currentPath[-1]
            else:
                currentPath = currentPath + path
                currentPoint = currentPath[-1]

        mergedPaths.append(currentPath)

        camPaths : List[CamPath] = []
        for path in mergedPaths:
            safeToClose = not ShapelyUtils.crosses(bounds, path[0], path[-1])
            camPaths.append( CamPath( shapely.geometry.LineString(path), safeToClose) )

        return camPaths

    @classmethod
    def separateTabs(cls, origPath: shapely.geometry.LineString, tabs: List['Tab']) -> List[shapely.geometry.LineString]:
        '''
        from a "normal" tool path, split this path into a list of "partial" paths
        avoiding the tabs areas
        '''
        from gcode_generator import Tab

        if len(tabs) == 0:
            return [origPath]

        pts = list(origPath.coords)

        shapely_openpath = shapely.geometry.LineString(pts)

        #print("origPath", origPath)
        #print("origPath", shapely_openpath)
         
        shapely_tabs_ = []
        # 1. from the tabs, build shapely (closed) tab polygons
        for tab_data in tabs:
            tab = Tab(tab_data)
            shapely_tabs = tab.svg_path.toShapelyPolygons()
            shapely_tabs_ += shapely_tabs

        # hey, multipolygons are good...
        shapely_tabs = shapely.geometry.MultiPolygon(shapely_tabs_)

        # 2. then "diff" the origin path with the tabs paths
        shapely_splitted_paths = shapely_openpath.difference(shapely_tabs)

        # 3. that's it
        #print("splitted_paths", shapely_splitted_paths)

        if shapely_splitted_paths.geom_type == 'LineString':
            shapely_splitted_paths = shapely.geometry.MultiLineString([shapely_splitted_paths])

        # back to shapely...
        paths : List[shapely.geometry.LineString] = []
        for shapely_splitted_path in shapely_splitted_paths.geoms:
            intpt_vector = []
            xy = shapely_splitted_path.xy
            for ptX, ptY in zip(xy[0], xy[1]):
                intpt_vector.append((ptX, ptY))
            paths.append(intpt_vector)
        
        # >>> XAM merge some paths when possible
        paths = cls.mergeCompatiblePaths(paths)
        # <<< XAM

        shapely_paths = [shapely.geometry.LineString(path) for path in paths]
        return shapely_paths

    @classmethod
    def mergeCompatiblePaths(cls, paths: List[shapely.geometry.LineString]) -> List[shapely.geometry.LineString]:
        '''
        This is a post-processing step to clipper-6.4.2 where found separated paths can be merged together,
        leading to less separated paths
        '''
        # ------------------------------------------------------------------------------------------------
        def pathsAreCompatible(path1: shapely.geometry.LineString, path2: shapely.geometry.LineString) -> bool:
            '''
            test if the 2 paths have their end point/start point compatible (the same)
            '''
            endPoint = path1[-1]
            startPoint = path2[0]

            if endPoint[0] == startPoint[0] and endPoint[1] == startPoint[1]:
                # can merge
                return True

            return False

        def mergePathIntoPath(path1: shapely.geometry.LineString, path2: shapely.geometry.LineString) -> bool:
            '''
            merge the 2 paths if their end point/start point are compatible (ie the same)
            '''
            endPoint = path1[-1]
            startPoint = path2[0]

            if endPoint[0] == startPoint[0]and endPoint[1] == startPoint[1]:
                # can merge
                path1 += path2[1:]
                return True

        def buildPathsCompatibilityTable(paths: List[shapely.geometry.LineString]) -> Dict[List,int]:
            '''
            for all paths in the list of paths, check first which ones can be merged
            '''
            compatibility_table = {}

            for i, path in enumerate(paths):
                for j, other_path in enumerate(paths):
                    if i == j:
                       continue
                    rc = pathsAreCompatible(path, other_path)
                    if rc:
                        if i in compatibility_table:
                            compatibility_table[i].append(j)
                        else: 
                            compatibility_table[i] = [j]
        
            return compatibility_table
        # ------------------------------------------------------------------------------------------------

        if len(paths) <= 1:
            return paths

        compatibility_table = buildPathsCompatibilityTable(paths)

        while len(compatibility_table) > 0:
            i = list(compatibility_table.keys())[0]
            path = paths[i]
            j = compatibility_table[i][0]
            path_to_be_merged = paths.pop(j)
            mergePathIntoPath(path, path_to_be_merged)
            compatibility_table = buildPathsCompatibilityTable(paths)

        return paths

    @staticmethod
    def dist(x1: float, y1: float, x2: float, y2: float) -> float :
        dx = x2 - x1
        dy = y2 - y1
        return dx * dx + dy * dy
    
    @staticmethod
    def distP(p1:Tuple[int,int], p2:Tuple[int,int]) -> float :
        return cam.dist(p1[0], p1[1], p2[0], p2[1])
    
    @classmethod
    def getGcode(cls, args):
        '''
        Convert paths to gcode. getGcode() assumes that the current Z position is at safeZ.
        getGcode()'s gcode returns Z to this position at the end.
        args must have:
          paths:          Array of CamPath
          ramp:           Ramp these paths?
          scale:          Factor to convert Clipper units to gcode units
          offsetX:        Offset X (gcode units)
          offsetY:        Offset Y (gcode units)
          decimal:        Number of decimal places to keep in gcode
          topZ:           Top of area to cut (gcode units)
          botZ:           Bottom of area to cut (gcode units)
          safeZ:          Z position to safely move over uncut areas (gcode units)
          passDepth:      Cut depth for each pass (gcode units)
          plungeFeed:     Feedrate to plunge cutter (gcode units)
          retractFeed:    Feedrate to retract cutter (gcode units)
          cutFeed:        Feedrate for horizontal cuts (gcode units)
          rapidFeed:      Feedrate for rapid moves (gcode units)
          tabs:           List of tabs
          tabZ:           Level below which tabs are to be processed
          flipXY          toggle X with Y
        '''
        paths : List[CamPath] = args["paths"]
        ramp = args["ramp"]
        scale = args["scale"]
        offsetX = args["offsetX"]
        offsetY = args["offsetY"]
        decimal = args["decimal"]
        topZ = args["topZ"]
        botZ = args["botZ"]
        safeZ = args["safeZ"]
        passDepth = args["passDepth"]
        
        plungeFeedGcode = ' F%d' % args["plungeFeed"]
        retractFeedGcode = ' F%d' % args["retractFeed"]
        cutFeedGcode = ' F%d' % args["cutFeed"]
        rapidFeedGcode = ' F%d' % args["rapidFeed"]

        plungeFeed = args["plungeFeed"]
        retractFeed = args["retractFeed"]
        cutFeed = args["cutFeed"]
        rapidFeed = args["rapidFeed"]

        tabs = args["tabs"]
        tabZ = args["tabZ"]

        flipXY = args["flipXY"]

        gcode = ""

        retractGcode = '; Retract\r\n' + \
            f'G1 Z' + safeZ.toFixed(decimal) + f'{rapidFeedGcode}\r\n'

        retractForTabGcode = '; Retract for tab\r\n' + \
            f'G1 Z' + tabZ.toFixed(decimal) + f'{rapidFeedGcode}\r\n'

        def getX(p: Tuple[int,int]) :
            return p[0] * scale + offsetX

        def getY(p : Tuple[int,int]):
            return -p[1] * scale + offsetY

        def convertPoint(p: Tuple[int,int]):
            x = p[0] * scale + offsetX
            y = -p[1] * scale + offsetY

            if flipXY is False:
                result = ' X' + ValWithUnit(x, "-").toFixed(decimal) +  \
                         ' Y' + ValWithUnit(y, "-").toFixed(decimal)
            else:
                result = ' X' + ValWithUnit(-y, "-").toFixed(decimal) +  \
                         ' Y' + ValWithUnit(x, "-").toFixed(decimal)

            return result

        # tabs are globals - bau maybe with path does not hits tabs
        has_active_tabs = len(tabs) > 0
        # --> has_active_tabs will be fixed later

        for pathIndex, path in enumerate(paths):
            origPath = path.path
            if len(origPath.coords) == 0:
                continue

            # split the path to cut into many partials paths to avoid tabs eraas
            #separatedPaths = cls.separateTabs(origPath, tabs)
            separatedPaths = cls.separateTabs(origPath, tabs)

            # tabs are globals and may not hit the origPath -> no "active tabs"
            if len(separatedPaths) == 1:
                has_active_tabs = False
            else:
                has_active_tabs = True

            gcode += \
                f'\r\n' + \
                f'; Path {pathIndex+1}\r\n'

            currentZ = safeZ
            finishedZ = topZ

            # need to cut at tabZ if tabs there
            exactTabZLevelDone = False

            while finishedZ > botZ:
                nextZ = max(finishedZ - passDepth, botZ)

                if has_active_tabs:
                    if nextZ == tabZ:
                        exactTabZLevelDone = True
                    elif nextZ < tabZ:
                        # a last cut at the exact tab height withput tabs 
                        if exactTabZLevelDone == False:
                            nextZ = tabZ
                            exactTabZLevelDone = True


                if (currentZ <= tabZ and ((not path.safeToClose) or has_active_tabs)) :
                    gcode += retractGcode
                    currentZ = safeZ
                elif (currentZ < safeZ and (not path.safeToClose)) :
                    gcode += retractGcode
                    currentZ = safeZ

                # check this - what does it mean ???
                if not has_active_tabs:
                    currentZ = finishedZ
                else:
                    currentZ = max(finishedZ, tabZ)
                
                gcode += '; Rapid to initial position\r\n' + \
                    'G1' + convertPoint(list(origPath.coords)[0]) + rapidFeedGcode + '\r\n'

                inTabsHeight = False
                
                if not has_active_tabs:
                    inTabsHeight = False
                    selectedPaths = [origPath]
                    gcode += 'G1 Z' + ValWithUnit(currentZ, "-").toFixed(decimal) + '\r\n'
                else:
                    if nextZ >= tabZ:
                        inTabsHeight = False
                        selectedPaths = [origPath]
                        gcode += 'G1 Z' + ValWithUnit(currentZ, "-").toFixed(decimal) + '\r\n'
                    else:
                        inTabsHeight = True
                        selectedPaths = separatedPaths

                for selectedPath in selectedPaths:
                    if selectedPath.is_empty:
                        continue

                    executedRamp = False
                    minPlungeTime = (currentZ - nextZ) / plungeFeed
                    if ramp and minPlungeTime > 0:
                        minPlungeTime = (currentZ - nextZ) / plungeFeed
                        idealDist = cutFeed * minPlungeTime
                        totalDist = 0
                        for end in range(1, len(list(selectedPath.coords))):
                            if totalDist > idealDist:
                                break

                            pt1 = list(selectedPath.coords)[end - 1]
                            pt2 = list(selectedPath.coords)[end]
                            totalDist += 2 * cam.dist(getX(pt1), getY(pt1), getX(pt2), getY(pt2))
                                
                        if totalDist > 0:
                            gcode += '; ramp\r\n'
                            executedRamp = True
                                    
                            #rampPath = selectedPath.slice(0, end)
                            rampPath = [ list(selectedPath.coords)[k] for k in range(0,end) ] 

                            #rampPathEnd = selectedPath.slice(0, end - 1).reverse()
                            rampPathEnd = [ list(selectedPath.coords)[k] for k in range(0,end-1) ]
                            rampPathEnd.reverse()

                            rampPath = rampPath + rampPathEnd
                                
                            distTravelled = 0
                            for i in range(1,len(rampPath)):
                                distTravelled += cam.dist(getX(rampPath[i - 1]), getY(rampPath[i - 1]), getX(rampPath[i]), getY(rampPath[i]))
                                newZ = currentZ + distTravelled / totalDist * (nextZ - currentZ)
                                gcode += 'G1' + convertPoint(rampPath[i]) + ' Z' + ValWithUnit(newZ, "-").toFixed(decimal)
                                if i == 1:
                                    gcode += ' F' + ValWithUnit(min(totalDist / minPlungeTime, cutFeed), "-").toFixed(decimal) + '\r\n'
                                else:
                                    gcode += '\r\n' 

                    if not inTabsHeight:
                        if not executedRamp:
                            gcode += \
                                '; plunge\r\n' + \
                                'G1 Z' + ValWithUnit(nextZ, "-").toFixed(decimal) + plungeFeedGcode + '\r\n'

                    if inTabsHeight:
                        # move to initial point of partial path
                        gcode += '; Tab: move to first point of partial path at safe height \r\n'
                        gcode += 'G1' + convertPoint(list(selectedPath.coords)[0]) + '\r\n'
                        gcode += \
                            '; plunge\r\n' + \
                            'G1 Z' + ValWithUnit(nextZ, "-").toFixed(decimal) + plungeFeedGcode + '\r\n'

                    currentZ = nextZ

                    gcode += '; cut\r\n'

                    # on a given height, generate series of G1
                    for i, pt in enumerate(selectedPath.coords):
                        if i == 0:
                            continue
                        
                        gcode += 'G1' + convertPoint(pt)
                        if i == 1:
                            gcode += cutFeedGcode + '\r\n'
                        else:
                            gcode += '\r\n'
                    
                    if inTabsHeight:
                        # retract to safeZ before processing next separatedPath
                        gcode += retractGcode

                finishedZ = nextZ
            
            gcode += retractGcode

        return gcode
    





class pocket_calculator:
    '''
    '''
    def __init__(self, multipoly: shapely.geometry.MultiPolygon, cutter_dia: float, overlap: float, climb: bool):
        '''
        cutter_dia is in user units. 
        overlap is in the range [0, 1].
        '''
        self.multipoly = multipoly

        self.cutter_dia = cutter_dia
        self.overlap = overlap
        self.climb = climb

        self.resolution = 16
        self.join_style = 1
        self.mitre_limit = 5.0


        # result of a the calculation
        self.cam_paths : List[CamPath] = [] 

        # temp variables
        self.all_paths : List[shapely.geometry.LineString] = []

    def pocket(self):
        '''
        main algo
        '''
        # use polygons exteriors lines - offset them and and diff with the offseted interiors if any
        multipoly = ShapelyUtils.orientMultiPolygon(self.multipoly)
        
        MatplotLibUtils.MatplotlibDisplay("multipoly pocket init", self.multipoly)
        
        # the exterior
        current = self.offsetMultiPolygon(multipoly, self.cutter_dia / 2, 'left', consider_interiors_offsets=True)
        
        MatplotLibUtils.MatplotlibDisplay("multipoly pocket first offset", current, force=False)

        if len(current.geoms) == 0:
            # cannot offset ! maybe geometry too narrow for the cutter
            return []
                
        # bound must be the exterior enveloppe + the interiors polygons
        # no! the bounds are from the first offset with width cutter_dia / 2
        #bounds = multipoly 
        bounds = shapely.geometry.MultiPolygon(current)

        # --------------------------------------------------------------------
      
        while True:
            #if climb:
            #    for line in current:
            #        line.reverse()

            exteriors = ShapelyUtils.multiPolyToMultiLine(current)

            self.collectPaths(exteriors)

            current = self.offsetMultiPolygon(current, self.cutter_dia * (1 - self.overlap), 'left', consider_interiors_offsets=False)
            
            if not current:
                break
            current = ShapelyUtils.simplifyMultiPoly(current, 0.001)
            if not current:
                break
            current = ShapelyUtils.orientMultiPolygon(current)

        # last: make beautiful interiors, only 1 step
        interiors = self.offsetMultiPolygonInteriors(multipoly, self.cutter_dia / 2, 'left', consider_exteriors_offsets=True)
        interiors_offsets = ShapelyUtils.multiPolyToMultiLine(interiors)
        self.collectPaths(interiors_offsets)
        # - done !

        self.mergePaths(bounds, self.all_paths)
 
    def offsetMultiPolygon(self, multipoly: shapely.geometry.MultiPolygon, amount: float, side: str, consider_interiors_offsets=False) -> shapely.geometry.MultiPolygon:
        '''
        Generate offseted polygons.
        '''
        offseter = ShapelyMultiPolygonOffset(multipoly)
        return offseter.offset(amount, side, consider_interiors_offsets, self.resolution, self.join_style, self.mitre_limit)

    def offsetMultiPolygonInteriors(self, multipoly: shapely.geometry.MultiPolygon, amount: float, side: str, consider_exteriors_offsets=False) -> shapely.geometry.MultiPolygon:
        '''
        Generate offseted polygons from the polygons interiors
        '''
        offseter = ShapelyMultiPolygonOffsetInteriors(multipoly)
        return offseter.offset(amount, side, consider_exteriors_offsets, self.resolution, self.join_style, self.mitre_limit)

    def collectPaths(self, multiline: shapely.geometry.MultiLineString):
        '''
        ''' 
        lines_ok = []
            
        for line in multiline.geoms:
            if len(list(line.coords)) > 0:
                lines_ok.append(line)

        self.all_paths = lines_ok + self.all_paths
  
    def mergePaths(self, _bounds: shapely.geometry.MultiPolygon, paths: List[shapely.geometry.LineString]) -> List[CamPath] :
        '''
        Try to merge paths. A merged path doesn't cross outside of bounds AND the interior polygons
        '''
        #MatplotLibUtils.MatplotlibDisplay("mergePath", shapely.geometry.MultiLineString(paths), force=True)

        if _bounds and len(_bounds.geoms) > 0:
            bounds = _bounds
        else: 
            bounds = shapely.geometry.MultiPolygon()
 
 
        ext_lines = ShapelyUtils.multiPolyToMultiLine(bounds)
        int_polys = []
        for poly in bounds.geoms:
            if poly.interiors:
                for interior in poly.interiors:
                    int_poly = shapely.geometry.Polygon(interior)
                    int_polys.append(int_poly)
        if int_polys:
            int_multipoly = shapely.geometry.MultiPolygon(int_polys)
        else:
            int_multipoly = None

        # std list
        thepaths = [ list(path.coords) for path in paths ]
        paths = thepaths

        currentPath = paths[0]
        
        pathEndPoint = currentPath[-1]
        pathStartPoint = currentPath[0]

        # close if start/end point not equal - why ? I could have simple lines!
        if pathEndPoint[0] != pathStartPoint[0] or pathEndPoint[1] != pathStartPoint[1]:
            currentPath = currentPath + [pathStartPoint]
        
        currentPoint = currentPath[-1]
        paths[0] = [] # empty

        mergedPaths : List[shapely.geometry.LineString] = [] 
        numLeft = len(paths) - 1

        while numLeft > 0 :
            closestPathIndex = None
            closestPointIndex = None
            closestPointDist = sys.maxsize
            for pathIndex, path in enumerate(paths):
                for pointIndex, point in enumerate(path):
                    dist = pocket_calculator.distP(currentPoint, point)
                    if dist < closestPointDist:
                        closestPathIndex = pathIndex
                        closestPointIndex = pointIndex
                        closestPointDist = dist

            path = paths[closestPathIndex]
            paths[closestPathIndex] = [] # empty
            numLeft -= 1
            needNew = ShapelyUtils.crosses(ext_lines, currentPoint, path[closestPointIndex])
            if (not needNew) and int_multipoly:
                needNew = ShapelyUtils.crosses(int_multipoly, currentPoint, path[closestPointIndex])

            # JSCUT path = path.slice(closestPointIndex, len(path)).concat(path.slice(0, closestPointIndex))
            path = path[closestPointIndex:] + path[:closestPointIndex]
            path.append(path[0])

            if needNew:
                mergedPaths.append(currentPath)
                currentPath = path
                currentPoint = currentPath[-1]
            else:
                currentPath = currentPath + path
                currentPoint = currentPath[-1]

        mergedPaths.append(currentPath)

        cam_paths : List[CamPath] = []
        for path in mergedPaths:
            safeToClose = not ShapelyUtils.crosses(bounds, path[0], path[-1])
            cam_paths.append( CamPath( shapely.geometry.LineString(path), safeToClose) )

        self.cam_paths = cam_paths

    @staticmethod
    def dist(x1: float, y1: float, x2: float, y2: float) -> float :
        dx = x2 - x1
        dy = y2 - y1
        return dx * dx + dy * dy
    
    @staticmethod
    def distP(p1:Tuple[int,int], p2:Tuple[int,int]) -> float :
        return pocket_calculator.dist(p1[0], p1[1], p2[0], p2[1])
   