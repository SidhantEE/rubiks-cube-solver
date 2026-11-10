"""One-axis bench test stand for the cube solver.

Holds one NEMA 17 motor and a 3x3 speed cube so the motor can turn a single
face while the other two layers are held still.

Run:  pip install manifold3d trimesh numpy matplotlib
      python bench_stand.py
Writes STL files to ./stl and preview images to ./preview.

All dimensions in millimetres. X runs along the motor shaft, Z is up.
The motor plate's cube-side face is x = 0. The motor body sits at x < 0.
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import CrossSection, JoinType, Manifold

# ---------------------------------------------------------------- parameters
CUBE = 56.0          # YJ YuLong V2 M, from TheCubicle listing (56.0 mm)
FIT = 0.6            # total clearance between cube and cradle walls
AXIS_H = 48.0        # shaft axis height above the bench
BASE_T = 5.0         # base plate thickness
BASE_W = 90.0        # base plate width
PLATE_T = 6.0        # motor plate thickness
PLATE_W = 56.0       # motor plate width
GAP = 26.0           # motor plate face to cube face
WALL = 6.0           # cradle side wall thickness
BACK_T = 6.0         # cradle back wall thickness
NEMA = 42.3          # NEMA 17 body width
HOLE_PITCH = 31.0    # NEMA 17 mounting hole spacing
PILOT_D = 22.6       # clearance for the motor's 22 mm boss
M3_CLEAR = 3.4       # M3 clearance hole
MOTOR_LEN = 48.0     # motor body length (17HE19-2004S)
SHAFT_D = 5.0        # motor shaft diameter
SHAFT_FLAT = 4.5     # distance from flat to the opposite side of the shaft
SHAFT_LEN = 24.0     # shaft length from motor face
SHAFT_DCUT = 15.0    # length of the flat, measured from the shaft tip

# Drive adapter tip. PLACEHOLDER VALUES: measure the square recess under the
# cube's centre cap with calipers before printing the adapter.
TIP_SQ = 15.0        # width of the square recess
TIP_DEPTH = 4.0      # how far the tip reaches into the recess
TIP_SCREW_D = 7.5    # clearance for the tension screw head in the recess

SEG = 96
OUT = pathlib.Path(__file__).parent


# ------------------------------------------------------------------- helpers
def extrude(cs, h):
    return Manifold.extrude(cs, h) if hasattr(Manifold, "extrude") else cs.extrude(h)


def rounded_rect(w, h, r):
    return CrossSection.square([w - 2 * r, h - 2 * r], center=True).offset(
        r, JoinType.Round, 2.0, SEG
    )


def polygon(points):
    pts = np.asarray(points, dtype=float)
    x, y = pts[:, 0], pts[:, 1]
    if np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) < 0:
        pts = pts[::-1]
    return CrossSection([pts.tolist()])


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return Manifold.cylinder(x1 - x0, r, r, SEG).rotate([0, 90, 0]).translate([x0, y, z])


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    return Manifold.cylinder(y1 - y0, r, r, SEG).rotate([-90, 0, 0]).translate([x, y0, z])


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return Manifold.cylinder(z1 - z0, r, r, SEG).translate([x, y, z0])


def slab_yz(width_y, height_z, r, x0, x1):
    """Rounded rectangle in the YZ plane, standing on z = 0, spanning x0..x1."""
    cs = rounded_rect(height_z, width_y, r)  # u = -z, v = y before rotation
    return extrude(cs, x1 - x0).rotate([0, 90, 0]).translate([x0, 0, height_z / 2])


def gusset(points_xz, y0, y1):
    """Triangular rib: polygon in the XZ plane, spanning y0..y1."""
    return extrude(polygon(points_xz), y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


# --------------------------------------------------------------------- stand
def build_stand():
    pocket = CUBE + FIT
    cradle_w = pocket + 2 * WALL
    floor_z = AXIS_H - CUBE / 2
    wall_top = AXIS_H + CUBE / 2 - 6.0
    cradle_x0 = GAP + CUBE / 3 + 2.0          # leaves the turning layer free
    pocket_x1 = GAP + CUBE + 0.4
    cradle_x1 = pocket_x1 + BACK_T
    base_x0 = -(PLATE_T + MOTOR_LEN + 8.0)
    base_x1 = cradle_x1 + 8.0

    # base plate
    base_len = base_x1 - base_x0
    base = extrude(rounded_rect(base_len, BASE_W, 10.0), BASE_T).translate(
        [base_x0 + base_len / 2, 0, 0]
    )

    # motor plate with ribs on both sides
    plate_h = AXIS_H + NEMA / 2 + 5.0
    plate = slab_yz(PLATE_W, plate_h, 8.0, -PLATE_T, 0.0)
    ribs = Manifold()
    for sign in (1, -1):
        ya, yb = sorted((sign * (PLATE_W / 2 - 4.0), sign * PLATE_W / 2))
        ribs += gusset([(0, BASE_T), (22, BASE_T), (0, BASE_T + 38)], ya, yb)
        ribs += gusset(
            [(-PLATE_T, BASE_T), (-PLATE_T - 22, BASE_T), (-PLATE_T, BASE_T + 38)], ya, yb
        )

    # cradle: U channel that holds the two layers that must not turn
    cradle = slab_yz(cradle_w, wall_top, 5.0, cradle_x0, cradle_x1)
    cradle -= box(cradle_x0 - 1, pocket_x1, -pocket / 2, pocket / 2, floor_z, wall_top + 1)
    # finger notches in the side walls, and a window in the back wall
    notch_x = (cradle_x0 + pocket_x1) / 2
    cradle -= cyl_y(13.0, -cradle_w, cradle_w, x=notch_x, z=wall_top + 2.0)
    cradle -= cyl_x(15.0, pocket_x1 - 1, cradle_x1 + 1, z=AXIS_H)

    # two rails under the motor body so it rests on the stand
    rails = Manifold()
    rail_top = AXIS_H - NEMA / 2 - 0.3
    for sign in (1, -1):
        ya, yb = sorted((sign * 10.0, sign * 18.0))
        rails += box(-PLATE_T - MOTOR_LEN, -PLATE_T + 0.5, ya, yb, BASE_T - 0.5, rail_top)

    stand = base + plate + ribs + cradle + rails

    # motor mounting holes
    stand -= cyl_x(PILOT_D / 2, -PLATE_T - 1, 1, z=AXIS_H)
    for sy in (1, -1):
        for sz in (1, -1):
            stand -= cyl_x(
                M3_CLEAR / 2, -PLATE_T - 1, 1,
                y=sy * HOLE_PITCH / 2, z=AXIS_H + sz * HOLE_PITCH / 2,
            )

    # bench mounting holes at the four corners
    for hx in (base_x0 + 9.0, base_x1 - 9.0):
        for sy in (1, -1):
            stand -= cyl_z(2.25, -1, BASE_T + 1, x=hx, y=sy * (BASE_W / 2 - 6.0))

    return stand


# ------------------------------------------------------------- drive adapter
def build_adapter(tip_sq=TIP_SQ):
    """Printed sleeve from the motor's D shaft to the cube's centre recess.

    Modelled standing on its motor end (z = 0), tip pointing up, which is also
    the print orientation.
    """
    body_len = GAP - 1.5            # 1.5 mm clear of the motor plate
    body_r, flange_r = 7.0, 9.0
    flange_t, cone_h = 3.0, 2.0

    body = cyl_z(body_r, 0, body_len)
    cone = Manifold.cylinder(cone_h, body_r, flange_r, SEG).translate(
        [0, 0, body_len - flange_t - cone_h]
    )
    flange = cyl_z(flange_r, body_len - flange_t, body_len)
    tip = extrude(rounded_rect(tip_sq, tip_sq, 1.0), TIP_DEPTH).translate([0, 0, body_len])
    adapter = body + cone + flange + tip

    # D bore for the shaft
    bore_r = SHAFT_D / 2 + 0.1
    flat_y = SHAFT_FLAT - SHAFT_D / 2 + 0.15
    bore_depth = SHAFT_LEN - PLATE_T - 1.5 + 1.0
    bore = cyl_z(bore_r, -1, bore_depth) ^ box(-5, 5, -5, flat_y, -2, bore_depth + 1)
    adapter -= bore
    # the shaft is fully round near the motor, so open the bore there
    round_len = (SHAFT_LEN - SHAFT_DCUT) - PLATE_T - 1.5 + 1.0
    if round_len > 0:
        adapter -= cyl_z(bore_r, -1, round_len)
    # M3 set screw onto the shaft flat (screw self-taps into the print)
    adapter -= cyl_y(1.45, 0, body_r + 1, z=7.0)
    # clearance for the cube's tension screw
    adapter -= cyl_z(TIP_SCREW_D / 2, body_len - 2.0, body_len + TIP_DEPTH + 1)
    return adapter


# ---------------------------------------------------------------- output
def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(
        vertices=np.asarray(mesh.vert_properties)[:, :3],
        faces=np.asarray(mesh.tri_verts),
        process=True,
    )


def ghost_parts():
    """Motor and cube, for the preview only."""
    motor = box(-PLATE_T - MOTOR_LEN, -PLATE_T, -NEMA / 2, NEMA / 2,
                AXIS_H - NEMA / 2, AXIS_H + NEMA / 2)
    motor += cyl_x(SHAFT_D / 2, -PLATE_T, SHAFT_LEN - PLATE_T, z=AXIS_H)
    cube = box(GAP, GAP + CUBE, -CUBE / 2, CUBE / 2, AXIS_H - CUBE / 2, AXIS_H + CUBE / 2)
    return motor, cube


def render(parts, path, elev, azim):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(9, 6.5), dpi=130)
    ax = fig.add_subplot(111, projection="3d")
    light = np.array([0.35, -0.5, 0.8])
    light /= np.linalg.norm(light)
    allv = []
    for mesh, colour, alpha in parts:
        shade = 0.45 + 0.55 * np.clip(mesh.face_normals @ light, 0, 1)
        rgba = np.concatenate(
            [np.outer(shade, np.array(colour)), np.full((len(shade), 1), alpha)], axis=1
        )
        ax.add_collection3d(Poly3DCollection(mesh.triangles, facecolors=rgba, linewidths=0))
        allv.append(mesh.vertices)
    v = np.vstack(allv)
    mid, span = (v.max(0) + v.min(0)) / 2, (v.max(0) - v.min(0)).max() / 2
    ax.set_xlim(mid[0] - span, mid[0] + span)
    ax.set_ylim(mid[1] - span, mid[1] + span)
    ax.set_zlim(mid[2] - span, mid[2] + span)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(path)
    plt.close(fig)


def main():
    (OUT / "stl").mkdir(exist_ok=True)
    (OUT / "preview").mkdir(exist_ok=True)

    stand = to_trimesh(build_stand())
    adapter = to_trimesh(build_adapter())
    stand.export(OUT / "stl" / "bench_stand.stl")
    adapter.export(OUT / "stl" / f"drive_adapter_PLACEHOLDER_{TIP_SQ:g}mm_tip.stl")

    for name, mesh in (("bench_stand", stand), ("drive_adapter", adapter)):
        size = mesh.bounds[1] - mesh.bounds[0]
        print(f"{name}: watertight={mesh.is_watertight} "
              f"size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
              f"solid volume={mesh.volume / 1000:.1f} cm3")

    import sys
    if "--no-preview" in sys.argv:
        return
    motor, cube = (to_trimesh(p) for p in ghost_parts())
    # adapter placed on the shaft for the assembly view
    placed = adapter.copy()
    placed.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
    placed.apply_translation([1.5, 0, AXIS_H])
    blue, grey, orange, steel = (0.16, 0.42, 0.85), (0.35, 0.36, 0.40), (0.95, 0.55, 0.15), (0.75, 0.77, 0.80)
    render([(stand, blue, 1.0)], OUT / "preview" / "stand.png", 24, -58)
    render([(stand, blue, 1.0), (motor, grey, 1.0), (cube, orange, 0.55), (placed, steel, 1.0)],
           OUT / "preview" / "assembly.png", 24, -58)
    render([(stand, blue, 1.0), (motor, grey, 1.0), (cube, orange, 0.55), (placed, steel, 1.0)],
           OUT / "preview" / "assembly_side.png", 8, -90)


if __name__ == "__main__":
    main()
