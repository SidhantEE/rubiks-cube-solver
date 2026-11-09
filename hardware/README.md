# Hardware

## Frame

The frame is the 3D-printed design from [t33devv/rubik](https://github.com/t33devv/rubik)
(`3D Files` folder). It has no license, so the STLs are not copied here. Download and print
them yourself. See `docs/BOM.md` for what each file does, and the
[build video](https://www.youtube.com/watch?v=QUscG2dRllM) for print counts and assembly.

The cube is held only by its six center pieces. Each center cap comes off and a printed
cube connector joins that center to a pancake NEMA 17 shaft.

Tips:
- Use a cube **without magnets** (the BOM lists a GAN RS). Magnets make each turn snap
  into place, which fights the motors.
- Loosen the cube's core screws a little so turns need less torque, but not so much that
  pieces pop out.
- Frame precision matters most. If one face stops at 85° instead of 90°, the next turn
  jams. Print the connectors and motor mounts accurately and check that all six shafts
  point at the cube's exact center.

## Wiring

```
12V PSU ── barrel jack adapter ──┬── VMOT on all 6 A4988s
                                 └── 100 µF cap across VMOT/GND at each driver
                                     (do NOT power the Mega from this 12 V)

Arduino Mega (USB-powered from the PC)
  5V  ─────────────── VDD on all 6 A4988s (logic power)
  GND ─────────────── GND on all 6 A4988s (common ground with the 12 V supply)
  D22 ─────────────── EN  on all 6 A4988s (LOW = enabled)
  D2/D3   ── STEP/DIR ── U motor driver
  D4/D5   ── STEP/DIR ── R motor driver
  D6/D7   ── STEP/DIR ── F motor driver
  D8/D9   ── STEP/DIR ── D motor driver
  D10/D11 ── STEP/DIR ── L motor driver
  D12/D13 ── STEP/DIR ── B motor driver

On every A4988:
  RESET ── SLEEP   (jumper them together, or the driver stays asleep)
  MS1 = HIGH, MS2 = HIGH, MS3 = LOW   (1/8 microstepping, matches the firmware)
  1A/1B/2A/2B ── motor coils
```

## Setting the current limit (do this before connecting motors)

Each A4988 has a small potentiometer that sets the motor current. Too high overheats the
motor and driver. Too low makes the motor skip steps.

1. Power the driver (12 V and 5 V connected, motor **disconnected**).
2. Measure the voltage between the potentiometer's top and GND with the multimeter. That's Vref.
3. Turn the potentiometer until `Vref = current limit × 8 × Rsense`.
   - Most StepStick A4988 boards have Rsense = 0.1 Ω (marked `R100`), so Vref = current × 0.8.
   - Check your motor's rated current and start at about 70% of it.
     For a 1.0 A pancake motor: 0.7 A × 0.8 = **Vref ≈ 0.56 V**.

Never plug or unplug a motor while the drivers are powered. That can destroy the driver.

## References

- [t33devv/rubik](https://github.com/t33devv/rubik): frame STLs, schematic, parts list
- [RahbeA/Rubiks-Cube-Robot](https://github.com/RahbeA/Rubiks-Cube-Robot): another build on the same
  frame, with firmware that turns opposite faces at the same time
- [From zero to Rubik's cube solving robot](https://stevcooo.medium.com/from-zero-to-rubiks-cube-solving-robot-ad3a2838cd):
  a write-up of the lessons learned building a six-motor solver
