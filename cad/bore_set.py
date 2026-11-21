"""Drive adapters with six shaft-hole sizes, for finding the bore fit by trial.

The tip is fixed at TIP_SQ (16.5 mm, found with adapter_set.py). Only the D
hole for the motor shaft changes. On the first trial print (2026-11-20) the
hole drawn at 5.2 mm was too tight: only the shaft's chamfered tip went in.

Run:  python bore_set.py
Writes stl/drive_adapter_bore_set.stl (all six, standing tip up for one print).

Each adapter is engraved with its hole diameter as drawn (5.3 to 5.8 mm). The
flat is moved out by the same amount plus 0.05 mm, as in bench_stand.py. Use
the smallest hole the shaft slides all the way into with the flats lined up,
then set BORE_CLEAR = (diameter - 5) / 2 and FLAT_CLEAR = BORE_CLEAR + 0.05
in bench_stand.py.
"""
from manifold3d import Manifold

from adapter_set import COLUMNS, PITCH, label_cutter
from bench_stand import OUT, SHAFT_D, TIP_SQ, build_adapter, to_trimesh

HOLES = [5.3, 5.4, 5.5, 5.6, 5.7, 5.8]   # hole diameter as drawn, mm


def build_labelled(hole):
    clear = (hole - SHAFT_D) / 2
    return build_adapter(TIP_SQ, clear, clear + 0.05) - label_cutter(f"{hole:g}")


def build_all():
    out = Manifold()
    for i, hole in enumerate(HOLES):
        col, row = i % COLUMNS, i // COLUMNS
        out += build_labelled(hole).translate([col * PITCH, -row * PITCH, 0])
    return out


def main():
    (OUT / "stl").mkdir(exist_ok=True)
    mesh = to_trimesh(build_all())
    mesh.export(OUT / "stl" / "drive_adapter_bore_set.stl")
    size = mesh.bounds[1] - mesh.bounds[0]
    bodies = len(mesh.split(only_watertight=True))
    print(f"drive_adapter_bore_set: {bodies} adapters, watertight={mesh.is_watertight} "
          f"size={size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm "
          f"solid volume={mesh.volume / 1000:.1f} cm3")
    print(f"tip {TIP_SQ:g} mm; hole diameters:", ", ".join(f"{h:g}" for h in HOLES), "mm")


if __name__ == "__main__":
    main()
