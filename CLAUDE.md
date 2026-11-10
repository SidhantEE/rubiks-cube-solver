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
- `cad/frame.py`: six-motor frame (base, tower x4, lift-off top). Imports from
  `bench_stand.py` and runs interference checks every time.
- `cad/stl/`: generated STL files, in print orientation.
- `hardware/README.md`: assembly, wiring, cube preparation, bench test.
- `docs/BOM.md`: the bill of materials. Keep it in step with any parts change.
- `docs/build-plan.html`, `docs/parts-viewer.html`: copies of two published
  Claude artifact pages (research, 3D viewer). They are page fragments without
  a doctype; they open fine in a browser.

## Commands

```
firmware/host_test/run.sh            # compile and run the sketch on this computer

pip install manifold3d trimesh numpy matplotlib
cd cad
python bench_stand.py --no-preview   # skip the slow matplotlib renders
python frame.py                      # prints OK/HIT for each collision check

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
- The host test simulates time and drivers. It cannot show that the sketch
  compiles for the Teensy or that real motors keep up.

## CAD conventions

- Units are millimetres. Z is up.
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
- The adapter tip (`TIP_SQ`, `TIP_DEPTH`, `TIP_SCREW_D`) is a placeholder. The
  recess under the cube's centre cap is not published and must be measured.
- Speed figures (40 to 45 ms per quarter turn at 24 V) are calculations, not
  measurements. No published cube robot uses this exact motor.
- The firmware passes the host test only. It has not been compiled for the
  Teensy or run on hardware. The TMC5160 register values follow the datasheet's
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

1. Compile and flash the firmware on the Teensy; send `STATUS` with one driver.
2. Bench test: one motor, start at `TURN 60`, shorten until steps are lost.
   Holding 40 to 45 ms means the design works as planned.
3. Measure the cube's centre recess and regenerate the adapter.
4. Print and assemble the frame.
5. Camera reading inside the robot. One camera sees only three faces, which is
   not enough by itself; options are turning faces to reveal the hidden
   stickers, mirrors, or a second camera. Camera mounts are not designed.
6. Faster solving: rob-twophase (github.com/efrantar/rob-twophase) counts
   opposite faces turning together as one move, which the firmware already
   supports.
7. A tray for the driver boards and a faster way to load the cube.
