# Rubik's cube solver

A six-motor robot that solves a 3x3 cube. Target: about 1 to 1.5 s per solve
("Tier 1" in `docs/build-plan.html`). Inspired by the Purdue 0.103 s record
robot, built with hobby parts.

## Hardware decisions (made, do not re-research unless asked)

- Motors: 6 x StepperOnline 17HE19-2004S. NEMA 17, 0.55 Nm, 2.0 A, 1.30 ohm,
  2.40 mH, rotor inertia 62 g·cm², 0.27 kg.
- Drivers: TMC5160 SilentStepStick, one per motor (7 bought, 1 spare).
  3 A max, 10 to 35 V, 0.075 ohm sense resistors, configured over SPI (no
  standalone mode).
- Controller: Teensy 4.1 with headers. 3.3 V logic, not 5 V tolerant.
- Cube: YJ YuLong V2 M, 56.0 mm, 88.9 g, magnetic. Run it tight and lubricated.
- Supply: 24 V, provided by the user. No driver fan (user's choice).
- Vision: `software/scanner.py` scans by hand at one webcam for now.

The repository began as a scaffold for a different build (t33devv/rubik:
pancake motors, A4988, Arduino Mega, 12 V, GAN RS cube). That plan was
replaced on 2026-11-10; nothing from it should be reintroduced.

## Repository layout

- `software/scanner.py`, `software/solver.py`: scan by webcam, solve with
  Kociemba two-phase, send the move string over serial.
- `firmware/cube_solver/cube_solver.ino`: Teensy 4.1 sketch. Writes the
  TMC5160 registers directly over SPI (no library), plans each move as an
  accelerate-then-brake profile, and runs opposite faces together.
- `firmware/host_test/`: stand-in Arduino and SPI headers plus `test_main.cpp`,
  which includes the real sketch and runs it against simulated drivers.
- `cad/bench_stand.py`: one-motor bench test stand and the shaft adapter.
  Also holds the shared parameters and helper functions.
- `cad/frame.py`: six-motor frame, redesigned on 2026-11-11 at the user's
  request to follow the Flatland and Rose record robot
  (github.com/jayflatland/HighFrequencyTwister, GPL-3.0; its frame is
  `CAD Drawings/Phase 4 Center Drive Redux/Five Motor Frame.stl` and
  `Sixth Motor Frame.stl`). Only the layout is followed; do not copy their
  files in. The user's rules for the frame: every motor held very securely
  with walls around it and visible screw fixings, sturdy before light (saving
  filament is welcome but not the priority), and something must detach so
  the cube can be loaded again and again. The user rejected open X-braced
  "cage" supports, a GAN-Robot-style tray with slim pillars, and a five-motor
  layout. Parts: flat base, pedestal around the bottom motor, two short and
  two tall box-column towers with a four-walled motor cradle on top, and a
  bridge with a collar for the top motor. `build_base_half()` (added
  2026-11-14) is an alternative base in two identical halves, 146 mm square,
  for a 180 mm bed such as the Bambu Lab A1 mini: Z-shaped seam, four M3 x 10
  bolts through upright ears, written as `frame_base_half.stl`. It has its
  own checks in `frame.py` and is not in the STEP assembly. `--preview` writes
  `cad/preview/frame_*.png`. Imports from `bench_stand.py` and runs
  interference checks every time. The README renders,
  `docs/parts-viewer.html` and option A in the enclosure page still show the
  frame from before that change.
- `cad/adapter_set.py`: the adapter nine times, tip widths 15.75 to 17.75 mm,
  each engraved with its width, for finding `TIP_SQ` by trial fit.
- `cad/inventor_export.py`: the whole robot (frame, six motors, adapters, cube)
  as one STEP assembly for Autodesk Inventor, in `cad/step/`. It reuses the
  geometry in `frame.py` and `bench_stand.py` through `cad/step_kernel.py`,
  which stands in for manifold3d with CadQuery's exact solid kernel. The motor
  and cube in it are reference models. Change geometry in the Python scripts,
  not in Inventor, then export again.
- `cad/stl/`: generated STL files, in print orientation.
- `hardware/README.md`: assembly, wiring, cube preparation, bench test.
- `docs/BOM.md`: the bill of materials. Keep it in step with any parts change.
- Copies of artifact pages published on 2026-11-14 (3D viewers; the meshes
  are embedded, so regenerate the page if the geometry changes):
  - `docs/adapter-fit.html`: the cube's centre recess (as estimated from
    photos) and the adapter. Its sizes are typed into the page by hand.
    https://claude.ai/artifact/G8ieZWQqmBhFJi6Yzjfutd
  - `docs/adapter-set.html`: the nine trial adapters.
    https://claude.ai/artifact/UK5CkWZ6wSTRduwjkcntTN
  - `docs/split-base.html`: the two-piece base.
    https://claude.ai/artifact/CJRJqvExEwrSMN7eybyUna
  - `docs/cable-routes.html`: the six motors in the frame with suggested
    cable routes (the routes and the motor plug are not modelled in `cad/`).
    https://claude.ai/artifact/6unfMbRZGT6rQG7a3Qrbrh
- `docs/build-plan.html`, `docs/parts-viewer.html`, `docs/enclosure-options.html`:
  copies of published Claude artifact pages (research, 3D viewer, ten frame
  concepts A to J ranked by printed plastic). They are page fragments without
  a doctype; they open fine in a browser. In the enclosure page only option A
  (the current frame) is modeled and checked; B to J are concept models. The
  user requires that no motor "floats": every side motor must have a support
  under its body that runs to the base, not only its four face screws.

## Commands

```
firmware/host_test/run.sh            # compile and run the sketch on this computer

pip install manifold3d trimesh numpy matplotlib
cd cad
python bench_stand.py --no-preview   # skip the slow matplotlib renders
python frame.py                      # prints OK/HIT for each collision check
pip install cadquery
python inventor_export.py            # writes step/cube_solver_assembly.step

python3 software/solver.py --demo    # needs software/requirements.txt installed
```

After a firmware change, run the host test and confirm "all checks passed".
After a geometry change, run `frame.py` and confirm every check prints `OK`.

## Firmware conventions

- Serial protocol: a line of moves replies `DONE <ms>`; also `PING`, `ON`,
  `OFF`, `TURN <ms>`, `SETTLE <ms>`, `CURRENT <mA>`, `STATUS`. `solver.py`
  depends on `PING`/`PONG`, `OK`, `DONE` and `ERR`.
- 8 microsteps, so a quarter turn is 400 steps. `TURN` sets the quarter-turn
  time; acceleration is derived from it. It starts at 60 ms on purpose.
- Pins: STEP/DIR/CS are U 2/3/4, R 5/6/7, F 8/9/10, D 14/15/16, L 17/18/19,
  B 20/21/22. SPI on 11/12/13. Shared enable on 23, active low.
- No Arduino `String` and no forward-declared functions, so the host test can
  include the `.ino` file as plain C++. Keep it that way.
- Keep `struct Axis` above the first function in the sketch. The Arduino build
  inserts function prototypes there, and they fail without the type.
- The host test simulates time and drivers. It cannot show that the sketch
  compiles for the Teensy or that real motors keep up.

## CAD conventions

- Units are millimetres. Z is up. The STEP assembly alone is turned so Y is up,
  because Inventor treats Y as up: script (x, y, z) is Inventor (x, z, -y).
- Bench stand: X runs along the motor shaft; the plate's cube-side face is x = 0.
- Frame: cube centre is on the Z axis at `ZC` = 115.
- Every motor mounting face is 32 mm from its cube face (`GAP` 26 + `PLATE_T` 6),
  so one adapter fits all six positions and the bench stand. Keep this.
- A turning face layer sweeps a 39.6 mm radius. Nothing may enter that volume.
- Parts must print without supports on a 250 x 210 x 210 mm bed (UTA FabLab
  Prusa i3 MK3; STL required, PLA, self-service).

## What is verified and what is not

- Motor dimensions come from the 17HE19-2004S datasheet drawing. Cube size
  comes from the seller's listing. Nothing has been measured with calipers.
- The adapter tip (`TIP_SQ`, `TIP_CORNER_R`, `TIP_DEPTH`, `TIP_SCREW_D`) is an
  estimate from the user's photos of the open centre (2026-11-14), scaled
  against the 56 mm cube width, good to about ± 1 mm: recess about 17 mm wide
  and 8 mm deep, corners about 2.5 mm radius (tip corners are 4 mm), and a boss about 9.5 mm across
  around the tension screw with its top about 2 mm below the rim (the
  hole in the tip is 11.5 mm so it clears the boss with margin). It still
  needs calipers or a trial fit with the adapter set.
- Speed figures (40 to 45 ms per quarter turn at 24 V) are calculations, not
  measurements. No published cube robot uses this exact motor.
- The firmware passes the host test and compiles for the Teensy 4.1
  (`arduino-cli compile --fqbn teensy:avr:teensy41 firmware/cube_solver`,
  Teensy core 1.62.0). On 2026-11-11 it was flashed to the Teensy (serial
  port COM3) with no drivers attached: `PING`, `STATUS`, the range checks and
  the no-driver refusal all replied correctly. No driver or motor has run. The TMC5160 register values follow the datasheet's
  example configuration and are untested on a real driver.
- Nothing has been printed, wired or run yet.

## Wiring notes

- The motor cable's 4-pin plug is wired red, blue, green, black (B-, A-, B+,
  A+). The driver needs each coil's two wires adjacent, so swap blue and green.
- Signal wiring can use Dupont jumpers. Motor power and motor coils need
  22 AWG or heavier; do not route motor current through a breadboard.
- 100 µF 50 V capacitor across the supply at each driver. Tie each driver's
  CLK pin to GND.
- Never unplug a motor while its driver is powered.

## Open work, in order

Roadmap as of 2026-11-14. Each step depends on the one before unless noted.

1. Choose and buy the printer. Bambu Lab A1 mini (180 mm bed) needs the
   two-piece base (`frame_base_half.stl` x2); the A1 or anything with a bed
   of 210 mm or more prints the one-piece `frame_base.stl`. The user was
   leaning toward the A1 mini or A1 mini Combo; not decided.
2. Print `drive_adapter_set.stl` and find the tip that fits the cube's centre
   recess. Put its width into `TIP_SQ`, regenerate, and re-export the STEP
   file. Also check the small notch on one wall of the recess (photo 3): if
   it sticks inward, the tip needs a relief cut.
3. Wire one TMC5160 driver to the Teensy and send `STATUS`. The firmware is
   already flashed; no driver has been attached yet. Can be done while
   waiting for the printer.
4. Print the bench stand and one adapter in the chosen size. Test spin: one
   motor with no cube, start at `TURN 60`, shorten until steps are lost.
5. Same test with the cube on the adapter, turning one face. Holding 40 to
   45 ms per quarter turn means the design works as planned.
6. Print five more adapters and the frame (base or two base halves,
   pedestal, two short towers, two tall towers, bridge) and assemble it.
7. Wire all six drivers and motors and route the cables
   (`docs/cable-routes.html` is a suggestion). Design a tray for the driver
   boards and some cable clips; neither exists yet.
8. First full solve, still scanning the cube by hand with `scanner.py`.
9. Scan the cube inside the robot. Plan: two fixed webcams at opposite
   corners, plus quarter turns to reveal stickers the frame hides (the
   bridge and top motor block part of the top face). 3D-capture apps are not
   needed. First job: use the CAD model to check which stickers each camera
   position can see. Camera mounts are not designed.
10. Faster solving: rob-twophase (github.com/efrantar/rob-twophase) counts
    opposite faces turning together as one move, which the firmware already
    supports.
11. A faster way to load the cube.
