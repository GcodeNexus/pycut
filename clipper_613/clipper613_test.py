import clipper_613 as clipper

def test1():
    outer = clipper.IntPointVector()
    outer.append(clipper.IntPoint(180,200))
    outer.append(clipper.IntPoint(260,200))
    outer.append(clipper.IntPoint(260,150))
    outer.append(clipper.IntPoint(180,150))

    inner = clipper.IntPointVector()
    inner.append(clipper.IntPoint(215,160))
    inner.append(clipper.IntPoint(230,190))
    inner.append(clipper.IntPoint(200,190))

    subj = clipper.PathVector()
    subj.append(outer)
    subj.append(inner)

    clip = clipper.PathVector()
    clip_0 = clipper.IntPointVector()
    clip_0.append(clipper.IntPoint(190,210))
    clip_0.append(clipper.IntPoint(240,210))
    clip_0.append(clipper.IntPoint(240,130))
    clip_0.append(clipper.IntPoint(190,130))
    clip.append(clip_0)

    c = clipper.Clipper()

    c.AddPaths(subj, clipper.PolyType.ptSubject, True)
    c.AddPaths(clip, clipper.PolyType.ptClip, True)

    solution = clipper.PathVector()
    
    c.Execute(clipper.ClipType.ctIntersection, 
            solution,
            clipper.PolyFillType.pftNonZero, 
            clipper.PolyFillType.pftNonZero)

    clipper.dumpPaths("subj", subj)
    clipper.dumpPaths("clip", clip)
    clipper.dumpPaths("solution", solution)

def test(clipType: clipper.ClipType):
    c1 = clipper.IntPointVector()
    c1.append(clipper.IntPoint(20,20))
    c1.append(clipper.IntPoint(20,60))
    c1.append(clipper.IntPoint(60,60))
    c1.append(clipper.IntPoint(60,20))

    subj = clipper.PathVector()
    subj.append(c1)

    clip = clipper.PathVector()
    c2 = clipper.IntPointVector()
    c2.append(clipper.IntPoint(40,40))
    c2.append(clipper.IntPoint(40,80))
    c2.append(clipper.IntPoint(80,80))
    c2.append(clipper.IntPoint(80,40))
    clip.append(c2)

    c = clipper.Clipper()

    c.AddPaths(subj, clipper.PolyType.ptSubject, True)
    c.AddPaths(clip, clipper.PolyType.ptClip, True)

    solution = clipper.PathVector()
    
    c.Execute(clipType, 
            solution,
            clipper.PolyFillType.pftNonZero, 
            clipper.PolyFillType.pftNonZero)

    clipper.dumpPaths("subj", subj)
    clipper.dumpPaths("clip", clip)
    clipper.dumpPaths("solution", solution)

def test_offset():
    outer = clipper.IntPointVector()
    outer.append(clipper.IntPoint(180,200))
    outer.append(clipper.IntPoint(260,200))
    outer.append(clipper.IntPoint(260,150))
    outer.append(clipper.IntPoint(180,150))

    subj = clipper.PathVector()
    subj.append(outer)

    joinType = clipper.JoinType.jtRound
    endType = clipper.EndType.etClosedPolygon

    co = clipper.ClipperOffset(2, 0.1)
    co.AddPaths(subj, joinType, endType)
        
    offsetted = clipper.PathVector()
    co.Execute(offsetted, -1)

    clipper.dumpPaths("offset input", subj)
    clipper.dumpPaths("solution offset", offsetted)

    #clipper.CleanPolygons(offsetted, 1)
    return offsetted

def test_openline_diff():
    '''
       - subject is an open line
       - clippers are the (closed) tabs
    
       - result is a list of open lines, where none of their parts
       are in the tab

    -> wring result!
    '''
    print("test_openline_diff")

    line = clipper.IntPointVector()
    line.append(clipper.IntPoint(100,100))
    line.append(clipper.IntPoint(600,100))
    line.append(clipper.IntPoint(600,600))
    line.append(clipper.IntPoint(100,600))
    line.append(clipper.IntPoint(100,100)) # close the path! but give it as "opened"

    tab1 = clipper.IntPointVector()
    tab1.append(clipper.IntPoint(200,80))
    tab1.append(clipper.IntPoint(300,80))
    tab1.append(clipper.IntPoint(300,120))
    tab1.append(clipper.IntPoint(200,120))

    tab2 = clipper.IntPointVector()
    tab2.append(clipper.IntPoint( 80,200))
    tab2.append(clipper.IntPoint(120,200))
    tab2.append(clipper.IntPoint(120,300))
    tab2.append(clipper.IntPoint( 80,300))

    # tab3
    tab3 = clipper.IntPointVector()
    tab3.append(clipper.IntPoint(580,200))
    tab3.append(clipper.IntPoint(620,200))
    tab3.append(clipper.IntPoint(620,300))
    tab3.append(clipper.IntPoint(580,300))
    
    tabs = clipper.PathVector()
    tabs.append(tab1)
    tabs.append(tab2)
    tabs.append(tab3)


    c = clipper.Clipper()
    c.AddPath(line, clipper.PolyType.ptSubject, False)
    c.AddPaths(tabs, clipper.PolyType.ptClip, True)

    polytree = clipper.PolyTree()

    c.Execute(clipper.ClipType.ctDifference, 
            polytree,
            clipper.PolyFillType.pftNonZero, 
            clipper.PolyFillType.pftNonZero)

    print("Test OpenLine Difference with Tabs")
    print("Resulting # paths:", polytree.Total())

    paths = clipper.PathVector()
    clipper.OpenPathsFromPolyTree(polytree, paths)

    print(paths)

if __name__ == '__main__':
    print("CLIPPER VERSION", clipper.CLIPPER_VERSION)
    
    #test1()
    #test(clipper.ClipType.ctUnion)
    #test(clipper.ClipType.ctIntersection)
    #test(clipper.ClipType.ctXor)
    #test(clipper.ClipType.ctDifferences)

    #test_offset()

    # version 6.4.2 is better - here bad results
    test_openline_diff()