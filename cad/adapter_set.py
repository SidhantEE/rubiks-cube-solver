"""Drive adapters in a range of tip widths, for finding the fit by trial.

The recess under the cube's centre cap has not been measured, so this prints
the real adapter nine times, each with a different tip width and the width
engraved on its side. The one that fits the cube is the one to use; put its
width into TIP_SQ in bench_stand.py so the other five can be printed to match.

Run:  python adapter_set.py
Writes stl/drive_adapter_set.stl (all nine, standing tip up for one print).

Only the tip width changes. Tip depth and the screw clearance still come from
TIP_DEPTH and TIP_SCREW_D in bench_stand.py, which are placeholders.
"""
from manifold3d import Manifold

from bench_stand import OUT, box, build_adapter, to_trimesh

SIZES = [13.5, 13.75, 14.0, 14.25, 14.5, 14.75, 15.0, 15.25, 15.5]
PITCH = 24.0         # spacing between adapters on the bed
COLUMNS = 3
BODY_R = 7.0         # adapter body radius, as in build_adapter()

# Label, engraved on the +X side of the body and read along the shaft axis.
# The set screw is on the +Y side, so the two do not meet.
DIGIT_W, DIGIT_H, STROKE, DIGIT_GAP = 3.0, 5.0, 0.8, 1.0
LABEL_Z = 1.5        # where the label starts, measured from the motor end
ENGRAVE = 0.6        # depth at the edges of the label; deeper in the middle

# seven-segment digits: a top, b top right, c bottom right, d bottom,
# e bottom left, f top left, g middle
SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


def digit_rects(ch):
    """Rectangles (u0, u1, v0, v1) of one digit; u runs along the text, v is up."""
    w, h, s = DIGIT_W, DIGIT_H, STROKE
    mid = (h - s) / 2
    rects = {
        "a": (0, w, h - s, h),
        "d": (0, w, 0, s),
        "g": (0, w, mid, mid + s),
        "f": (0, s, mid, h),
        "b": (w - s, w, mid, h),
        "e": (0, s, 0, mid + s),
        "c": (w - s, w, 0, mid + s),
    }
    return [rects[seg] for seg in SEGMENTS[ch]]


def label_cutter(text):
    """Boxes that engrave the text into the +X side of the body.

    Seen from +X the text runs along +Z with the tops of the digits toward -Y,
    so it reads normally with the adapter lying on its side.
    """
    # the body curves away from a flat label; start the cut below the lowest point
    sag = BODY_R - (BODY_R ** 2 - (DIGIT_H / 2) ** 2) ** 0.5
    x0, x1 = BODY_R - sag - ENGRAVE, BODY_R + 1.0
    out, u = Manifold(), LABEL_Z
    for ch in text:
        if ch == ".":
            rects, advance = [(0, STROKE, 0, STROKE)], STROKE + DIGIT_GAP
        else:
            rects, advance = digit_rects(ch), DIGIT_W + DIGIT_GAP
        for u0, u1, v0, v1 in rects:
            out += box(x0, x1, DIGIT_H / 2 - v1, DIGIT_H / 2 - v0, u + u0, u + u1)
        u += advance
    return out


def build_labelled(size):
    return build_adapter(size) - label_cutter(f"{size:g}")


def build_all():
    out = Manifold()
    for i, size in enumerate(SIZES):
        col, row = i % COLUMNS, i // COLUMNS
        out += build_labelled(size).translate([col * PITCH, -row * PITCH, 0])
    return out


def main():
    (OUT / "stl").mkdir(exist_ok=True)
    mesh = to_trimesh(build_all())
    mesh.export(OUT / "stl" / "drive_adapter_set.stl")
    size = mesh.bounds[1] - mesh.bounds[0]
    bodies = len(mesh.split(only_watertight=True))
    print(f"drive_adapter_set: {bodies} adapters, watertight={mesh.is_watertight} "
          f"size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
          f"solid volume={mesh.volume / 1000:.1f} cm3")
    print("tip widths:", ", ".join(f"{s:g}" for s in SIZES), "mm")


if __name__ == "__main__":
    main()
