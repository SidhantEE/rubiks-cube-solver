"""Whole-robot assembly as a STEP file for Autodesk Inventor.

Rebuilds the frame and adapter from frame.py and bench_stand.py with an exact
solid kernel (see step_kernel.py), adds six motors and the cube, and writes
one assembly:

    step/cube_solver_assembly.step

Run:  pip install cadquery trimesh numpy
      python inventor_export.py

In Inventor: File > Open, pick the .step file. It arrives as an assembly with
one part per printed piece; the motor, adapter and tower are each one part
used several times.

The motor and cube are reference models for checking fit, not for printing.
The cube is drawn with its centre caps off, as it runs in the robot. The
recess under each cap uses the same placeholder size as the adapter tip.
"""
import pathlib

import cadquery as cq

import step_kernel  # noqa: F401  must come before bench_stand and frame
from step_kernel import Manifold

import bench_stand as bs
import frame as fr

OUT = pathlib.Path(__file__).parent / "step"

# Motor details from the 17HE19-2004S drawing that the frame scripts do not need
BOSS_D = 22.0
BOSS_H = 2.0
BODY_CHAMFER = 4.5

# Cube drawing details (appearance only; the 56 mm envelope is what matters)
CUBIE_FILLET = 1.5
TILE = 14.5
TILE_T = 0.6
RECESS_FIT = 0.4       # recess is this much wider than the adapter tip
RECESS_EXTRA = 0.5     # and this much deeper

COLOURS = {
    "U_white": ((0, 0, 1), (0.95, 0.95, 0.95)),
    "D_yellow": ((0, 0, -1), (0.98, 0.84, 0.10)),
    "R_red": ((1, 0, 0), (0.80, 0.10, 0.12)),
    "L_orange": ((-1, 0, 0), (1.00, 0.45, 0.05)),
    "F_green": ((0, -1, 0), (0.05, 0.62, 0.25)),
    "B_blue": ((0, 1, 0), (0.05, 0.25, 0.75)),
}


def colour(rgb, alpha=1.0):
    return cq.Color(rgb[0], rgb[1], rgb[2], alpha)


# --------------------------------------------------------------------- motor
def build_motor():
    """NEMA 17, mounting face on z = 0, shaft along +Z, body below."""
    half = bs.NEMA / 2
    body = (cq.Workplane("XY").box(bs.NEMA, bs.NEMA, bs.MOTOR_LEN, centered=(True, True, False))
            .translate((0, 0, -bs.MOTOR_LEN)).edges("|Z").chamfer(BODY_CHAMFER))
    body = body.union(cq.Workplane("XY").circle(BOSS_D / 2).extrude(BOSS_H))
    # threaded mounting holes, drawn as plain M3 tap-drill holes
    holes = (cq.Workplane("XY").rect(bs.HOLE_PITCH, bs.HOLE_PITCH, forConstruction=True)
             .vertices().circle(1.25).extrude(-4.5))
    body = body.cut(holes)

    shaft = cq.Workplane("XY").circle(bs.SHAFT_D / 2).extrude(bs.SHAFT_LEN)
    flat_y = bs.SHAFT_FLAT - bs.SHAFT_D / 2
    flat = (cq.Workplane("XY").box(10, 10, bs.SHAFT_DCUT + 1, centered=(True, False, False))
            .translate((0, flat_y, bs.SHAFT_LEN - bs.SHAFT_DCUT)))
    shaft = shaft.cut(flat)
    assert half > BOSS_D / 2
    return body.union(shaft).val()


# ---------------------------------------------------------------------- cube
def face_frame(normal):
    """Location that carries a part drawn on +Z onto the face with this normal."""
    nx, ny, nz = normal
    if nz == 1:
        return cq.Location(cq.Vector(0, 0, 0))
    if nz == -1:
        return cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), 180)
    # rotate +Z onto the horizontal normal: axis = z cross n
    return cq.Location(cq.Vector(0, 0, 0), cq.Vector(-ny, nx, 0), 90)


def build_cube():
    """Cube centred on the origin. Returns the body and one tile set per face."""
    pitch = bs.CUBE / 3
    half = bs.CUBE / 2

    cubie = cq.Workplane("XY").box(pitch, pitch, pitch).edges().fillet(CUBIE_FILLET).val()
    body = cq.Workplane("XY").box(pitch, pitch, pitch).val()          # hidden core
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for k in (-1, 0, 1):
                if (i, j, k) != (0, 0, 0):
                    body = body.fuse(cubie.translate(cq.Vector(i * pitch, j * pitch, k * pitch)))

    # drawn on the +Z face, then carried to each face
    tile = (cq.Workplane("XY").rect(TILE, TILE).extrude(TILE_T).edges("|Z").fillet(2.0)
            .translate((0, 0, half - TILE_T)).val())
    nine = [tile.translate(cq.Vector(a * pitch, b * pitch, 0)) for a in (-1, 0, 1) for b in (-1, 0, 1)]
    tiles_z = cq.Compound.makeCompound(nine)
    side = bs.TIP_SQ + RECESS_FIT
    depth = bs.TIP_DEPTH + RECESS_EXTRA
    recess_z = (cq.Workplane("XY").rect(side, side).extrude(depth + 1)
                .translate((0, 0, half - depth)).val())

    tile_sets = {}
    for name, (normal, _) in COLOURS.items():
        loc = face_frame(normal)
        tiles = tiles_z.moved(loc)
        recess = recess_z.moved(loc)
        body = body.cut(tiles).cut(recess)
        tile_sets[name] = tiles.cut(recess)
    return body, tile_sets


# ------------------------------------------------------------------ assembly
def drive_locations():
    """Where each motor's mounting face goes; the shaft points at the cube."""
    side = cq.Location(cq.Vector(fr.R_FACE, 0, fr.ZC), cq.Vector(0, 1, 0), -90)
    locs = {}
    for k, face in enumerate(("R", "B", "L", "F")):
        locs[face] = cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90 * k) * side
    locs["D"] = cq.Location(cq.Vector(0, 0, fr.DECK_Z0))
    locs["U"] = cq.Location(cq.Vector(0, 0, fr.TOP_Z1), cq.Vector(1, 0, 0), 180)
    return locs


def main():
    OUT.mkdir(exist_ok=True)
    base = fr.build_base().solid()
    tower = fr.build_tower().solid()
    top = fr.build_top().solid()
    adapter = bs.build_adapter().solid()
    motor = build_motor()
    cube_body, tile_sets = build_cube()

    for name, shape in (("frame_base", base), ("frame_tower", tower), ("frame_top", top),
                        ("drive_adapter", adapter), ("motor", motor), ("cube_body", cube_body)):
        print(f"{name}: solids={len(shape.Solids())} valid={shape.isValid()} "
              f"volume={shape.Volume() / 1000:.1f} cm3")

    # adapter sits 1.5 mm clear of the plate's cube-side face, on the shaft
    on_shaft = cq.Location(cq.Vector(0, 0, bs.PLATE_T + 1.5))
    centre = cq.Location(cq.Vector(0, 0, fr.ZC))
    drives = drive_locations()

    # ------------------------------------------------------- interference
    def placed(shape, loc):
        return Manifold(shape.moved(loc))

    frame_all = Manifold(base) + Manifold(top)
    for k in range(4):
        frame_all += Manifold(tower).rotate([0, 0, 90 * k])
    cube_all = placed(cube_body, centre)
    motors_all, adapters_all = Manifold(), Manifold()
    for loc in drives.values():
        motors_all += placed(motor, loc)
        adapters_all += placed(adapter, loc * on_shaft)
    checks = {
        "frame vs motors": fr.overlap(frame_all, motors_all),
        "frame vs adapters": fr.overlap(frame_all, adapters_all),
        "frame vs cube": fr.overlap(frame_all, cube_all),
        "frame vs turning cube layers": fr.overlap(frame_all, fr.swept_layers()),
        "adapters vs cube": fr.overlap(adapters_all, cube_all),
        "adapters vs motors": fr.overlap(adapters_all, motors_all),
        "motors vs cube": fr.overlap(motors_all, cube_all),
    }
    for name, vol in checks.items():
        print(f"{'OK ' if vol < 1.0 else 'HIT'} {name}: {vol:.1f} mm3")

    # ----------------------------------------------------------- assembly
    # frame in orange, adapters in light grey, motors dark
    blue, orange, grey = (0.94, 0.42, 0.10), (0.75, 0.76, 0.78), (0.25, 0.26, 0.29)
    # Inventor treats Y as up; the scripts use Z. Stand the robot upright in
    # the file: script (x, y, z) becomes Inventor (x, z, -y).
    up = cq.Location(cq.Vector(0, 0, 0), cq.Vector(1, 0, 0), -90)
    assy = cq.Assembly(name="cube_solver")
    assy.add(base, name="frame_base", color=colour(blue), loc=up)
    for k, face in enumerate(("R", "B", "L", "F")):
        assy.add(tower, name=f"frame_tower_{face}", color=colour(blue),
                 loc=up * cq.Location(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90 * k))
    assy.add(top, name="frame_top", color=colour(blue), loc=up)
    for face, loc in drives.items():
        assy.add(motor, name=f"motor_{face}", color=colour(grey), loc=up * loc)
        assy.add(adapter, name=f"drive_adapter_{face}", color=colour(orange),
                 loc=up * loc * on_shaft)

    cube = cq.Assembly(name="cube")
    cube.add(cube_body, name="cube_body", color=colour((0.06, 0.06, 0.07)))
    for name, (_, rgb) in COLOURS.items():
        cube.add(tile_sets[name], name=f"tiles_{name}", color=colour(rgb))
    assy.add(cube, name="cube_YuLong_V2M", loc=up * centre)

    path = OUT / "cube_solver_assembly.step"
    assy.save(str(path))
    print(f"wrote {path}  ({path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
