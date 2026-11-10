"""Six-motor frame for the cube solver.

Three printed part types:
  frame_base.stl   deck on four legs; the bottom motor hangs under the deck
  frame_tower.stl  side motor tower, print four; bolts to the deck through
                   slots so it can slide 5 mm in or out
  frame_top.stl    cross plate that sits on the four towers and carries the
                   top motor; lifts off to load the cube

Run:  python frame.py
Writes print-oriented STL files to ./stl and reports interference checks.

All dimensions in millimetres. The cube centre is on the Z axis at height ZC.
"""
import math
import pathlib
import sys

import numpy as np
import trimesh
from manifold3d import Manifold

from bench_stand import (
    CUBE, GAP, HOLE_PITCH, M3_CLEAR, MOTOR_LEN, NEMA, PILOT_D, PLATE_T, SEG,
    SHAFT_D, SHAFT_LEN, box, cyl_x, cyl_z, extrude, gusset, rounded_rect,
    slab_yz, to_trimesh,
)

# ---------------------------------------------------------------- parameters
ZC = 115.0                         # cube centre height above the bench
R_IN = CUBE / 2 + GAP              # 54: plate face nearest the cube
R_FACE = R_IN + PLATE_T            # 60: motor mounting face
DECK_Z0 = ZC - R_FACE              # 55: deck underside, bottom motor face
DECK_Z1 = ZC - R_IN                # 61: deck top
TOP_Z0 = ZC + R_IN                 # 169: top plate underside, tower tops
TOP_Z1 = ZC + R_FACE               # 175: top plate upper face, top motor face
ARM_W = 80.0                       # deck arm width
ARM_R = 100.0                      # deck arm reach from the centre
LEG_T = 6.0
FOOT_W = 76.0                      # tower foot width
FOOT_R1 = 96.0                     # tower foot outer reach
BOLT_R = 75.0                      # tower bolt position (mid-slot)
BOLT_T = 33.0                      # tower bolt offset either side
SLIDE = 5.0                        # tower travel each way
TOP_ARM_W = 70.0
TOP_ARM_R = 70.0
TOWER_PILOT_R = R_IN + PLATE_T / 2  # 57: screw holes in the tower's top edge
TOWER_PILOT_T = 16.0
OUT = pathlib.Path(__file__).parent


def four(part):
    """Copies of a +X part at 0, 90, 180 and 270 degrees about Z."""
    out = Manifold()
    for k in range(4):
        out += part.rotate([0, 0, 90 * k])
    return out


def cross(width, reach, z0, z1, r=8.0):
    arm = extrude(rounded_rect(2 * reach, width, r), z1 - z0).translate([0, 0, z0])
    return arm + arm.rotate([0, 0, 90])


def motor_holes_z(z0, z1):
    holes = cyl_z(PILOT_D / 2, z0, z1)
    for sx in (1, -1):
        for sy in (1, -1):
            holes += cyl_z(M3_CLEAR / 2, z0, z1, x=sx * HOLE_PITCH / 2, y=sy * HOLE_PITCH / 2)
    return holes


def slot_z(x0, x1, y, r, z0, z1):
    return (cyl_z(r, z0, z1, x=x0, y=y) + cyl_z(r, z0, z1, x=x1, y=y)
            + box(x0, x1, y - r, y + r, z0, z1))


# ---------------------------------------------------------------------- base
def build_base():
    deck = cross(ARM_W, ARM_R, DECK_Z0, DECK_Z1) + cyl_z(62.0, DECK_Z0, DECK_Z1)

    leg = box(ARM_R - LEG_T, ARM_R, -ARM_W / 2 + 8, ARM_W / 2 - 8, 0, DECK_Z0 + 1)
    leg -= cyl_x(24.0, ARM_R - LEG_T - 1, ARM_R + 1, z=0)      # cable arch
    base = deck + four(leg)

    base -= motor_holes_z(DECK_Z0 - 1, DECK_Z1 + 1)
    nut_r = 5.7 / 2 / math.cos(math.radians(30))
    bolts = Manifold()
    for sy in (1, -1):
        bolts += cyl_z(M3_CLEAR / 2, DECK_Z0 - 1, DECK_Z1 + 1, x=BOLT_R, y=sy * BOLT_T)
        bolts += Manifold.cylinder(2.6 + 1, nut_r, nut_r, 6).translate(
            [BOLT_R, sy * BOLT_T, DECK_Z0 - 1])
    base -= four(bolts)
    return base


# --------------------------------------------------------------------- tower
def build_tower():
    """Tower for the +X motor, in its assembled position."""
    height = TOP_Z0 - DECK_Z1
    plate = slab_yz(CUBE, height, 3.0, R_IN, R_FACE).translate([0, 0, DECK_Z1])
    foot_len = FOOT_R1 - R_IN
    foot = extrude(rounded_rect(foot_len, FOOT_W, 5.0), PLATE_T).translate(
        [R_IN + foot_len / 2, 0, DECK_Z1])
    tower = plate + foot
    for sign in (1, -1):
        ya, yb = sorted((sign * 24.0, sign * 28.0))
        tower += gusset(
            [(R_FACE, DECK_Z1 + PLATE_T), (FOOT_R1 - 2, DECK_Z1 + PLATE_T),
             (R_FACE, DECK_Z1 + PLATE_T + 50)], ya, yb)

    # cradle: the motor body rests on a shelf and sits between two cheeks
    motor_bottom_z = ZC - NEMA / 2 - 0.3
    half = NEMA / 2 + 0.3
    cradle = box(R_FACE, FOOT_R1 - 2, -(half + 4.0), half + 4.0, DECK_Z1 + PLATE_T - 0.5, ZC)
    cradle -= box(R_FACE - 1, FOOT_R1, -half, half, motor_bottom_z, ZC + 1)
    cradle -= cyl_x(11.0, R_FACE, FOOT_R1, z=motor_bottom_z - 3.0 - 11.0)   # lightening tunnel
    tower += cradle

    tower -= cyl_x(PILOT_D / 2, R_IN - 1, R_FACE + 1, z=ZC)
    for sy in (1, -1):
        for sz in (1, -1):
            tower -= cyl_x(M3_CLEAR / 2, R_IN - 1, R_FACE + 1,
                           y=sy * HOLE_PITCH / 2, z=ZC + sz * HOLE_PITCH / 2)
        tower -= slot_z(BOLT_R - SLIDE, BOLT_R + SLIDE, sy * BOLT_T, M3_CLEAR / 2,
                        DECK_Z1 - 1, DECK_Z1 + PLATE_T + 1)
        # pilot holes for the screws that hold the top plate down
        tower -= cyl_z(1.4, TOP_Z0 - 12, TOP_Z0 + 1, x=TOWER_PILOT_R, y=sy * TOWER_PILOT_T)
    return tower


# ----------------------------------------------------------------------- top
def build_top():
    top = cross(TOP_ARM_W, TOP_ARM_R, TOP_Z0, TOP_Z1)
    lips = Manifold()
    for sy in (1, -1):
        ya, yb = sorted((sy * (CUBE / 2 + 0.3), sy * (CUBE / 2 + 4.3)))
        lips += box(R_IN - SLIDE - 1, R_FACE + SLIDE + 1, ya, yb, TOP_Z0 - 4, TOP_Z0 + 0.5)
    top += four(lips)
    top -= motor_holes_z(TOP_Z0 - 1, TOP_Z1 + 1)
    slots = Manifold()
    for sy in (1, -1):
        slots += slot_z(TOWER_PILOT_R - SLIDE, TOWER_PILOT_R + SLIDE, sy * TOWER_PILOT_T,
                        M3_CLEAR / 2, TOP_Z0 - 1, TOP_Z1 + 1)
    top -= four(slots)
    return top


# ----------------------------------------------------------- stand-in solids
def motor_x():
    """Side motor on the +X tower, with its shaft."""
    body = box(R_FACE, R_FACE + MOTOR_LEN, -NEMA / 2, NEMA / 2, ZC - NEMA / 2, ZC + NEMA / 2)
    return body + cyl_x(SHAFT_D / 2, R_FACE - SHAFT_LEN, R_FACE, z=ZC)


def motor_bottom():
    body = box(-NEMA / 2, NEMA / 2, -NEMA / 2, NEMA / 2, DECK_Z0 - MOTOR_LEN, DECK_Z0)
    return body + cyl_z(SHAFT_D / 2, DECK_Z0, DECK_Z0 + SHAFT_LEN)


def motor_top():
    body = box(-NEMA / 2, NEMA / 2, -NEMA / 2, NEMA / 2, TOP_Z1, TOP_Z1 + MOTOR_LEN)
    return body + cyl_z(SHAFT_D / 2, TOP_Z1 - SHAFT_LEN, TOP_Z1)


def swept_layers():
    """Volume swept by every face layer as it turns (corner radius of the cube)."""
    r = CUBE / 2 * math.sqrt(2) + 0.2
    t = CUBE / 3
    sweep = cyl_x(r, CUBE / 2 - t, CUBE / 2, z=ZC) + cyl_x(r, -CUBE / 2, -CUBE / 2 + t, z=ZC)
    sweep += sweep.translate([0, 0, -ZC]).rotate([0, 0, 90]).translate([0, 0, ZC])
    sweep += cyl_z(r, ZC + CUBE / 2 - t, ZC + CUBE / 2) + cyl_z(r, ZC - CUBE / 2, ZC - CUBE / 2 + t)
    return sweep


def overlap(a, b):
    return (a ^ b).volume()


def print_oriented(mesh, flip):
    m = mesh.copy()
    if flip:
        m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return m


def main():
    (OUT / "stl").mkdir(exist_ok=True)
    base, tower, top = build_base(), build_tower(), build_top()
    towers = four(tower)
    side_motors = four(motor_x())
    sweep = swept_layers()

    checks = {
        "base vs towers": overlap(base, towers),
        "top vs towers": overlap(top, towers),
        "base vs top": overlap(base, top),
        "frame vs turning cube layers": overlap(base + towers + top, sweep),
        "frame vs side motors": overlap(base + top, side_motors),
        "towers vs their motors": overlap(tower, motor_x()),
        "side motors vs each other": overlap(motor_x(), motor_x().rotate([0, 0, 90])),
        "base vs bottom motor": overlap(base, motor_bottom()),
        "top vs top motor": overlap(top, motor_top()),
        "towers pushed in 5 mm vs turning layers": overlap(
            four(tower.translate([-SLIDE, 0, 0])), sweep),
        "towers pushed in 5 mm vs each other": overlap(
            tower.translate([-SLIDE, 0, 0]),
            tower.translate([-SLIDE, 0, 0]).rotate([0, 0, 90])),
    }
    for name, vol in checks.items():
        print(f"{'OK ' if vol < 1.0 else 'HIT'} {name}: {vol:.1f} mm3")

    parts = {"frame_base": (base, True), "frame_tower": (tower, False), "frame_top": (top, True)}
    for name, (solid, flip) in parts.items():
        mesh = to_trimesh(solid)
        printable = print_oriented(mesh, flip)
        printable.export(OUT / "stl" / f"{name}.stl")
        size = printable.bounds[1] - printable.bounds[0]
        print(f"{name}: watertight={mesh.is_watertight} "
              f"size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
              f"solid volume={mesh.volume / 1000:.1f} cm3")
        if "--assembly" in sys.argv:
            out = pathlib.Path(sys.argv[sys.argv.index("--assembly") + 1])
            mesh.export(out / f"{name}_assembled.stl")


if __name__ == "__main__":
    main()
