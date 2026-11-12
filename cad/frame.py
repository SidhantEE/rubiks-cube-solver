"""Six-motor frame for the cube solver.

Box columns on a flat base, after the Flatland and Rose record robot of 2016
(github.com/jayflatland/HighFrequencyTwister): each side motor sits in a
four-walled cradle on top of a hollow column, and a bridge across two
opposite columns carries the sixth motor and lifts off to load the cube.
The geometry here is our own; only the layout follows theirs.

Printed parts:
  frame_base.stl        flat cross-shaped floor with raised pads for the
                        towers and the pedestal
  frame_pedestal.stl    box around the bottom motor; the motor hangs inside
                        from its top plate; screws to the base from below
  frame_tower.stl       side motor column, print two
  frame_tower_tall.stl  the same column with two posts that carry the bridge,
                        print two (they go opposite each other)
  frame_top.stl         bridge across the two tall towers, with a walled
                        collar for the top motor

How each side motor is held: it drops into its cradle from above, shaft in
the slot of the front wall. Four M3 screws go through the front wall into the
motor face, the body sits on a shelf between four walls, and two M3 clamp
screws through the side walls pinch the body near its back end.

Each tower bolts to the base through slots so it can slide 5 mm in or out.

Run:  python frame.py
Writes print-oriented STL files to ./stl and reports interference checks.
Add --preview to also write preview/frame_*.png.

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
    SHAFT_D, SHAFT_LEN, box, cyl_x, cyl_y, cyl_z, extrude, gusset,
    rounded_rect, to_trimesh,
)

# ---------------------------------------------------------------- parameters
ZC = 115.0                         # cube centre height above the bench
R_IN = CUBE / 2 + GAP              # 54: plate face nearest the cube
R_FACE = R_IN + PLATE_T            # 60: motor mounting face
DECK_Z0 = ZC - R_FACE              # 55: pedestal plate underside, bottom motor face
DECK_Z1 = ZC - R_IN                # 61: pedestal top
TOP_Z0 = ZC + R_IN                 # 169: top plate underside, tower tops
TOP_Z1 = ZC + R_FACE               # 175: top plate upper face, top motor face
BASE_A = 104.0                     # base arm reach (208 mm across)
BASE_K = 42.0                      # base arm half width
BASE_T = 2.4                       # base floor thickness
PAD_Z = 6.0                        # top of the raised pads: towers and pedestal sit here
PED_WALL = 2.4                     # pedestal wall thickness
PED_FIT = 0.4                      # pedestal clearance around the bottom motor
PED_POST = 24.0                    # pedestal corner post position (x and y)
PED_POST_R = 4.0
FOOT_W = 76.0                      # tower foot width
FOOT_R1 = 99.0                     # tower foot and column outer reach
FOOT_T = 4.0                       # tower foot thickness
BOLT_R = 75.0                      # tower bolt position (mid-slot)
BOLT_T = 33.0                      # tower bolt offset either side
SLIDE = 5.0                        # tower travel each way
MOTOR_FIT = 0.35                   # clearance each side between motor and walls
WALL_T = 4.0                       # cradle wall thickness
COL_T = 3.0                        # hollow column wall thickness, below the cradle
SHELF_T = 4.0                      # cradle floor under the side motor body
RIB_T = 2.4                        # rib under the middle of the shelf
CRADLE_TOP = ZC + NEMA / 2 + 2.0   # 138.2: top of the cradle walls
CLAMP_D = 2.8                      # clamp screw hole: an M3 screw cuts its own thread
CLAMP_X = 98.0                     # side motor clamp screws, distance from the centre
TOP_ARM_R = 68.0
TOWER_PILOT_R = R_IN + PLATE_T / 2  # 57: screw holes in the top of each post
TOWER_PILOT_T = 20.0
COLLAR_T = 3.0                     # wall around the top motor
COLLAR_H = 24.0
OUT = pathlib.Path(__file__).parent

WALL_IN = NEMA / 2 + MOTOR_FIT     # 21.5: inner face of the walls beside a motor
WALL_OUT = WALL_IN + WALL_T        # 25.5: outer face
CRADLE_X1 = R_FACE + MOTOR_LEN + 0.5 + WALL_T   # 112.5: back of the cradle


def four(part):
    """Copies of a +X part at 0, 90, 180 and 270 degrees about Z."""
    out = Manifold()
    for k in range(4):
        out += part.rotate([0, 0, 90 * k])
    return out


def two(part):
    """A +X part and its copy on -X."""
    return part + part.rotate([0, 0, 180])


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
    """Flat cross-shaped floor with raised pads."""
    a, k = BASE_A, BASE_K
    arm = extrude(rounded_rect(2 * a, 2 * k, 8.0), BASE_T)
    base = arm + arm.rotate([0, 0, 90])

    # raised pads: one under each side of a tower, a ring under the pedestal
    pads = Manifold()
    for sy in (1, -1):
        ya, yb = sorted((sy * 19.0, sy * (k - 1.0)))
        pads += box(R_IN - SLIDE - 1, a - 3, ya, yb, 0, PAD_Z)
    base += four(pads) + box(-28, 28, -28, 28, 0, PAD_Z)
    base -= box(-18, 18, -18, 18, -1, PAD_Z + 1)

    # open floor under the middle of each tower
    base -= four(extrude(rounded_rect(56.0, 34.0, 6.0), BASE_T + 2).translate([66.0, 0, -1]))

    nut_r = 5.7 / 2 / math.cos(math.radians(30))
    bolts = Manifold()
    for sy in (1, -1):
        bolts += cyl_z(M3_CLEAR / 2, -1, PAD_Z + 1, x=BOLT_R, y=sy * BOLT_T)
        bolts += Manifold.cylinder(2.6 + 1, nut_r, nut_r, 6).translate([BOLT_R, sy * BOLT_T, -1])
    # pedestal screws come up from below; their heads sit in counterbores
    bolts += cyl_z(M3_CLEAR / 2, -1, PAD_Z + 1, x=PED_POST, y=PED_POST)
    bolts += cyl_z(3.25, -1, 3.0, x=PED_POST, y=PED_POST)
    base -= four(bolts)
    return base


def build_pedestal():
    """Box around the bottom motor. The motor hangs from the top plate."""
    hi = NEMA / 2 + PED_FIT
    ho = hi + PED_WALL
    ped = extrude(rounded_rect(2 * ho, 2 * ho, 3.0), PLATE_T).translate([0, 0, DECK_Z0])
    ped += box(-ho, ho, -ho, ho, PAD_Z, DECK_Z0 + 0.5)
    ped += four(cyl_z(PED_POST_R, PAD_Z, DECK_Z1, x=PED_POST, y=PED_POST))
    ped -= box(-hi, hi, -hi, hi, PAD_Z - 1, DECK_Z0)
    # arched opening in every wall: cable exit and air
    arch = cyl_x(12.0, -40, 40, z=30.0) + box(-40, 40, -12, 12, PAD_Z - 1, 30.0)
    ped -= arch + arch.rotate([0, 0, 90])
    ped -= motor_holes_z(DECK_Z0 - 1, DECK_Z1 + 1)
    ped -= four(cyl_z(1.4, PAD_Z - 1, PAD_Z + 10, x=PED_POST, y=PED_POST))
    return ped


# --------------------------------------------------------------------- tower
def build_tower(tall=False):
    """Box column for the +X motor, in its assembled position.

    A hollow column from the foot up to a shelf, then a four-walled cradle.
    The motor drops in from above with its shaft in the slot of the front wall.
    """
    foot_top = PAD_Z + FOOT_T
    shelf_z1 = ZC - NEMA / 2 - 0.3
    shelf_z0 = shelf_z1 - SHELF_T
    over = CRADLE_X1 - FOOT_R1          # how far the cradle overhangs the column

    # column: hollow box from the foot to the shelf, with a rib up the middle
    tower = box(R_IN, FOOT_R1, -WALL_OUT, WALL_OUT, PAD_Z, shelf_z0)
    tower -= box(R_FACE, FOOT_R1 - COL_T, -WALL_OUT + COL_T, WALL_OUT - COL_T, foot_top, shelf_z0 + 1)
    tower += box(R_FACE - 0.5, FOOT_R1 - COL_T + 0.5, -RIB_T / 2, RIB_T / 2, foot_top - 0.5, shelf_z0)
    foot_len = FOOT_R1 - R_IN
    tower += extrude(rounded_rect(foot_len, FOOT_W, 5.0), FOOT_T).translate(
        [R_IN + foot_len / 2, 0, PAD_Z])

    # cradle: front wall, two side walls, back wall and the shelf
    cradle = box(R_IN, CRADLE_X1, -WALL_OUT, WALL_OUT, shelf_z0, CRADLE_TOP)
    cradle -= box(R_FACE, CRADLE_X1 - WALL_T, -WALL_IN, WALL_IN, shelf_z1, CRADLE_TOP + 1)
    tower += cradle
    # 45 degree brackets carry the overhanging back of the cradle
    for ya, yb in ((-WALL_OUT, -WALL_IN), (-RIB_T / 2, RIB_T / 2), (WALL_IN, WALL_OUT)):
        tower += gusset([(FOOT_R1 - 0.5, shelf_z0 - over), (CRADLE_X1 - 1, shelf_z0 - 0.5),
                         (CRADLE_X1 - 1, shelf_z0 + 0.5), (FOOT_R1 - 0.5, shelf_z0 + 0.5)], ya, yb)

    if tall:
        # two posts up to the bridge: the front wall and a stub of each side wall
        for sy in (1, -1):
            ya, yb = sorted((sy * PILOT_D / 2, sy * WALL_OUT))
            tower += box(R_IN, R_FACE, ya, yb, CRADLE_TOP - 1, TOP_Z0)
            ya, yb = sorted((sy * WALL_IN, sy * WALL_OUT))
            tower += box(R_FACE - 0.5, R_FACE + 14, ya, yb, CRADLE_TOP - 1, TOP_Z0)

    # slot in the front wall for the shaft, open at the top
    tower -= (cyl_x(PILOT_D / 2, R_IN - 1, R_FACE + 1, z=ZC)
              + box(R_IN - 1, R_FACE + 1, -PILOT_D / 2, PILOT_D / 2, ZC, TOP_Z0 + 1))
    # notch in the back wall for the cable and a finger
    tower -= box(CRADLE_X1 - WALL_T - 1, CRADLE_X1 + 1, -10, 10, ZC + 6, CRADLE_TOP + 1)
    # clamp screws through the side walls, onto the motor body
    tower -= cyl_y(CLAMP_D / 2, -WALL_OUT - 1, WALL_OUT + 1, x=CLAMP_X, z=ZC)
    for sy in (1, -1):
        for sz in (1, -1):
            tower -= cyl_x(M3_CLEAR / 2, R_IN - 1, R_FACE + 1,
                           y=sy * HOLE_PITCH / 2, z=ZC + sz * HOLE_PITCH / 2)
        tower -= slot_z(BOLT_R - SLIDE, BOLT_R + SLIDE, sy * BOLT_T, M3_CLEAR / 2,
                        PAD_Z - 1, foot_top + 1)
        if tall:
            # pilot holes for the screws that hold the bridge down
            tower -= cyl_z(1.4, TOP_Z0 - 12, TOP_Z0 + 1, x=TOWER_PILOT_R, y=sy * TOWER_PILOT_T)
    return tower


def place_towers(tall, short, dx=0.0):
    """Tall towers on +X and -X, short ones on +Y and -Y, shifted radially by dx."""
    return (two(tall.translate([dx, 0, 0]))
            + two(short.translate([dx, 0, 0])).rotate([0, 0, 90]))


# ----------------------------------------------------------------------- top
def build_top():
    """Bridge across the two tall towers, with a walled collar for the top motor."""
    top = extrude(rounded_rect(2 * TOP_ARM_R, 2 * WALL_OUT + 2, 8.0), PLATE_T).translate([0, 0, TOP_Z0])
    ci = WALL_IN
    co = ci + COLLAR_T
    top += extrude(rounded_rect(2 * co, 2 * co, 3.0), COLLAR_H).translate([0, 0, TOP_Z1 - 0.5])
    top -= box(-ci, ci, -ci, ci, TOP_Z1, TOP_Z1 + COLLAR_H + 1)
    # clamp screws through two collar walls, onto the motor body
    top -= cyl_y(CLAMP_D / 2, -co - 1, co + 1, z=TOP_Z1 + COLLAR_H - 8)

    top -= motor_holes_z(TOP_Z0 - 1, TOP_Z1 + 1)
    cuts = extrude(rounded_rect(17.0, 24.0, 4.0), PLATE_T + 2).translate([36.5, 0, TOP_Z0 - 1])
    for sy in (1, -1):
        cuts += slot_z(TOWER_PILOT_R - SLIDE, TOWER_PILOT_R + SLIDE, sy * TOWER_PILOT_T,
                       M3_CLEAR / 2, TOP_Z0 - 1, TOP_Z1 + 1)
    top -= two(cuts)
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


def write_previews(solids):
    from bench_stand import render
    (OUT / "preview").mkdir(exist_ok=True)
    dark, grey, cube_c = (0.30, 0.31, 0.34), (0.62, 0.63, 0.66), (0.15, 0.55, 0.85)
    frame = [(to_trimesh(s), dark, 1.0) for s in solids["frame"]]
    motors = [(to_trimesh(s), grey, 1.0) for s in solids["motors"]]
    cube = [(to_trimesh(box(-CUBE / 2, CUBE / 2, -CUBE / 2, CUBE / 2,
                            ZC - CUBE / 2, ZC + CUBE / 2)), cube_c, 1.0)]
    render(frame + motors + cube, OUT / "preview" / "frame_assembly.png", 24, -35)
    render(frame + motors + cube, OUT / "preview" / "frame_side.png", 4, -90)
    render(frame + cube, OUT / "preview" / "frame_only.png", 24, -35)
    render([(to_trimesh(solids["tower"]), dark, 1.0)], OUT / "preview" / "frame_tower.png", 18, -40)


def main():
    (OUT / "stl").mkdir(exist_ok=True)
    base, pedestal, top = build_base(), build_pedestal(), build_top()
    short, tall = build_tower(), build_tower(tall=True)
    towers = place_towers(tall, short)
    towers_in = place_towers(tall, short, -SLIDE)
    towers_out = place_towers(tall, short, SLIDE)
    side_motors = four(motor_x())
    sweep = swept_layers()

    checks = {
        "base vs towers": overlap(base, towers),
        "base vs pedestal": overlap(base, pedestal),
        "pedestal vs towers": overlap(pedestal, towers),
        "top vs towers": overlap(top, towers),
        "frame vs turning cube layers": overlap(base + pedestal + towers + top, sweep),
        "frame vs side motors": overlap(base + pedestal + top, side_motors),
        "towers vs their motors": overlap(short + tall, motor_x()),
        "towers vs each other": overlap(tall, short.rotate([0, 0, 90])),
        "side motors vs each other": overlap(motor_x(), motor_x().rotate([0, 0, 90])),
        "base and pedestal vs bottom motor": overlap(base + pedestal, motor_bottom()),
        "top vs top motor": overlap(top, motor_top()),
        "towers pushed in 5 mm vs turning layers": overlap(towers_in, sweep),
        "towers pushed in 5 mm vs each other": overlap(
            tall.translate([-SLIDE, 0, 0]),
            short.translate([-SLIDE, 0, 0]).rotate([0, 0, 90])),
        "towers pushed in 5 mm vs base, pedestal, top": overlap(towers_in, base + pedestal + top),
        "towers pulled out 5 mm vs base, top": overlap(towers_out, base + top),
    }
    for name, vol in checks.items():
        print(f"{'OK ' if vol < 1.0 else 'HIT'} {name}: {vol:.1f} mm3")

    parts = {"frame_base": (base, False, 1), "frame_pedestal": (pedestal, True, 1),
             "frame_tower": (short, False, 2), "frame_tower_tall": (tall, False, 2),
             "frame_top": (top, False, 1)}
    total = 0.0
    for name, (solid, flip, count) in parts.items():
        mesh = to_trimesh(solid)
        printable = print_oriented(mesh, flip)
        printable.export(OUT / "stl" / f"{name}.stl")
        size = printable.bounds[1] - printable.bounds[0]
        total += count * mesh.volume / 1000
        print(f"{name}: watertight={mesh.is_watertight} "
              f"size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
              f"solid volume={mesh.volume / 1000:.1f} cm3 (x{count})")
        if "--assembly" in sys.argv:
            out = pathlib.Path(sys.argv[sys.argv.index("--assembly") + 1])
            mesh.export(out / f"{name}_assembled.stl")
    print(f"whole frame, solid volume: {total:.1f} cm3")

    if "--preview" in sys.argv:
        write_previews({
            "frame": [base, pedestal, towers, top], "tower": tall,
            "motors": [side_motors, motor_bottom(), motor_top()],
        })


if __name__ == "__main__":
    main()
