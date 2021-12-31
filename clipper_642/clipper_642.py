# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.2
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _clipper_642
else:
    import _clipper_642

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):
    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)
    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""
    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())
    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


class SwigPyIterator(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")

    def __init__(self, *args, **kwargs):
        raise AttributeError("No constructor defined - class is abstract")
    __repr__ = _swig_repr
    __swig_destroy__ = _clipper_642.delete_SwigPyIterator

    def value(self):
        return _clipper_642.SwigPyIterator_value(self)

    def incr(self, n=1):
        return _clipper_642.SwigPyIterator_incr(self, n)

    def decr(self, n=1):
        return _clipper_642.SwigPyIterator_decr(self, n)

    def distance(self, x):
        return _clipper_642.SwigPyIterator_distance(self, x)

    def equal(self, x):
        return _clipper_642.SwigPyIterator_equal(self, x)

    def copy(self):
        return _clipper_642.SwigPyIterator_copy(self)

    def next(self):
        return _clipper_642.SwigPyIterator_next(self)

    def __next__(self):
        return _clipper_642.SwigPyIterator___next__(self)

    def previous(self):
        return _clipper_642.SwigPyIterator_previous(self)

    def advance(self, n):
        return _clipper_642.SwigPyIterator_advance(self, n)

    def __eq__(self, x):
        return _clipper_642.SwigPyIterator___eq__(self, x)

    def __ne__(self, x):
        return _clipper_642.SwigPyIterator___ne__(self, x)

    def __iadd__(self, n):
        return _clipper_642.SwigPyIterator___iadd__(self, n)

    def __isub__(self, n):
        return _clipper_642.SwigPyIterator___isub__(self, n)

    def __add__(self, n):
        return _clipper_642.SwigPyIterator___add__(self, n)

    def __sub__(self, *args):
        return _clipper_642.SwigPyIterator___sub__(self, *args)
    def __iter__(self):
        return self

# Register SwigPyIterator in _clipper_642:
_clipper_642.SwigPyIterator_swigregister(SwigPyIterator)

CLIPPER_VERSION = _clipper_642.CLIPPER_VERSION
ctIntersection = _clipper_642.ctIntersection
ctUnion = _clipper_642.ctUnion
ctDifference = _clipper_642.ctDifference
ctXor = _clipper_642.ctXor
ptSubject = _clipper_642.ptSubject
ptClip = _clipper_642.ptClip
pftEvenOdd = _clipper_642.pftEvenOdd
pftNonZero = _clipper_642.pftNonZero
pftPositive = _clipper_642.pftPositive
pftNegative = _clipper_642.pftNegative
class IntPoint(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr
    X = property(_clipper_642.IntPoint_X_get, _clipper_642.IntPoint_X_set)
    Y = property(_clipper_642.IntPoint_Y_get, _clipper_642.IntPoint_Y_set)

    def __init__(self, x=0, y=0):
        _clipper_642.IntPoint_swiginit(self, _clipper_642.new_IntPoint(x, y))
    __swig_destroy__ = _clipper_642.delete_IntPoint

# Register IntPoint in _clipper_642:
_clipper_642.IntPoint_swigregister(IntPoint)
cvar = _clipper_642.cvar
loRange = cvar.loRange
hiRange = cvar.hiRange


def __lshift__(*args):
    return _clipper_642.__lshift__(*args)
class DoublePoint(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr
    X = property(_clipper_642.DoublePoint_X_get, _clipper_642.DoublePoint_X_set)
    Y = property(_clipper_642.DoublePoint_Y_get, _clipper_642.DoublePoint_Y_set)

    def __init__(self, *args):
        _clipper_642.DoublePoint_swiginit(self, _clipper_642.new_DoublePoint(*args))
    __swig_destroy__ = _clipper_642.delete_DoublePoint

# Register DoublePoint in _clipper_642:
_clipper_642.DoublePoint_swigregister(DoublePoint)

ioReverseSolution = _clipper_642.ioReverseSolution
ioStrictlySimple = _clipper_642.ioStrictlySimple
ioPreserveCollinear = _clipper_642.ioPreserveCollinear
jtSquare = _clipper_642.jtSquare
jtRound = _clipper_642.jtRound
jtMiter = _clipper_642.jtMiter
etClosedPolygon = _clipper_642.etClosedPolygon
etClosedLine = _clipper_642.etClosedLine
etOpenButt = _clipper_642.etOpenButt
etOpenSquare = _clipper_642.etOpenSquare
etOpenRound = _clipper_642.etOpenRound
class PolyNode(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self):
        _clipper_642.PolyNode_swiginit(self, _clipper_642.new_PolyNode())
    __swig_destroy__ = _clipper_642.delete_PolyNode
    Contour = property(_clipper_642.PolyNode_Contour_get, _clipper_642.PolyNode_Contour_set)
    Childs = property(_clipper_642.PolyNode_Childs_get, _clipper_642.PolyNode_Childs_set)
    Parent = property(_clipper_642.PolyNode_Parent_get, _clipper_642.PolyNode_Parent_set)

    def GetNext(self):
        return _clipper_642.PolyNode_GetNext(self)

    def IsHole(self):
        return _clipper_642.PolyNode_IsHole(self)

    def IsOpen(self):
        return _clipper_642.PolyNode_IsOpen(self)

    def ChildCount(self):
        return _clipper_642.PolyNode_ChildCount(self)

# Register PolyNode in _clipper_642:
_clipper_642.PolyNode_swigregister(PolyNode)

class PolyTree(PolyNode):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr
    __swig_destroy__ = _clipper_642.delete_PolyTree

    def GetFirst(self):
        return _clipper_642.PolyTree_GetFirst(self)

    def Clear(self):
        return _clipper_642.PolyTree_Clear(self)

    def Total(self):
        return _clipper_642.PolyTree_Total(self)

    def __init__(self):
        _clipper_642.PolyTree_swiginit(self, _clipper_642.new_PolyTree())

# Register PolyTree in _clipper_642:
_clipper_642.PolyTree_swigregister(PolyTree)


def Orientation(poly):
    return _clipper_642.Orientation(poly)

def Area(poly):
    return _clipper_642.Area(poly)

def PointInPolygon(pt, path):
    return _clipper_642.PointInPolygon(pt, path)

def SimplifyPolygon(*args):
    return _clipper_642.SimplifyPolygon(*args)

def SimplifyPolygons(*args):
    return _clipper_642.SimplifyPolygons(*args)

def CleanPolygon(*args):
    return _clipper_642.CleanPolygon(*args)

def CleanPolygons(*args):
    return _clipper_642.CleanPolygons(*args)

def MinkowskiSum(*args):
    return _clipper_642.MinkowskiSum(*args)

def MinkowskiDiff(poly1, poly2, solution):
    return _clipper_642.MinkowskiDiff(poly1, poly2, solution)

def PolyTreeToPaths(polytree, paths):
    return _clipper_642.PolyTreeToPaths(polytree, paths)

def ClosedPathsFromPolyTree(polytree, paths):
    return _clipper_642.ClosedPathsFromPolyTree(polytree, paths)

def OpenPathsFromPolyTree(polytree, paths):
    return _clipper_642.OpenPathsFromPolyTree(polytree, paths)

def ReversePath(p):
    return _clipper_642.ReversePath(p)

def ReversePaths(p):
    return _clipper_642.ReversePaths(p)
class IntRect(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr
    left = property(_clipper_642.IntRect_left_get, _clipper_642.IntRect_left_set)
    top = property(_clipper_642.IntRect_top_get, _clipper_642.IntRect_top_set)
    right = property(_clipper_642.IntRect_right_get, _clipper_642.IntRect_right_set)
    bottom = property(_clipper_642.IntRect_bottom_get, _clipper_642.IntRect_bottom_set)

    def __init__(self):
        _clipper_642.IntRect_swiginit(self, _clipper_642.new_IntRect())
    __swig_destroy__ = _clipper_642.delete_IntRect

# Register IntRect in _clipper_642:
_clipper_642.IntRect_swigregister(IntRect)

esLeft = _clipper_642.esLeft
esRight = _clipper_642.esRight
class ClipperBase(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self):
        _clipper_642.ClipperBase_swiginit(self, _clipper_642.new_ClipperBase())
    __swig_destroy__ = _clipper_642.delete_ClipperBase

    def AddPath(self, pg, PolyTyp, Closed):
        return _clipper_642.ClipperBase_AddPath(self, pg, PolyTyp, Closed)

    def AddPaths(self, ppg, PolyTyp, Closed):
        return _clipper_642.ClipperBase_AddPaths(self, ppg, PolyTyp, Closed)

    def Clear(self):
        return _clipper_642.ClipperBase_Clear(self)

    def GetBounds(self):
        return _clipper_642.ClipperBase_GetBounds(self)

    def PreserveCollinear(self, *args):
        return _clipper_642.ClipperBase_PreserveCollinear(self, *args)

# Register ClipperBase in _clipper_642:
_clipper_642.ClipperBase_swigregister(ClipperBase)

class Clipper(ClipperBase):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, initOptions=0):
        _clipper_642.Clipper_swiginit(self, _clipper_642.new_Clipper(initOptions))

    def Execute(self, *args):
        return _clipper_642.Clipper_Execute(self, *args)

    def ReverseSolution(self, *args):
        return _clipper_642.Clipper_ReverseSolution(self, *args)

    def StrictlySimple(self, *args):
        return _clipper_642.Clipper_StrictlySimple(self, *args)
    __swig_destroy__ = _clipper_642.delete_Clipper

# Register Clipper in _clipper_642:
_clipper_642.Clipper_swigregister(Clipper)

class ClipperOffset(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, miterLimit=2.0, roundPrecision=0.25):
        _clipper_642.ClipperOffset_swiginit(self, _clipper_642.new_ClipperOffset(miterLimit, roundPrecision))
    __swig_destroy__ = _clipper_642.delete_ClipperOffset

    def AddPath(self, path, joinType, endType):
        return _clipper_642.ClipperOffset_AddPath(self, path, joinType, endType)

    def AddPaths(self, paths, joinType, endType):
        return _clipper_642.ClipperOffset_AddPaths(self, paths, joinType, endType)

    def Execute(self, *args):
        return _clipper_642.ClipperOffset_Execute(self, *args)

    def Clear(self):
        return _clipper_642.ClipperOffset_Clear(self)
    MiterLimit = property(_clipper_642.ClipperOffset_MiterLimit_get, _clipper_642.ClipperOffset_MiterLimit_set)
    ArcTolerance = property(_clipper_642.ClipperOffset_ArcTolerance_get, _clipper_642.ClipperOffset_ArcTolerance_set)

# Register ClipperOffset in _clipper_642:
_clipper_642.ClipperOffset_swigregister(ClipperOffset)

class clipperException(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def __init__(self, description):
        _clipper_642.clipperException_swiginit(self, _clipper_642.new_clipperException(description))
    __swig_destroy__ = _clipper_642.delete_clipperException

    def what(self):
        return _clipper_642.clipperException_what(self)

# Register clipperException in _clipper_642:
_clipper_642.clipperException_swigregister(clipperException)

class IntPointVector(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def iterator(self):
        return _clipper_642.IntPointVector_iterator(self)
    def __iter__(self):
        return self.iterator()

    def __nonzero__(self):
        return _clipper_642.IntPointVector___nonzero__(self)

    def __bool__(self):
        return _clipper_642.IntPointVector___bool__(self)

    def __len__(self):
        return _clipper_642.IntPointVector___len__(self)

    def __getslice__(self, i, j):
        return _clipper_642.IntPointVector___getslice__(self, i, j)

    def __setslice__(self, *args):
        return _clipper_642.IntPointVector___setslice__(self, *args)

    def __delslice__(self, i, j):
        return _clipper_642.IntPointVector___delslice__(self, i, j)

    def __delitem__(self, *args):
        return _clipper_642.IntPointVector___delitem__(self, *args)

    def __getitem__(self, *args):
        return _clipper_642.IntPointVector___getitem__(self, *args)

    def __setitem__(self, *args):
        return _clipper_642.IntPointVector___setitem__(self, *args)

    def pop(self):
        return _clipper_642.IntPointVector_pop(self)

    def append(self, x):
        return _clipper_642.IntPointVector_append(self, x)

    def empty(self):
        return _clipper_642.IntPointVector_empty(self)

    def size(self):
        return _clipper_642.IntPointVector_size(self)

    def swap(self, v):
        return _clipper_642.IntPointVector_swap(self, v)

    def begin(self):
        return _clipper_642.IntPointVector_begin(self)

    def end(self):
        return _clipper_642.IntPointVector_end(self)

    def rbegin(self):
        return _clipper_642.IntPointVector_rbegin(self)

    def rend(self):
        return _clipper_642.IntPointVector_rend(self)

    def clear(self):
        return _clipper_642.IntPointVector_clear(self)

    def get_allocator(self):
        return _clipper_642.IntPointVector_get_allocator(self)

    def pop_back(self):
        return _clipper_642.IntPointVector_pop_back(self)

    def erase(self, *args):
        return _clipper_642.IntPointVector_erase(self, *args)

    def __init__(self, *args):
        _clipper_642.IntPointVector_swiginit(self, _clipper_642.new_IntPointVector(*args))

    def push_back(self, x):
        return _clipper_642.IntPointVector_push_back(self, x)

    def front(self):
        return _clipper_642.IntPointVector_front(self)

    def back(self):
        return _clipper_642.IntPointVector_back(self)

    def assign(self, n, x):
        return _clipper_642.IntPointVector_assign(self, n, x)

    def resize(self, *args):
        return _clipper_642.IntPointVector_resize(self, *args)

    def insert(self, *args):
        return _clipper_642.IntPointVector_insert(self, *args)

    def reserve(self, n):
        return _clipper_642.IntPointVector_reserve(self, n)

    def capacity(self):
        return _clipper_642.IntPointVector_capacity(self)

    def reverse(self):
        return _clipper_642.IntPointVector_reverse(self)
    __swig_destroy__ = _clipper_642.delete_IntPointVector

# Register IntPointVector in _clipper_642:
_clipper_642.IntPointVector_swigregister(IntPointVector)

class PathVector(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def iterator(self):
        return _clipper_642.PathVector_iterator(self)
    def __iter__(self):
        return self.iterator()

    def __nonzero__(self):
        return _clipper_642.PathVector___nonzero__(self)

    def __bool__(self):
        return _clipper_642.PathVector___bool__(self)

    def __len__(self):
        return _clipper_642.PathVector___len__(self)

    def __getslice__(self, i, j):
        return _clipper_642.PathVector___getslice__(self, i, j)

    def __setslice__(self, *args):
        return _clipper_642.PathVector___setslice__(self, *args)

    def __delslice__(self, i, j):
        return _clipper_642.PathVector___delslice__(self, i, j)

    def __delitem__(self, *args):
        return _clipper_642.PathVector___delitem__(self, *args)

    def __getitem__(self, *args):
        return _clipper_642.PathVector___getitem__(self, *args)

    def __setitem__(self, *args):
        return _clipper_642.PathVector___setitem__(self, *args)

    def pop(self):
        return _clipper_642.PathVector_pop(self)

    def append(self, x):
        return _clipper_642.PathVector_append(self, x)

    def empty(self):
        return _clipper_642.PathVector_empty(self)

    def size(self):
        return _clipper_642.PathVector_size(self)

    def swap(self, v):
        return _clipper_642.PathVector_swap(self, v)

    def begin(self):
        return _clipper_642.PathVector_begin(self)

    def end(self):
        return _clipper_642.PathVector_end(self)

    def rbegin(self):
        return _clipper_642.PathVector_rbegin(self)

    def rend(self):
        return _clipper_642.PathVector_rend(self)

    def clear(self):
        return _clipper_642.PathVector_clear(self)

    def get_allocator(self):
        return _clipper_642.PathVector_get_allocator(self)

    def pop_back(self):
        return _clipper_642.PathVector_pop_back(self)

    def erase(self, *args):
        return _clipper_642.PathVector_erase(self, *args)

    def __init__(self, *args):
        _clipper_642.PathVector_swiginit(self, _clipper_642.new_PathVector(*args))

    def push_back(self, x):
        return _clipper_642.PathVector_push_back(self, x)

    def front(self):
        return _clipper_642.PathVector_front(self)

    def back(self):
        return _clipper_642.PathVector_back(self)

    def assign(self, n, x):
        return _clipper_642.PathVector_assign(self, n, x)

    def resize(self, *args):
        return _clipper_642.PathVector_resize(self, *args)

    def insert(self, *args):
        return _clipper_642.PathVector_insert(self, *args)

    def reserve(self, n):
        return _clipper_642.PathVector_reserve(self, n)

    def capacity(self):
        return _clipper_642.PathVector_capacity(self)
    __swig_destroy__ = _clipper_642.delete_PathVector

# Register PathVector in _clipper_642:
_clipper_642.PathVector_swigregister(PathVector)

class PolyNodes(object):
    thisown = property(lambda x: x.this.own(), lambda x, v: x.this.own(v), doc="The membership flag")
    __repr__ = _swig_repr

    def iterator(self):
        return _clipper_642.PolyNodes_iterator(self)
    def __iter__(self):
        return self.iterator()

    def __nonzero__(self):
        return _clipper_642.PolyNodes___nonzero__(self)

    def __bool__(self):
        return _clipper_642.PolyNodes___bool__(self)

    def __len__(self):
        return _clipper_642.PolyNodes___len__(self)

    def __getslice__(self, i, j):
        return _clipper_642.PolyNodes___getslice__(self, i, j)

    def __setslice__(self, *args):
        return _clipper_642.PolyNodes___setslice__(self, *args)

    def __delslice__(self, i, j):
        return _clipper_642.PolyNodes___delslice__(self, i, j)

    def __delitem__(self, *args):
        return _clipper_642.PolyNodes___delitem__(self, *args)

    def __getitem__(self, *args):
        return _clipper_642.PolyNodes___getitem__(self, *args)

    def __setitem__(self, *args):
        return _clipper_642.PolyNodes___setitem__(self, *args)

    def pop(self):
        return _clipper_642.PolyNodes_pop(self)

    def append(self, x):
        return _clipper_642.PolyNodes_append(self, x)

    def empty(self):
        return _clipper_642.PolyNodes_empty(self)

    def size(self):
        return _clipper_642.PolyNodes_size(self)

    def swap(self, v):
        return _clipper_642.PolyNodes_swap(self, v)

    def begin(self):
        return _clipper_642.PolyNodes_begin(self)

    def end(self):
        return _clipper_642.PolyNodes_end(self)

    def rbegin(self):
        return _clipper_642.PolyNodes_rbegin(self)

    def rend(self):
        return _clipper_642.PolyNodes_rend(self)

    def clear(self):
        return _clipper_642.PolyNodes_clear(self)

    def get_allocator(self):
        return _clipper_642.PolyNodes_get_allocator(self)

    def pop_back(self):
        return _clipper_642.PolyNodes_pop_back(self)

    def erase(self, *args):
        return _clipper_642.PolyNodes_erase(self, *args)

    def __init__(self, *args):
        _clipper_642.PolyNodes_swiginit(self, _clipper_642.new_PolyNodes(*args))

    def push_back(self, x):
        return _clipper_642.PolyNodes_push_back(self, x)

    def front(self):
        return _clipper_642.PolyNodes_front(self)

    def back(self):
        return _clipper_642.PolyNodes_back(self)

    def assign(self, n, x):
        return _clipper_642.PolyNodes_assign(self, n, x)

    def resize(self, *args):
        return _clipper_642.PolyNodes_resize(self, *args)

    def insert(self, *args):
        return _clipper_642.PolyNodes_insert(self, *args)

    def reserve(self, n):
        return _clipper_642.PolyNodes_reserve(self, n)

    def capacity(self):
        return _clipper_642.PolyNodes_capacity(self)
    __swig_destroy__ = _clipper_642.delete_PolyNodes

# Register PolyNodes in _clipper_642:
_clipper_642.PolyNodes_swigregister(PolyNodes)



# miserable attempt to debug - simply add python code like this
def IntPointVector__repr__(self):
    res = "IntPointVector #%d\n" % len(self)
    for i, pt in enumerate(self):
       res += "  [%d] %8d %8d\n" % (i, pt.X, pt.Y)
    return res 
IntPointVector.__repr__ = IntPointVector__repr__


def PathVector__repr__(self):
    res = "PathVector #%d\n" % len(self)
    for k, path in enumerate(self):
#res += repr(path)
        for i, pt in enumerate(path):
            res += "  [%d] %8d %8d\n" % (i, pt.X, pt.Y)
    return res 
PathVector.__repr__ = PathVector__repr__


class ClipType:
    ctIntersection = 0
    ctUnion = 1
    ctDifference = 2
    ctXor = 3

class PolyType:
    ptSubject = 0
    ptClip = 1

class PolyFillType:
    pftEvenOdd = 0
    pftNonZero = 1
    pftPositive = 2
    pftNegative = 3

class InitOptions:
    ioReverseSolution = 1
    ioStrictlySimple = 2
    ioPreserveCollinear = 4

class JoinType:
    jtSquare = 0 
    jtRound = 1 
    jtMiter= 2

class EndType:
    etClosedPolygon = 0
    etClosedLine = 1
    etOpenButt = 2
    etOpenSquare = 3
    etOpenRound = 4

class EdgeSide:
    esLeft = 1
    esRight = 2

def dumpIntPoint(label, pt):
    if label: print(label)
    print(pt.X, pt.Y)

def dumpPath(label, path):
    if label: print("---- path  ", label , "  len#", len(path))
    for pt in path:
        dumpIntPoint(None, pt)

def dumpPaths(label, paths):
    print(label)
    for path in paths:
        print("---- path   len#", len(path))
        dumpPath(None, path)




