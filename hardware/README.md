# Hardware

## Mechanical concept

The cube is held in place only by its six center pieces. Each center cap is
removed and replaced with a printed **center coupler** that fits over a NEMA 17
shaft. Six motor brackets on a printed frame hold the motors on the cube's six
axes, so the cube floats in the middle with no other support.

Tips:
- Loosen the cube's core screws slightly so turns need little torque, but not
  so much that pieces pop out.
- Leave about 0.5 mm of axial play between the couplers and the cube. If the
  frame clamps too tightly, faces bind.
- Corner-cut a little: tune the motor speed until no move skips steps.

## Wiring

```
12V PSU ──┬── switch ──┬── VM / GND on all 6 driver carriers
          │            └── (do NOT power the Mega from 12 V here)
          │
Arduino Mega (USB-powered from the PC)
  GND ─────────────── GND on all 6 driver carriers (common ground!)
  D22 ─────────────── EN  on all 6 carriers (LOW = enabled)
  D2/D3   ── STEP/DIR ── U motor driver
  D4/D5   ── STEP/DIR ── R motor driver
  D6/D7   ── STEP/DIR ── F motor driver
  D8/D9   ── STEP/DIR ── D motor driver
  D10/D11 ── STEP/DIR ── L motor driver
  D12/D13 ── STEP/DIR ── B motor driver
```

Driver setup:
- Set microstepping to **1/8**. On TMC2209 carriers, MS1 = LOW and MS2 = LOW
  selects 1/8. On A4988, use MS1 = HIGH, MS2 = HIGH, MS3 = LOW.
- Set the current limit with the potentiometer to about 70% of the motor's
  rated current to start.
- Never plug or unplug a motor while the drivers are powered. That can destroy
  the driver.

## CAD

Put STL and source CAD files (Fusion 360 / Onshape exports) in this folder:

```
hardware/
  cad/        source files
  stl/        printable exports
```
