
from io import StringIO
import os
import math

from typing import List
from typing import Tuple
from typing import Dict
from typing import Any

import tempfile

import xml.etree.ElementTree as etree

import svgpathtools
import numpy as np

import shapely.geometry

#from clipper_613 import clipper_613 as ClipperLib
from clipper_642 import clipper_642 as ClipperLib

from clipper_utils import ClipperUtils

M_PI = math.acos(-1)


class SvgPath:
    '''
    Transform svgpathtools 'Path' to 'ClipperLib' path

    - svgpathtools 'Path' are list of 'Segment(s)' and
    each segment has a list of points, given in format 'complex type' (a+bj)

    - ClipperLib 'Path' are list of IntPoint (X,Y)

    so the transformation is straightforward

    Convention:
    - a svg <path> definition is noted: svg_path_d
    - a path from svgpathtools is noted: svg_path
    - the discretization of a svg_path results in a numpy array, noted: np_svg_path
    - a clipper path is noted: clipper_path  (a 'ClipperLib.IntPointVector')
    '''
    PYCUT_SAMPLE_LEN_COEFF = 100 # is in jsCut 1.0/0.01 ie the same
    PYCUT_SAMPLE_MIN_NB_SEGMENTS = 5 # is in jsCut 1

    @classmethod
    def set_arc_precision(cls, arc_min_segments_length):
        '''
        '''
        cls.PYCUT_SAMPLE_LEN_COEFF = 1.0 / arc_min_segments_length

    @classmethod
    def set_arc_min_nb_segments(cls, arc_min_nb_segments):
        '''
        '''
        cls.PYCUT_SAMPLE_MIN_NB_SEGMENTS = arc_min_nb_segments

    @classmethod
    def read_svg_shapes_as_paths(cls, svg: str) -> Dict[str,Tuple[Dict[str,str],svgpathtools.Path]] :
        '''
        '''
        svg_shapes = {}

        # a tmp file
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, 'temp_svg.svg')
            
            fp = open(filename, "w")
            fp.write(svg)
            fp.close()

            paths, attributes = svgpathtools.svg2paths(filename)

            for k, path in enumerate(paths):
                attribs = attributes[k]

                path_id = attribs.get('id', None)
                print("============= path %s =================" % path_id)
                #print(path)
                #print(attribs)

                if path_id is None:
                    continue

                svg_shapes[path_id] = (attribs, path)

        return svg_shapes

    def __init__(self, p_id: str, p_attrs: Dict):
        '''
        '''
        # the 'id' of a svg <path> definition
        self.p_id = p_id
        # and the attributes of the <path>
        self.p_attrs = p_attrs

        # the transformation of the svg_path_d to a svgpathtools 'path'
        self.svg_path = svgpathtools.parse_path(self.p_attrs['d'])

    def discretize(self) -> np.array :
        '''
        Transform the svg_path (a list of svgpathtools Segments) into a list of 'complex' points
        - Line: only 2 points
        - Arc: discretize per hand
        - QuadraticBezier, CubicBezier: discretize per hand

        TODO: Take care not to add twice the same points
        - Arc
        - Beziers
        '''
        points = np.array([], dtype=np.complex128)
        
        for k, segment in enumerate(self.svg_path):
            if segment.__class__.__name__ == 'Line':
                # start and end
                if len(self.svg_path) == 1:
                    pts = segment.points([0,1])
                else:
                    if k < len(self.svg_path)-1:
                        pts = segment.points([0])
                    else:
                        pts = segment.points([0, 1])
            elif segment.__class__.__name__ == 'Arc':
                # no 'points' method for 'Arc'!
                seg_length = segment.length()

                nb_samples = int(seg_length * self.PYCUT_SAMPLE_LEN_COEFF)
                nb_samples = max(nb_samples, self.PYCUT_SAMPLE_MIN_NB_SEGMENTS)
                
                _pts = []
                for k in range(nb_samples+1):
                    _pts.append(segment.point(float(k)/float(nb_samples)))

                pts = np.array(_pts, dtype=np.complex128)

            else:  # 'QuadraticBezier', 'CubicBezier'
                seg_length = segment.length()

                nb_samples = int(seg_length * self.PYCUT_SAMPLE_LEN_COEFF)
                nb_samples = max(nb_samples, self.PYCUT_SAMPLE_MIN_NB_SEGMENTS)
                
                incr = 1.0 / nb_samples

                samples = [x* incr for x in range(0, nb_samples+1)]
                pts = segment.points(samples)

            points = np.concatenate((points, pts))

        return points

    def toClipperPath(self) -> ClipperLib.IntPointVector:
        '''
        '''
        np_svg_path = self.discretize()

        clipper_path = ClipperLib.IntPointVector()

        for complex_pt in np_svg_path:
            pt = ClipperLib.IntPoint( \
                int(complex_pt.real * (ClipperUtils.inchToClipperScale / 25.4)),
                int(complex_pt.imag * (ClipperUtils.inchToClipperScale / 25.4)))
            clipper_path.append(pt)

        return clipper_path

    @classmethod
    def fromCircleDef(cls, center, radius) -> 'SvgPath':
        '''
        '''
        NB_SEGMENTS = 12
        angles = [ float(k * M_PI )/ (NB_SEGMENTS) for k in range(NB_SEGMENTS*2 +1)]

        discretized_svg_path : List[complex] = [ complex( \
                    center[0] + radius*math.cos(angle), 
                    center[1] + radius*math.sin(angle) ) for angle in angles]

        svg_path = svgpathtools.Path()

        for i in range(len(discretized_svg_path)-1):
            start = discretized_svg_path[i]
            end   = discretized_svg_path[i+1]

            svg_path.append(svgpathtools.Line(start, end))

        return SvgPath("pycut_tab", {'d': svg_path.d()})

    @classmethod
    def fromClipperPath(cls, prefix: str, clipper_path: ClipperLib.IntPointVector) -> 'SvgPath':
        '''
        '''
        discretized_svg_path : List[complex] = [ complex( \
                    pt.X / (ClipperUtils.inchToClipperScale / 25.4), 
                    pt.Y / (ClipperUtils.inchToClipperScale / 25.4)) for pt in clipper_path]


        svg_path = svgpathtools.Path()

        for i in range(len(discretized_svg_path)-1):
            start = discretized_svg_path[i]
            end   = discretized_svg_path[i+1]

            svg_path.append(svgpathtools.Line(start, end))

        # last one : from end point to start point
        start = discretized_svg_path[-1]
        end   = discretized_svg_path[0]

        svg_path.append(svgpathtools.Line(start, end))

        return SvgPath(prefix, {'d': svg_path.d(), 'fill-rule': 'nonzero'})

    @classmethod
    def fromClipperPaths(cls, prefix: str, clipper_paths: ClipperLib.PathVector) -> 'SvgPath':
        '''
        Note:
            only 1 path "def" consisting of 2 or more lines : 
            for the path interior be filled in color -> fill-rule is 'evenodd'
        '''
        discretized_svg_paths = []
        for clipper_path in clipper_paths:
            discretized_svg_path : List[complex] = [ complex( \
                    pt.X / (ClipperUtils.inchToClipperScale / 25.4), 
                    pt.Y / (ClipperUtils.inchToClipperScale / 25.4)) for pt in clipper_path]
            
            discretized_svg_paths.append(discretized_svg_path)

        svg_path = svgpathtools.Path()

        for discretized_svg_path in discretized_svg_paths:
            for i in range(len(discretized_svg_path)-1):
                start = discretized_svg_path[i]
                end   = discretized_svg_path[i+1]

                svg_path.append(svgpathtools.Line(start, end))

        return SvgPath(prefix, {'d': svg_path.d(), 'fill-rule': 'evenodd'})

    def toShapelyPolygon(self) -> shapely.geometry.Polygon:
        '''
        '''
        path = self.toClipperPath()

        pts = [ (pt.X, pt.Y) for pt in path ]
    
        return shapely.geometry.Polygon(pts)




class SvgTransformer:
    '''
    '''
    def __init__(self, svg):
        self.svg = svg

    def collect_shapes(self) -> List[etree.ElementTree]:
        '''
        '''
        # python xml module can load with svg xml header with encoding utf-8
        tree = etree.fromstring(self.svg)
        elements = tree.findall('.//*')

        shapes_types = [
        	"path",
            "rect",
            "circle",
            "ellipse",
            "polygon",
            "line",
            "polyline"
        ]

        shapes : List[etree.ElementTree] = []
        
        for element in elements:
            tag = element.tag.split("{http://www.w3.org/2000/svg}")[1]
            
            if tag in shapes_types:
                shapes.append(element)

        # lxml - exception with svg xml header with encoding utf-8
        #
        #tree = etree.parse(StringIO(self.svg))
        #shapes = tree.xpath('//*[local-name()="path" or local-name()="circle" or local-name()="rect" or local-name()="ellipse" or local-name()="polygon" or local-name()="line" or local-name()="polyline"]')

        return shapes
        
    def augment(self, svg_paths: List[SvgPath]) -> str:
        '''
        '''
        all_paths = ""

        shapes = self.collect_shapes()

        for shape in shapes:
            shape_id = shape.attrib.get('id', None)

            print("svg : found shape %s : %s" % (shape.tag, shape_id))

            if shape_id is None:
                print("      -> ignoring")
                continue

            tag = shape.tag.split("}")[1]
            svg_attrs = ''
            for key, value in shape.attrib.items():
                svg_attrs += ' %s="%s"' % (key, value)

            all_paths += '<%s %s/>\r\n' % (tag, svg_attrs)

        for k, svg_path in enumerate(svg_paths):
            p_id = svg_path.p_id
            d_def = svg_path.p_attrs['d']

            stroke = '#00ff00'
            stroke_width = '0'
            
            fill = svg_path.p_attrs.get("fill", "#111111")
            fill_opacity = svg_path.p_attrs.get("fill-opacity", "1.0")
            fill_rule = svg_path.p_attrs.get("fill-rule", "nonzero")

            path = '<path id="%(id)s_%(counter)d" style="stroke:%(stroke)s;stroke-width:%(stroke_width)s;fill:%(fill)s;fill-opacity:%(fill_opacity)s;fill-rule:%(fill_rule)s;" \
              d="%(d_def)s" />' % {
                'id': p_id, 
                'counter': k, 
                'fill': fill,
                'stroke_width': stroke_width,
                'stroke': stroke,
                'fill_opacity': fill_opacity, 
                'fill_rule': fill_rule, 
                'd_def': d_def
            }

            all_paths += path + '\r\n'
        
        root = etree.fromstring(self.svg)
        root_attrib = root.attrib
        
        svg = '''<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
                width="%s"
                height="%s"
                viewBox="%s"
                version="1.1">
                <g>
                  %s
                </g> 
             </svg>''' % (root_attrib["width"], root_attrib["height"], root_attrib["viewBox"], all_paths)

        #print(svg)
        
        return svg

    def augment_with_toolpaths(self, svg_paths: List[SvgPath]) -> str:
        '''
        TODO: eval the best stroke-width in function of the item size

        40x40 mm -> stroke-width = 0.2 ok
        1x1 mm   -> stroke-width = 0.01 ok
        '''
        all_paths = ""

        shapes = self.collect_shapes()

        for shape in shapes:
            shape_id = shape.attrib.get('id', None)

            print("svg : found shape %s : %s" % (shape.tag, shape_id))

            if shape_id is None:
                print("     -> ignoring")

            tag = shape.tag.split("}")[1]
            svg_attrs = ''
            for key, value in shape.attrib.items():
                svg_attrs += ' %s="%s"' % (key, value)

            all_paths += '<%s %s/>\r\n' % (tag, svg_attrs)

        for k, svg_path in enumerate(svg_paths):
            p_id = svg_path.p_id
            d_def = svg_path.p_attrs['d']

            stroke = '#00ff00'
            stroke_width = '0.2'
            
            fill = 'none'

            all_paths += '<path id="%(id)s_%(counter)d" style="stroke:%(stroke)s;stroke-width:%(stroke_width)s;fill:%(fill)s" d="%(d_def)s" />' % {
                'id': p_id, 
                'counter': k,
                'stroke_width': stroke_width,
                'stroke': stroke,
                'fill': fill,
                'd_def': d_def
            }
        
        root = etree.fromstring(self.svg)
        root_attrib = root.attrib

        svg = '''<svg xmlns:svg="http://www.w3.org/2000/svg" xmlns="http://www.w3.org/2000/svg"
                width="%s"
                height="%s"
                viewBox="%s"
                version="1.1">
                <g>
                 %s
                </g> 
             </svg>''' % (root_attrib["width"], root_attrib["height"], root_attrib["viewBox"], all_paths)

        #print(svg)
        
        return svg




    

