# Rubik's cube solver

A six-motor robot that solves a 3x3 cube, aiming for about 1 to 1.5 seconds.

## Parts chosen

| Part | Choice |
|---|---|
| Motors | 6 × StepperOnline 17HE19-2004S (NEMA 17, 0.55 Nm, 2 A, 2.4 mH) |
| Drivers | TMC5160 SilentStepStick, one per motor |
| Controller | Teensy 4.1 |
| Cube | YJ YuLong V2 M, 56 mm |
| Supply | 24 V |
| Solver (planned) | [rob-twophase](https://github.com/efrantar/rob-twophase) |

`docs/build-plan.html` has the research behind these choices, the feasibility
calculation and the bill of materials. Open it in a browser.

## Printed parts

Everything in `cad/` is generated from Python, so each dimension is a named
number that can be changed and regenerated.

```
pip install manifold3d trimesh numpy matplotlib
cd cad
python bench_stand.py --no-preview   # one-motor test stand and shaft adapter
python frame.py                      # six-motor frame, with collision checks
```

STL files are written to `cad/stl`:

| File | What it is | Print |
|---|---|---|
| `bench_stand.stl` | Holds one motor and the cube for the first test | 1 |
| `frame_base.stl` | Deck on four legs; bottom motor hangs underneath | 1 |
| `frame_tower.stl` | Side motor tower with cradle | 4 |
| `frame_top.stl` | Lift-off plate for the top motor | 1 |
| `drive_adapter_PLACEHOLDER_15mm_tip.stl` | Sleeve from motor shaft to cube centre | 6 |

`docs/parts-viewer.html` shows the parts in 3D.

## Status

- Parts are ordered. Nothing has been printed or tested yet.
- Motor and cube dimensions come from the motor datasheet and the cube's
  product listing, not from measuring the real parts.
- The adapter tip is a placeholder. Measure the square recess under the cube's
  centre cap before printing it, then set `TIP_SQ`, `TIP_DEPTH` and
  `TIP_SCREW_D` in `cad/bench_stand.py`.
- The speed figures in the build plan are calculations. The first real test is
  one motor on the bench stand: start at 60 ms per quarter turn and shorten it
  until steps are lost. Holding 40 to 45 ms means the design works as planned.
- Not started: solver integration, Teensy firmware, camera mounts.
