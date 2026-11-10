# Rubik's cube solver

A six-motor robot that solves a 3x3 cube. Target: about 1 to 1.5 s per solve
("Tier 1" in `docs/build-plan.html`). Inspired by the Purdue 0.103 s record
robot, built with hobby parts.

## Hardware decisions (made, do not re-research unless asked)

- Motors: 6 x StepperOnline 17HE19-2004S. NEMA 17, 0.55 Nm, 2.0 A, 1.30 ohm,
  2.40 mH, rotor inertia 62 g·cm², 0.27 kg.
- Drivers: TMC5160 SilentStepStick, one per motor (7 bought, 1 spare).
  3 A max, 10 to 35 V, configured over SPI (no standalone mode).
- Controller: Teensy 4.1 with headers. 3.3 V logic, not 5 V tolerant.
- Cube: YJ YuLong V2 M, 56.0 mm, 88.9 g, magnetic. Run it tight and lubricated.
- Supply: 24 V, provided by the user. No driver fan (user's choice).
- Solver: plan is rob-twophase (github.com/efrantar/rob-twophase).
- Vision: start with manual entry or one webcam; see "Open work".

## Two plans in one repository

The repository began as a scaffold for the t33devv/rubik build: pancake
NEMA 17 motors, A4988 drivers, Arduino Mega, 12 V, a non-magnetic GAN RS cube
and the t33devv frame. The hardware that was ordered is the list above.

- `software/scanner.py`, `software/solver.py`: hardware-independent. Still valid.
- `firmware/cube_solver/cube_solver.ino`: written for the Mega and A4988. Must
  be ported to Teensy 4.1 and TMC5160 (SPI configuration, 3.3 V logic).
- `docs/BOM.md`, `docs/bom.html`, `hardware/README.md`: describe the earlier
  plan. Do not follow their wiring (12 V, 5 V logic) or cube advice for the
  ordered parts. They have not been rewritten; ask before deleting them.

## Repository layout

- `cad/bench_stand.py`: one-motor bench test stand and the shaft adapter.
  Also holds the shared parameters and helper functions.
- `cad/frame.py`: six-motor frame (base, tower x4, lift-off top). Imports from
  `bench_stand.py` and runs interference checks every time.
- `cad/stl/`: generated STL files, in print orientation.
- `docs/build-plan.html`, `docs/parts-viewer.html`: copies of two published
  Claude artifact pages (research, BOM, 3D viewer). They are page fragments
  without a doctype; they open fine in a browser.

## Commands

```
pip install manifold3d trimesh numpy matplotlib
cd cad
python bench_stand.py --no-preview   # skip the slow matplotlib renders
python frame.py                      # prints OK/HIT for each collision check
```

After any geometry change, run `frame.py` and confirm every check prints `OK`.

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
- Nothing has been printed or run yet.

## Wiring notes

- The motor cable's 4-pin plug is wired B-, A-, B+, A+. The driver needs each
  coil's two wires adjacent, so two pins must be moved before plugging in.
- Signal wiring can use Dupont jumpers. Motor power and motor coils need
  22 AWG or heavier; do not route motor current through a breadboard.
- 100 µF 50 V capacitor across the supply at each driver.
- Never unplug a motor while its driver is powered.

## Open work, in order

1. Build rob-twophase and get from a scramble to a move list.
2. Teensy firmware: TMC5160 SPI setup and a step generator with acceleration.
3. Bench test: one motor, start at 60 ms per quarter turn, shorten until steps
   are lost. Holding 40 to 45 ms means the design works as planned.
4. Measure the cube's centre recess and regenerate the adapter.
5. Camera reading. One camera sees only three faces, which is not enough by
   itself; options are turning faces to reveal the hidden stickers, mirrors, or
   a second camera. Camera mounts are not designed.
6. A tray for the driver boards and a faster way to load the cube.
