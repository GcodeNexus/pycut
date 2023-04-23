
import os
import sys
import io

import unittest
from misc_private.svgelements_svgpathtools.discretisation import SvgPath_SvgPathTools, SvgPath_SvgElements
import xmlrunner

import matplotlib.pyplot as plt

svg_rect = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_rectangle" width="100mm" height="100mm" viewBox="0 0 100 100"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
     <rect id="rect" style="fill:#0000ff" width="50" height="70" x="10" y="10" rx="5" ry="10" />
  </g>
</svg>"""
    
svg_circle = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_circle" width="100mm" height="100mm"  viewBox="0 0 100 100"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <circle id="circle" style="fill:#007c00" cx="30" cy="30" r="5" />
  </g>
</svg>"""
    
svg_ellispe = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_ellipse" width="100mm" height="100mm"  viewBox="0 0 100 100"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <ellipse id="ellipse" cx="100" cy="50" rx="100" ry="50" />
  </g>
</svg>"""
    
svg_line = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_line" width="100mm" height="100mm"  viewBox="0 0 100 100"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <line id="line" x1="10" y1="10" x2="80" y2="60" stroke="black"/>
  </g>
</svg>"""
    
svg_polyline = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_polyline" width="300mm" height="300mm"  viewBox="0 0 300 300"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <polyline id="polyline" points="100,100 150,25 150,75 200,0" fill="none" stroke="black" />
  </g>
</svg>"""
    
svg_polygon1 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_polygon" width="300mm" height="300mm"  viewBox="0 0 300 300"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <polygon id="polygon1" points="100,100 200,100 150,150 100,100" fill="none" stroke="black" />
  </g>
</svg>"""
    
svg_polygon2 = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" id="test_polygon" width="300mm" height="300mm"  viewBox="0 0 300 300"
   xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg">
  <g id="layer">
    <polygon id="polygon2" points="100,100 200,100 150,150" fill="none" stroke="black" />
  </g>
</svg>"""



def plot(pts, title):
    plt.figure()
    plt.title(title)
        
    xx = [ pt.real for pt in pts ]
    yy = [pt.imag for pt in pts ]

    plt.plot(xx, yy, 'ro-')
      
    plt.axis('equal')
    plt.show()


class SvgPathToolsTests(unittest.TestCase):
    """
    """
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
       
    def test_discretise_rectangle(self):
        """
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_rect))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "?")
        self.assertTrue(path.p_id == "rect")
        self.assertTrue(path.path_closed == True)
        self.assertTrue(len(path.svg_path) == 8)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path[2].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[3].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path[4].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[5].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path[6].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[7].__class__.__name__ == "Arc")

        self.assertTrue(path.path_closed == True)

        pts = path.discretize_closed_path()

        self.assertTrue(len(pts) == 489)

    def test_discretise_circle(self):
        """
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_circle))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.path_closed == True)

        # svgpathtools makes of if 2 arcs
        self.assertTrue(len(path.svg_path) == 2)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Arc")

        pts = path.discretize_closed_path()

        plot(pts, "circle SvgPathTools")

        self.assertTrue(len(pts) == 315)

    def test_discretise_ellipse(self):
        """
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_ellispe))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path) == 2)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Arc")

        pts = path.discretize_closed_path()

        self.assertTrue(len(pts) == 4845)

    def test_discretise_line(self):
        """
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_line))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.p_id == "line")
        self.assertTrue(path.path_closed == False)

        self.assertTrue(len(path.svg_path) == 1)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Line")

        pts = path.discretize_open_path()

        self.assertTrue(len(pts) == 2)

    def test_discretise_polyline(self):
        """
        """        
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_polyline))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.path_closed == False)

        self.assertTrue(len(path.svg_path) == 3)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[2].__class__.__name__ == "Line")

        pts = path.discretize_open_path()

        self.assertTrue(len(pts) == 4)

    def test_discretise_polygon1(self):
        """
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_polygon1))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.p_id == "polygon1")
        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path) == 4) # svpathtools: this is **bad**
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[2].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[3].__class__.__name__ == "Line")

        pts = path.discretize_closed_path()
        '''
        expecting 4 points (not 3) because of the shapely fix
        '''
        self.assertTrue(len(pts) == 4)

    def test_discretise_polygon2(self):
        """
        no end point == start point
        """
        paths = SvgPath_SvgPathTools.read_paths_from_file(io.StringIO(svg_polygon2))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.p_id == "polygon2")
        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path) == 3)
        self.assertTrue(path.svg_path[0].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path[2].__class__.__name__ == "Line")

        pts = path.discretize_closed_path()
        '''
        expecting 4 points (not 3) because of the shapely fix
        '''
        self.assertTrue(len(pts) == 4)  
        

class SvgElementsTests(unittest.TestCase):
    """
    """
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
       
    def test_discretise_rectangle(self):
        """
        """
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_rect))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "rect")
        self.assertTrue(path.p_id == "rect")
        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path.segments()) == 10)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[4].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[5].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[6].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[7].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[8].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[9].__class__.__name__ == "Close")

        pts = path.discretize_closed_path()

        self.assertTrue(len(pts) == 489)

    def test_discretise_circle(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_circle))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "circle")
        self.assertTrue(path.p_id == "circle")
        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path.segments()) == 6)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[4].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[5].__class__.__name__ == "Close")

        pts = path.discretize_closed_path()

        plot(pts, "circle SvgElements")

        self.assertTrue(len(pts) == 313)

    def test_discretise_ellipse(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_ellispe))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "ellipse")
        self.assertTrue(path.p_id == "ellipse")
        self.assertTrue(path.path_closed == True)

        self.assertTrue(len(path.svg_path.segments()) == 6)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[4].__class__.__name__ == "Arc")
        self.assertTrue(path.svg_path.segments()[5].__class__.__name__ == "Close")

        pts = path.discretize_closed_path()

        self.assertTrue(len(pts) == 4845)

    def test_discretise_line(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_line))

        self.assertTrue(len(paths) == 1)
        
        path = paths[0]
        
        self.assertTrue(path.tag == "line")
        self.assertTrue(path.p_id == "line")
        self.assertTrue(path.path_closed == False)

        self.assertTrue(len(path.svg_path.segments()) == 2)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Line")

        pts = path.discretize_open_path()

        self.assertTrue(len(pts) == 2)

    def test_discretise_polyline(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_polyline))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "polyline")
        self.assertTrue(path.p_id == "polyline")
        self.assertTrue(path.path_closed == False)

        self.assertTrue(len(path.svg_path.segments()) == 4)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Line")

        pts = path.discretize_open_path()

        self.assertTrue(len(pts) == 4)

    def test_discretise_polygon1(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_polygon1))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "polygon")
        self.assertTrue(path.p_id == "polygon1")
        self.assertTrue(path.path_closed == True)
        
        self.assertTrue(len(path.svg_path.segments()) == 5)
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[4].__class__.__name__ == "Close")

        pts = path.discretize_closed_path()
        '''
        expecting 4 points (not 3) because of the shapely fix
        '''
        self.assertTrue(len(pts) == 4)

    def test_discretise_polygon2(self):
        """
        """        
        paths = SvgPath_SvgElements.read_paths_from_file(io.StringIO(svg_polygon2))

        self.assertTrue(len(paths) == 1)

        path = paths[0]

        self.assertTrue(path.tag == "polygon")
        self.assertTrue(path.p_id == "polygon2")
        self.assertTrue(path.path_closed == True)
        
        self.assertTrue(len(path.svg_path.segments()) == 4)
        # yes , only 2 lines, hopefully the discretisation is ok...
        self.assertTrue(path.svg_path.segments()[0].__class__.__name__ == "Move")
        self.assertTrue(path.svg_path.segments()[1].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[2].__class__.__name__ == "Line")
        self.assertTrue(path.svg_path.segments()[3].__class__.__name__ == "Close")

        pts = path.discretize_closed_path()
        '''
        expecting 4 points (not 3) because of the shapely fix
        '''
        self.assertTrue(len(pts) == 4)


def get_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SvgPathToolsTests))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(SvgElementsTests))
    
    return suite


if __name__ == '__main__':
    if os.environ.get('PYCUT_XMLRUNNER_UNITTESTS', None) == "YES":
        unittest.main(testRunner=xmlrunner.XMLTestRunner(path='RESULTS', indic="test_svgpath_discretise"))
    else:
        unittest.main()


#unittest.TextTestRunner(verbosity=2).run(suite)
#xmlrunner.XMLTestRunner(path='RESULTS', indic="test_svgpath_discretise").run(get_suite()[0])
