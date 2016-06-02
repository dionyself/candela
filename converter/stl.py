#!/usr/bin/env python

"""
    pySTL2GC  Copyright (C) 2016 Dionys Rosario
    This program comes with ABSOLUTELY NO WARRANTY
    This is free software, and you are welcome to redistribute it
    under certain conditions.
    Usage: "cat file.stl | stl.py > file.ngc"
"""

import ocl
import logging
import subproccess
logging.basicConfig(level=20)

__autor__ = "Dionys Rosario"
__copyright__ = "Copyright 2016, SublimeTech"
__credits__ = ["Jakob Flierl"]
__licence__ = "Free BSD"
__version__ = "0.0.1"

def to_gcode(filename="./var/assets/sphere.stl", use_native=False):
    if use_native:
        return use_native(filename)
    zsafe = 5.0
    zstep = 3.0
    d = 2.0
    d_overlap = 1 - 0.75  # step percentage
    corner = 0.0  # d

    s = ocl.STLSurf()
    ocl.STLReader(filename, s)
    # s.rotate(0,0,0)
    logging.info(s)
    logging.info(s.bb)
    zdim = s.bb.maxpt.z - s.bb.minpt.z
    logging.info("zdim "+ str(zdim))
    zstart = s.bb.maxpt.z - zstep
    logging.info("zstart " + str(zstart))
    c = ocl.CylCutter(d, 6)
    logging.info(c)

    apdc  = ocl.AdaptivePathDropCutter()
    apdc.setSTL(s)
    apdc.setCutter(c)
    apdc.setSampling(d*d_overlap)
    apdc.setMinSampling(d*d_overlap / 100)

    minx = s.bb.minpt.x - corner
    miny = s.bb.minpt.y - corner
    maxx = s.bb.maxpt.x + corner
    maxy = s.bb.maxpt.y + corner
    z = s.bb.minpt.z - zsafe

    dx = d * d_overlap
    dy = d * d_overlap

    p = zigzag_x(minx, dx, maxx, miny, dy, maxy, z)
    apdc.setPath(p)
    apdc.setZ(z)
    logging.info("calculating.. ")
    # apdc.setThreads(4)
    apdc.run()
    logging.info("done.")

    w = GCodeWriter()
    print "G21 F900"
    print "G64 P0.001"  # path control mode : constant velocity
    print "M03 S13500"  # start spindle
    print "GO X%s Y%s Z%s" % (s.bb.minpt.x, s.bb.minpt.y, zsafe)
    zcurr = zstart
    pts = apdc.getCLPoints()
    fst = True
    while zcurr > (s.bb.minpt.z - zstep):
        logging.error(zcurr)
        for pt in pts:
            z = - min(-cp.z, -zcurr) - s.bb.maxpt.z
            #if !isNearlyEqual(z, 0):
            if fst:
                w.g0(cp.x, cp.y, zsafe)
                w.g0(cp.x, cp.y, 0)
                fst = False
            w.g1(cp.x, cp.y, z)
            #endif
        zcurr -= zstep
        reverse(pts.begin(), pts.end())
    print "G0Z" + str(zsafe)
    print "M05" # stop spindle
    print "G0X" + str(s.bb.minpt.x) + " Y" + str(s.bb.minpt.y)
    print "M2"
    print "%"
    return 0

def zigzag_x(minx, dx, maxx, miny, dy, maxy, z):
        p = ocl.Path()
        rev = 0
        while miny < maxy:
            if rev == 0:
                p.append(ocl.Line(ocl.Point(minx, miny, z), ocl.Point(maxx, miny, z)))
                rev = 1
            else:
                p.append(Line(Point(maxx, miny, z), Point(minx, miny, z)))
                rev = 0
            miny += dy
        return p

def zigzag_y(minx, dx, maxx, miny, dy, maxy, z):
        p = ocl.Path()
        rev = 0;
        for i in range(minx, maxx, dx):
            if rev == 0:
                p.append(ocl.Line(ocl.Point(minx, i, z), ocl.Point(maxy, i, z)))
                rev = 1;
            else:
                p.append(Line(Point(maxy, i, z), Point(minx, i, z)));
                rev = 0;
        return p;

def isNearlyEqual(a, b, factor=5):
    return (a==b or int(a*10**factor)==int(b*10**factor))


class GCodeWriter:
    def g1(x, y, z):
        print "G1 X%s Y%s Z%s" % (x, y, z)
    def g0(x, y, z):
        print "G0 X%s Y%s Z%s" % (x, y, z)

def native(filename):
    return subprocess.call("cat %s | ./var/pkg/stl2ngc/stl2ngc" % filename, shell=True)

if __name__ == "__main__":
    to_gcode(use_native=True)
    #  to_gcode(filename="/dev/stdin", use_native=True)
