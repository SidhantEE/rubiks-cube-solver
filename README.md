# Rubik's Cube Solver Robot

A six-motor robot that solves a 3x3 Rubik's cube. Each face's center piece is
coupled directly to a NEMA 17 stepper motor, so any face can be turned without
regripping the cube.

```
 webcam ──► software/ (Python)  ──USB serial──►  firmware/ (Arduino Mega)  ──► 6 × stepper drivers ──► 6 × NEMA 17
            scan colors                           parse moves
            solve (Kociemba)                      step motors
```

## How it works

1. **Scan.** Hold each face up to the webcam. `scanner.py` samples the 9
   stickers and classifies their colors.
2. **Solve.** `solver.py` builds the 54-character facelet string and runs
   Kociemba's two-phase algorithm, which usually finds a solution in about 20 moves.
3. **Execute.** The move string (e.g. `R U' F2 D ...`) is sent over serial to
   the Arduino, which turns the matching motor 90° or 180°.

## Repo layout

| Path | What's in it |
|---|---|
| `firmware/cube_solver/` | Arduino sketch: serial protocol and stepper control |
| `software/` | Python: color scanner, solver, serial sender |
| `hardware/` | Printed parts list, wiring, assembly notes |
| `docs/BOM.md` | Bill of materials with prices |

## Quick start

```bash
cd software
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Test the solver with no hardware attached:
python solver.py --demo

# Full run: scan with the webcam, solve, and send moves to the robot
python solver.py --port COM3
```

Flash `firmware/cube_solver/cube_solver.ino` to an Arduino Mega 2560 using
the Arduino IDE before connecting.

## Face / motor mapping

| Face | Notation | Mega STEP pin | Mega DIR pin |
|---|---|---|---|
| Up | U | 2 | 3 |
| Right | R | 4 | 5 |
| Front | F | 6 | 7 |
| Down | D | 8 | 9 |
| Left | L | 10 | 11 |
| Back | B | 12 | 13 |

All six drivers share ENABLE on pin 22 (active LOW).

## Status

- [x] Repo scaffold, firmware, solver pipeline
- [ ] Order parts (see `docs/BOM.md`)
- [ ] Design and print frame and center couplers
- [ ] Wire and tune motor speed and current
- [ ] Calibrate color thresholds for your lighting
