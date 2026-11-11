"""Stand-in for the parts of manifold3d that the CAD scripts use, built on
CadQuery's exact (B-rep) kernel instead of triangle meshes.

Importing this module registers it under the name "manifold3d". Any script
imported afterwards (bench_stand.py, frame.py) then builds true solids with
real cylinders and flat faces, which can be written to STEP for Inventor.
The geometry code itself stays in one place.

Only inventor_export.py should import this. Import it before bench_stand.
"""
import math
import sys
import types

import cadquery as cq
import trimesh  # noqa: F401  loaded first: it probes for the real manifold3d

_O = cq.Vector(0, 0, 0)
_AXES = (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1))


class JoinType:
    Round = "arc"
    Square = "intersection"
    Miter = "intersection"


class CrossSection:
    """A closed outline in the XY plane."""

    def __init__(self, contours=None):
        self.wire = None
        if contours:
            pts = [cq.Vector(float(x), float(y), 0) for x, y in contours[0]]
            self.wire = cq.Wire.makePolygon(pts + [pts[0]])

    @staticmethod
    def square(size, center=False):
        w, h = float(size[0]), float(size[1])
        cx, cy = (0.0, 0.0) if center else (w / 2, h / 2)
        out = CrossSection()
        out.wire = cq.Workplane("XY").center(cx, cy).rect(w, h).val()
        return out

    def offset(self, delta, join_type=JoinType.Round, miter_limit=2.0, segments=0):
        out = CrossSection()
        out.wire = self.wire.offset2D(delta, join_type)[0]
        return out


class Manifold:
    """A solid, or nothing (the starting value for a running union)."""

    def __init__(self, shape=None):
        self.s = shape

    # ------------------------------------------------------------ primitives
    @staticmethod
    def cube(size, center=False):
        x, y, z = (float(v) for v in size)
        solid = cq.Solid.makeBox(x, y, z)
        if center:
            solid = solid.translate(cq.Vector(-x / 2, -y / 2, -z / 2))
        return Manifold(solid)

    @staticmethod
    def cylinder(height, radius_low, radius_high=-1.0, circular_segments=0, center=False):
        if radius_high < 0:
            radius_high = radius_low
        if 3 <= circular_segments <= 12:
            # a deliberate prism, such as the hexagonal nut pocket
            if abs(radius_low - radius_high) > 1e-9:
                raise NotImplementedError("tapered prism")
            n = circular_segments
            pts = [(radius_low * math.cos(2 * math.pi * k / n),
                    radius_low * math.sin(2 * math.pi * k / n)) for k in range(n)]
            solid = cq.Workplane("XY").polyline(pts).close().extrude(height).val()
        elif abs(radius_low - radius_high) < 1e-9:
            solid = cq.Solid.makeCylinder(radius_low, height)
        else:
            solid = cq.Solid.makeCone(radius_low, radius_high, height)
        if center:
            solid = solid.translate(cq.Vector(0, 0, -height / 2))
        return Manifold(solid)

    @staticmethod
    def extrude(cross_section, height):
        return Manifold(cq.Solid.extrudeLinear(cross_section.wire, [], cq.Vector(0, 0, height)))

    # ------------------------------------------------------------ transforms
    def translate(self, v):
        if self.s is None:
            return self
        return Manifold(self.s.translate(cq.Vector(*(float(c) for c in v))))

    def rotate(self, v):
        """Degrees about X, then Y, then Z, as manifold3d does."""
        if self.s is None:
            return self
        s = self.s
        for axis, angle in zip(_AXES, v):
            if angle:
                s = s.rotate(_O, axis, float(angle))
        return Manifold(s)

    # -------------------------------------------------------------- booleans
    def __add__(self, other):
        if self.s is None:
            return other
        if other.s is None:
            return self
        return Manifold(self.s.fuse(other.s))

    def __sub__(self, other):
        if self.s is None or other.s is None:
            return self
        return Manifold(self.s.cut(other.s))

    def __xor__(self, other):
        if self.s is None or other.s is None:
            return Manifold()
        return Manifold(self.s.intersect(other.s))

    # --------------------------------------------------------------- queries
    def volume(self):
        return 0.0 if self.s is None else self.s.Volume()

    def is_empty(self):
        return self.volume() == 0.0

    def solid(self):
        """The finished shape with seams between coplanar faces merged."""
        try:
            return self.s.clean()
        except Exception:
            return self.s


_module = types.ModuleType("manifold3d")
_module.Manifold = Manifold
_module.CrossSection = CrossSection
_module.JoinType = JoinType
sys.modules["manifold3d"] = _module
