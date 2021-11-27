
from typing import List
import math

from svgpathutils import SvgPath
from svgviewer import SvgViewer

import clipper.clipper as ClipperLib

class SvgOp:
    '''
    '''
    inchToClipperScale = 100000  # Scale inch to Clipper
    cleanPolyDist = inchToClipperScale / 100000
    arcTolerance = inchToClipperScale / 40000

    pxPerInch = 96

    def __init__(self, operation):
        self.operation = operation
        
        # the input
        self.svg_paths : List[SvgPath] = [] # to fill at "setup"
        # the input "transformed"
        self.clipper_paths : List[List[ClipperLib.IntPoint]] = []
        
        # the resulting paths from the op combinaison setting
        self.combined_clipper_paths = ClipperLib.PathVector()
        # and the resulting svg paths from the combinaison, to be displayed
        # in the svg viewer
        self.combined_svg_paths : List[SvgPath] = []

    def setup(self, svg_viewer: SvgViewer):
        '''
        '''
        for svg_path_id in self.operation["paths"]:

            svg_path_d = svg_viewer.get_path_d(svg_path_id)
            svg_path = SvgPath(svg_path_id, {'d': svg_path_d})

            self.svg_paths.append(svg_path)

    def calculate(self):
        '''
        '''
        self.calculate_op_region()
        self.calculate_gcode()
           
    def calculate_op_region(self):
        '''
        '''
        for svg_path in self.svg_paths:
            clipper_path = svg_path.toClipperPath()
            self.clipper_paths.append(clipper_path)

        self.combine_clipper_paths()

        for clipper_path in self.combined_clipper_paths:
            svg_path = SvgPath.fromClipperPath(clipper_path)
            self.combined_svg_paths.append(svg_path)

    def combine_clipper_paths(self):
        '''
        '''
        subj = ClipperLib.PathVector()
        subj.append(self.clipper_paths[0])

        clip = ClipperLib.PathVector()
        for path in self.clipper_paths[1:]:
            clip.append(path)

        c = ClipperLib.Clipper()

        c.AddPaths(subj, ClipperLib.PolyType.ptSubject, True)
        c.AddPaths(clip, ClipperLib.PolyType.ptClip, True)
    
        clipType :ClipperLib.ClipType  = {
            "Union": ClipperLib.ClipType.ctUnion,
            "Intersection": ClipperLib.ClipType.ctIntersection,
            "XOR": ClipperLib.ClipType.ctXor,
            "Difference": ClipperLib.ClipType.ctDifference,
        } [self.operation["Combine"]]    

        c.Execute(clipType, 
                self.combined_clipper_paths,
                ClipperLib.PolyFillType.pftNonZero, 
                ClipperLib.PolyFillType.pftNonZero)


    def calculate_gcode(self):
        '''
        '''
        pass
