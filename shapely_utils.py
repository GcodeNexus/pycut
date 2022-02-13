
import math

from typing import List
from typing import Tuple

import shapely.geometry
from shapely.validation import make_valid

import matplotlib.pyplot as plt


class ShapelyUtils:
    '''
    Helper functions on Shapely
    '''
    MAPLOTLIB_DEBUG = False
    #MAPLOTLIB_DEBUG = True
    cnt = 1

    @classmethod
    def diff(cls, paths1: shapely.geometry.MultiLineString, paths2: shapely.geometry.MultiLineString) -> shapely.geometry.MultiLineString:
        '''
        Return difference between to Clipper geometries. Returns new geometry.
        '''
        diffs = [path1.difference(path2) for (path1,path2) in zip(paths1.geoms, paths2.geoms) ]

        return shapely.geometry.MultiLineString(diffs)

    @classmethod
    def simplifyMultiLine(cls, multiline: shapely.geometry.MultiLineString, tol: float) -> shapely.geometry.MultiLineString:
        '''
        '''
        lines = []
        for line in multiline.geoms:
            xline = line.simplify(tol)
            if xline:
                lines.append(xline)
        
        if lines:
            res = shapely.geometry.MultiLineString(lines)
        else:
            res = None

        return res

    @classmethod
    def simplifyOffset(cls, offset: any, tol: float) -> shapely.geometry.MultiLineString:
        '''
        '''
        geoms = []
        for geom in offset.geoms:
            if geom.geom_type == 'LineString':
                simplified_geom = geom.simplify(tol)
                geoms.append(simplified_geom)
            if geom.geom_type == 'MultiLineString':
                for linestring in geom.geoms:
                    simplified_linestring = linestring.simplify(tol)
                    geoms.append(simplified_linestring)

        return geoms

    @classmethod
    def simplifyMultiOffset(cls, multi_offset: List[any], tol: float) -> shapely.geometry.MultiLineString:
        '''
        '''
        multi_offset_simplify = []
        for offset in multi_offset:
            simplified_offset = cls.simplifyOffset(offset)
            if simplified_offset:
                multi_offset_simplify.append(simplified_offset)

        return multi_offset_simplify

    @classmethod
    def simplifyMultiPoly(cls, multipoly: shapely.geometry.MultiPolygon, tol: float) -> shapely.geometry.MultiPolygon:
        '''
        '''
        polys = []
        for poly in multipoly.geoms:
            xpoly = poly.simplify(tol)
            if xpoly:
                polys.append(xpoly)
        
        if polys:
            res = shapely.geometry.MultiPolygon(polys)
        else:
            res = None

        return res

    @classmethod
    def offsetLine(cls, line: shapely.geometry.LineString, amount: float, side: str, resolution=16, join_style=1, mitre_limit=5.0) -> shapely.geometry.LineString:
        '''
        '''
        return line.parallel_offset(amount, side, resolution=resolution, join_style=join_style, mitre_limit=mitre_limit)

    @classmethod
    def offsetMultiLine(cls, multiline: shapely.geometry.MultiLineString, amount: float, side: str, resolution=16, join_style=1, mitre_limit=5.0) -> shapely.geometry.MultiLineString:
        '''
        '''
        offseted_lines = [cls.offsetLine(line, amount, side, resolution, join_style, mitre_limit) for line in multiline.geoms ]
        
        # resulting linestring can be empty
        filtered_lines = []
        
        for geom in offseted_lines:
            if geom.geom_type == 'LineString':
                if geom.is_empty:
                    continue
                filtered_lines.append(geom)
            if geom.geom_type == 'MultiLineString':
                for line in geom.geoms:
                    if line.is_empty:
                        continue
                    filtered_lines.append(line)
         
        if len(filtered_lines) == 0:
            return None

        offsetted = shapely.geometry.MultiLineString(filtered_lines)

        return offsetted

    @classmethod
    def orientMultiPolygon(cls, multipoly: shapely.geometry.MultiPolygon):
        '''
        '''
        geoms = []
        for geom in multipoly.geoms:
            xgeom = shapely.geometry.polygon.orient(geom)
            geoms .append(xgeom)
        xmultipoly = shapely.geometry.MultiPolygon(geoms)

        return xmultipoly

    @classmethod
    def offsetMultiPolygon(cls, geometry: shapely.geometry.MultiPolygon, amount: float, side, ginterior=False, resolution=16, join_style=1, mitre_limit=5.0) -> List[shapely.geometry.MultiLineString] :
        '''
        Generate offseted lines from the polygons. All the produced lines are good 
        to store in the toolpaths.

        But for the next offset step, remove the degenerated lines from this set
        to construct a valid multipolygon that we can offset.
        '''
        multi_offset = [] # for each poly in the multipoly - each item can be of various types

        for poly in geometry.geoms:

            linestring = cls.polyExteriorToLineString(poly)

            offset = linestring.parallel_offset(amount, side, resolution=resolution, join_style=join_style, mitre_limit=5.0)

            if poly.interiors: # with interiors
                # from the offseted lines, build a multipolygon that we diff with the interiors
                exterior_multipoly = cls.buildMultiPolyFromOffset([offset])
                print("multipoly VALID ? ", exterior_multipoly.is_valid)

                exterior_multipoly = cls.fixMultipoly(exterior_multipoly)

                # with interiors
                interior_polys = []
                for interior in poly.interiors:
                    ipoly = shapely.geometry.Polygon(interior)
                    print("ipoly VALID ? ", ipoly.is_valid)
                       
                    if ipoly.is_valid == False:
                        iipoly = cls.fixSimplePolygon(ipoly)
                        if iipoly:
                            interior_polys.append(iipoly)
                    else:
                        interior_polys.append(ipoly)
                
                interior_multipoly = shapely.geometry.MultiPolygon(interior_polys)
                if ginterior == True:
                    interior_multipoly = ShapelyUtils.orientMultiPolygon(interior_multipoly)
                    interior_offset = ShapelyUtils.offsetMultiPolygon(interior_multipoly, amount, 'right')
                    interior_multipoly = ShapelyUtils.buildMultiPolyFromOffset(interior_offset)
                
                # the diff is the solution
                try:
                    sol_poly = exterior_multipoly.difference(interior_multipoly)
                except Exception as e :
                    print("ERROR difference")
                    print(e)
                    raise

                if sol_poly.geom_type == 'Polygon':
                    offset = shapely.geometry.LineString(list(sol_poly.exterior.coords))
                elif sol_poly.geom_type == 'MultiPolygon':
                    offsets = []
                    for geom in sol_poly.geoms:
                        if geom.geom_type == 'Polygon':
                            offsets.append(shapely.geometry.LineString(geom.exterior))
                    offset = shapely.geometry.MultiLineString(offsets)

            else: # without interiors
                pass

       
            multi_offset.append(offset)

        return multi_offset

    @classmethod
    def offsetMultiPolygonAsMultiPolygon(cls, geometry: shapely.geometry.MultiPolygon, amount: float, side, ginterior=False, resolution=16, join_style=1, mitre_limit=5.0) -> shapely.geometry.MultiPolygon :
        '''
        Generate offseted lines from the polygons. All the produced lines are good 
        to store in the toolpaths.

        But for the next offset step, remove the degenerated lines from this set
        to construct a valid multipolygon that we can offset.
        '''
        polys = []

        for poly in geometry.geoms:

            linestring = cls.polyExteriorToLineString(poly)

            offset = linestring.parallel_offset(amount, side, resolution=resolution, join_style=join_style, mitre_limit=5.0)

            exterior_multipoly = cls.buildMultiPolyFromOffset([offset])
            print("exterior_multipoly VALID ? ", exterior_multipoly.is_valid)

            if not exterior_multipoly.is_valid:
                exterior_multipoly = cls.fixMultipoly(exterior_multipoly)

            if poly.interiors: # with interiors
                
                # with interiors
                interior_polys = []
                for interior in poly.interiors:
                    ipoly = shapely.geometry.Polygon(interior)
                    print("ipoly VALID ? ", ipoly.is_valid)
                       
                    if ipoly.is_valid == False:
                        iipoly = cls.fixSimplePolygon(ipoly)
                        if iipoly:
                            interior_polys.append(iipoly)
                    else:
                        interior_polys.append(ipoly)
                
                interior_multipoly = shapely.geometry.MultiPolygon(interior_polys)
                # this simplify may be important so that the offset becomes Ok (example: letter "B") 
                interior_multipoly = ShapelyUtils.simplifyMultiPoly(interior_multipoly, 0.001)
                if ginterior == True:
                    ShapelyUtils.MatplotlibDisplay("starting interior offset from", interior_multipoly)

                    interior_multipoly = ShapelyUtils.orientMultiPolygon(interior_multipoly)
                    ShapelyUtils.MatplotlibDisplay("starting interior offset from oriented", interior_multipoly)

                    interior_offset = ShapelyUtils.offsetMultiPolygon(interior_multipoly, amount, 'right')

                    for k, offset in enumerate(interior_offset):
                        ShapelyUtils.MatplotlibDisplay("interior offseting (linestring) %d" % k, offset)
                        
                    # the diff is the solution
                    interior_multipoly = ShapelyUtils.buildMultiPolyFromOffset(interior_offset)

                    ShapelyUtils.MatplotlibDisplay("resulting multipolygon of interior offset", interior_multipoly)

                try:
                    sol_poly = exterior_multipoly.difference(interior_multipoly)

                    ShapelyUtils.MatplotlibDisplay("diff of interior offseting", sol_poly)

                except Exception as e :
                    print("ERROR difference")
                    print(e)
                    raise

                if sol_poly.geom_type == 'Polygon':
                    polys.append(sol_poly)
                elif sol_poly.geom_type == 'MultiPolygon':
                    for geom in sol_poly.geoms:
                        if geom.geom_type == 'Polygon':
                            polys.append(geom)

            else: # without interiors
                for poly in exterior_multipoly.geoms:
                    if poly.geom_type == 'Polygon':
                        polys.append(poly)

        return shapely.geometry.MultiPolygon(polys)

    @classmethod
    def buildMultiPolyFromOffset(cls, multi_offset: any) -> shapely.geometry.MultiPolygon:
        '''
        offset is the direct result of an parallel_offset operation -> can be of various type

        We filter the degenerated lines
        '''
        polygons = []

        for offset in multi_offset:
            lines_ok = []
            if offset.geom_type == 'LineString':
                if len(list(offset.coords)) <=  2:
                    pass
                else:
                    lines_ok.append(offset)
            if offset.geom_type == 'MultiLineString':
                for geom in offset.geoms:
                    if geom.geom_type == 'LineString':
                        if len(list(geom.coords)) <=  2:
                            continue
                        lines_ok.append(geom)
                
            for line_ok in lines_ok:
                polygon = shapely.geometry.Polygon(line_ok)
                polygons.append(polygon)

        return shapely.geometry.MultiPolygon(polygons)

    @classmethod
    def polyExteriorToLineString(cls, poly: shapely.geometry.Polygon):
        '''
        '''
        print(" ------------------------  poly to linestring ---")

        linestring = shapely.geometry.LineString(poly.exterior)

        return linestring

    @classmethod
    def polyToLinearRing(cls, poly: shapely.geometry.Polygon):
        '''
        '''
        print(" ------------------------  poly to linestring ---")

        linearring = shapely.geometry.LinearRing(list(poly.exterior.coords))

        return linearring

    @classmethod
    def multiPolyToMultiLine(cls, multipoly: shapely.geometry.MultiPolygon) -> shapely.geometry.MultiLineString:
        '''
        '''
        lines = []

        for poly in multipoly.geoms:
            line = cls.polyExteriorToLineString(poly)
            lines.append(line)
        
        multiline = shapely.geometry.MultiLineString(lines)
        
        return multiline

    @classmethod
    def crosses(cls, bounds: shapely.geometry.MultiPolygon, p1: Tuple[int,int], p2: Tuple[int,int]):
        '''
        Does the line from p1 to p2 cross outside of bounds?
        '''
        if bounds == None:
            return True
        if p1[0] == p2[0] and p1[0] == p2[0]:
            return False

        # JSCUT clipper.AddPath([p1, p2], ClipperLib.PolyType.ptSubject, False)
        # JSCUT clipper.AddPaths(bounds, ClipperLib.PolyType.ptClip, True)

        p1_p2 = shapely.geometry.LineString([p1,p2])

       
        result = p1_p2.intersection(bounds)
    
        if result.is_empty is True:
            return False
            #child : ClipperLib.PolyNode = result.GetFirst() 
            #points = child.Contour
            #if len(points) == 2:
            #    if points[0].X == p1.X and points[1].X == p2.X and points[0].Y == p1.Y and points[1].Y == p2.Y :
            #        return False
            #    if points[0].X == p2.X and points[1].X == p1.X and points[0].Y == p2.Y and points[1].Y == p1.Y :
            #        return False

       
        if result.geom_type == 'Point':
            if result.x == p1[0] and result.y == p1[1] :
                return False
            if result.x == p2[0] and result.y == p2[1] :
                return False
            
            
        return True

    @classmethod
    def union_list_of_polygons(cls, poly_list: List[shapely.geometry.Polygon]) -> shapely.geometry.MultiPolygon :
        '''
        '''
        first = poly_list[0]

        geometry = first
        
        for poly in poly_list[1:]:
            geometry = geometry.union(poly)

        return geometry

    @classmethod
    def reorder_poly_points(cls, poly: shapely.geometry.Polygon) -> shapely.geometry.Polygon:
        '''
        Problem: shapely bug when outsiding a polygon where the stating point
        in a convex corner: at that point, the offset line 'outside' is uncorrect.

        Solution: start the list of points at a point in the middle of a segment
        (if there is one)  
        '''
        if not poly.geom_type == 'Polygon':
            return poly
            
        pts = list(poly.exterior.coords)

        # ----------------------------------------------------
        def is_inside_segment(pt, pt_left, pt_right):
            ab = (pt[0] - pt_left[0], pt[1], pt_left[1])
            ac = (pt[0] - pt_right[0], pt[1], pt_right[1])

            if (ab[0]*ab[0] + ab[1]*ab[1]) < 0.00001:
                return False
            if (ac[0]*ac[0] + ac[1]*ac[1]) < 0.00001:
                return False

            s1 = ab[0]
            s1 = ab[1]

            s2 = ac[0]
            s2 = ac[1]
            
            # a segment ?
            if math.fabs(s1*s2 - s2*s1) > 0.00001:
                return False

            # inside the segment ?
            x = pt[0]
            x1 = pt_left[0]
            x2 = pt_right[0]

            #y = pt[1]
            #y1 = pt_left[1]
            #y2 = pt_right[1]

            if math.fabs(x2-x1) < 0.00001:
                return False

            alpha = (x-x1)/(x2-x1)

            return alpha > 0
        # -----------------------------------------------------

        k_ok = None
        
        for k, pt in enumerate(pts):
            pt_prev = pts[k-1] 
            if k < len(pts) -1:
                pt_next = pts[k+1]
            else: 
                pt_next = pts[0]

            if is_inside_segment(pt, pt_prev, pt_next):
                k_ok = k
                break

        # k_ok is the right start!

        if k is not None:
            pts = pts[k_ok:] + pts[:k_ok]

            return shapely.geometry.Polygon(pts)

        return poly

    @classmethod
    def fixMultipoly(cls, multipoly: shapely.geometry.MultiPolygon) -> shapely.geometry.MultiPolygon :
        '''
        '''
        valid_polys = []

        for poly in multipoly.geoms:
            if not poly.is_valid:
                fixed_poly = cls.fixGenericPolygon(poly)
                if fixed_poly is not None:
                    valid_polys.append(fixed_poly)
            else:
                valid_polys.append(poly)

        if len(valid_polys) > 0:
            return shapely.geometry.MultiPolygon(valid_polys)

        return None

    @classmethod
    def fixSimplePolygon(cls, polygon: shapely.geometry.Polygon) -> shapely.geometry.Polygon :
        '''
        '''
        valid_poly = make_valid(polygon)

        if valid_poly.geom_type == 'Polygon':
            return valid_poly

        if valid_poly.geom_type == 'MultiPolygon':
            polys = []

            for geom in valid_poly.geoms:
                if not geom.is_valid:
                    continue

                polys.append(geom)

            # take the largest one!
            largest_area = -1
            largest_poly = None
            for poly in polys:
                area = poly.area
                if area > largest_area:
                    largest_area = area
                    largest_poly = poly

            return largest_poly

        return None

    @classmethod
    def fixGenericPolygon(cls, polygon: shapely.geometry.Polygon) -> shapely.geometry.Polygon :
        '''
        fix exterior and interiors in not valid
        '''
        if polygon.is_valid:
            return polygon

        exterior = list(polygon.exterior.coords)
        interiors = polygon.interiors

        ext_poly = shapely.geometry.Polygon(exterior)
        if not ext_poly.is_valid:
            ext_poly = cls.fixSimplePolygon(ext_poly)

        fixed_interiors = []
        for interior in interiors:
            int_poly = shapely.geometry.Polygon(list(interior.coords))

            if not int_poly.is_valid:
                int_poly = cls.fixSimplePolygon(int_poly)

            fixed_interiors.append(int_poly)

        ext_linestring = shapely.geometry.LineString(list(ext_poly.exterior.coords))
        holes_linestrings = [shapely.geometry.LineString(list(int_poly.exterior.coords)) for int_poly in fixed_interiors] 

        fixed_poly = shapely.geometry.Polygon(ext_linestring, holes=holes_linestrings)

        return fixed_poly

    @classmethod
    def fixSimplePolygon(cls, polygon: shapely.geometry.Polygon) -> shapely.geometry.Polygon :
        '''
        '''
        valid_poly = make_valid(polygon)

        if valid_poly.geom_type == 'Polygon':
            return valid_poly

        if valid_poly.geom_type == 'MultiPolygon':
            polys = []

            for geom in valid_poly.geoms:
                if not geom.is_valid:
                    continue

                polys.append(geom)

            # take the largest one!
            largest_area = -1
            largest_poly = None
            for poly in polys:
                area = poly.area
                if area > largest_area:
                    largest_area = area
                    largest_poly = poly

            return largest_poly

        if valid_poly.geom_type == 'GeometryCollection':
            # shit
            pass

        return None

    @classmethod
    def fixGenericPolygon(cls, polygon: shapely.geometry.Polygon) -> shapely.geometry.Polygon :
        '''
        fix exterior and interiors in not valid
        '''
        if polygon.is_valid:
            return polygon

        exterior = list(polygon.exterior.coords)
        interiors = polygon.interiors

        ext_poly = shapely.geometry.Polygon(exterior)
        if not ext_poly.is_valid:
            ext_poly = cls.fixSimplePolygon(ext_poly)

        if not interiors:
            ext_linestring = shapely.geometry.LineString(list(ext_poly.exterior.coords))

            fixed_poly = shapely.geometry.Polygon(ext_linestring)
            
        else:
            fixed_interiors = []
            for interior in interiors:
                int_poly = shapely.geometry.Polygon(list(interior.coords))

                if not int_poly.is_valid:
                    int_poly = cls.fixSimplePolygon(int_poly)

                fixed_interiors.append(int_poly)

            ext_linestring = shapely.geometry.LineString(list(ext_poly.exterior.coords))
            holes_linestrings = [shapely.geometry.LineString(list(int_poly.exterior.coords)) for int_poly in fixed_interiors] 

            fixed_poly = shapely.geometry.Polygon(ext_linestring, holes=holes_linestrings)

        return fixed_poly

    @classmethod
    def MatplotlibDisplay(cls, title, geom: any):
        '''
        '''
        if cls.MAPLOTLIB_DEBUG == False:
            return

        cls.cnt += 1

        # dispatch
        if geom.geom_type == 'LineString':
            cls._MatplotlibDisplayLineString(title, geom)
        if geom.geom_type == 'MultiLineString':
            cls._MatplotlibDisplayMultiLineString(title, geom)
        if geom.geom_type == 'Polygon':
            cls._MatplotlibDisplayPolygon(title, geom)
        if geom.geom_type == 'MultiMultiPolygon':
            cls._MatplotlibDisplayMultiPolygon(title, geom)
        else:
            pass

    @classmethod
    def _MatplotlibDisplayLineString(cls, title, linestring):
        '''
        ''' 
        plt.figure(cls.cnt)
        plt.title(title)

        x = linestring.coords.xy[0]
        y = linestring.coords.xy[1]

        # plot
        style = {
            0: 'bo-',
        }

        plt.plot(x,y, style[0])
        plt.show()

    @classmethod
    def _MatplotlibDisplayMultiLineString(cls, title, multilinestring):
        '''
        '''    
        plt.figure(cls.cnt)
        plt.title(title)

        style = {
            0: 'bo-',
            1: 'r+--'
        }
        
        xx = []
        yy = []

        for line in multilinestring.geoms:
            ix = line.coords.xy[0]
            iy = line.coords.xy[1]

            xx.append(ix)
            yy.append(iy)

        for k, (x,y) in enumerate(zip(xx,yy)):
            plt.plot(x, y, style[k%2])

        plt.show()

    @classmethod
    def _MatplotlibDisplayPolygon(cls, title, polygon):
        '''
        '''
        plt.figure(cls.cnt)
        plt.title(title)

        style_ext = {
            0: 'bo-'
        }
        style_int = {
            0: 'r+--',
            1: 'go-'
        }
        
        x = polygon.exterior.coords.xy[0]
        y = polygon.exterior.coords.xy[1]

        plt.plot(x, y, style_ext)

        interiors_xx = []
        interiors_yy = []

        for interior in polygon.interiors:
            ix = interior.coords.xy[0]
            iy = interior.coords.xy[1]

            interiors_xx.append(ix)
            interiors_yy.append(iy)

        for k, (ix,iy) in enumerate(zip(interiors_xx,interiors_yy)):
            plt.plot(ix, iy, style_int[k%2])

        plt.show()

    @classmethod
    def _MatplotlibDisplayMultiPolygon(cls, title, multipoly):
        '''
        '''
        plt.figure(cls.cnt)
        plt.title(title)

        xx_ext = []
        yy_ext = []

        xx_int = []
        yy_int = []

        for geom in multipoly.geoms:
            x = geom.exterior.coords.xy[0]
            y = geom.exterior.coords.xy[1]

            xx_ext.append(x)
            yy_ext.append(y)

            for interior in geom.interiors:
                ix = interior.coords.xy[0]
                iy = interior.coords.xy[1]

                xx_int.append(ix)
                yy_int.append(iy)
        
        # plot
        for x,y in zip(xx_ext,yy_ext):
            plt.plot(x,y, 'bo-')
        for x,y in zip(xx_int,yy_int):
            plt.plot(x,y, 'r+--')

        plt.show()

