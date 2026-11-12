# Bill of Materials

Audited on 10 November 2026 against the order lines and the parts' own
datasheets. `docs/build-plan.html` has the research behind each choice; its
cost table predates the order lines and is superseded by this file.

Prices are US dollars. "Order" means the line was read from the order or
invoice. "Cart" means the figure was read from the cart or checkout page but
did not appear in the order lines seen. "Listed" means the item is confirmed
ordered but the price comes from the product page. "Estimate" is a rough
figure to check before buying.

## Ordered

| Part | Qty | Each | Subtotal | Source | Basis |
|---|---|---|---|---|---|
| StepperOnline 17HE19-2004S stepper motor, pack of 5 | 1 | $35.47 | $35.47 | StepperOnline 5-17HE19-2004S | Order |
| StepperOnline 17HE19-2004S stepper motor, single | 1 | $8.71 | $8.71 | StepperOnline 17HE19-2004S | Order |
| StepperOnline packing fee | | | $1.90 | StepperOnline | Cart |
| TMC5160 SilentStepStick driver (one is a spare) | 7 | $19.20 | $134.40 | Mouser 700-TMC5160SILENTSTE | Order |
| Mouser tariff on the drivers | | | $10.78 | Mouser | Order |
| Teensy 4.1 with headers, SparkFun DEV-16996 | 1 | $35.95 | $35.95 | Mouser 474-DEV-16996 | Order |
| 22 AWG stranded wire, black, 25 ft | 1 | $5.95 | $5.95 | Mouser 474-PRT-08867 | Order |
| 22 AWG stranded wire, red, 25 ft | 1 | $5.95 | $5.95 | Mouser 474-PRT-08865 | Order |
| Mouser UPS Ground shipping | | | $9.39 | Mouser | Cart |
| YJ YuLong V2 M speed cube | 1 | $8.99 | $8.99 | TheCubicle | Listed |
| Cubicle Silicone Lube, Weight 3, 5 cc | 1 | $3.89 | $3.89 | TheCubicle | Listed |
| **Ordered subtotal** | | | **$261.38** | | |

Notes on the order:

- Jumper wires were in the Mouser cart but were not ordered; they are already
  owned.
- StepperOnline and TheCubicle shipping, and sales tax, are not included.

## Still to buy

| Part | Qty | Subtotal | Basis |
|---|---|---|---|
| 100 µF 50 V electrolytic capacitor, one per driver | 7 | $3 to $5 | Estimate |
| M3 screw assortment (see "Screws" below) | 1 box | $8 to $10 | Estimate |
| Screw terminals or protoboard for the 24 V wiring | 1 | $5 to $10 | Estimate |
| Micro-USB cable for the Teensy | 1 | $0 to $5 | Estimate; the board does not include one |
| Printed bench stand, UTA FabLab | 1 | about $5 | Estimate at $0.05 per gram |
| Printed six-motor frame and six shaft adapters, UTA FabLab | 1 set | $15 to $17 | Estimate at $0.05 per gram |
| USB camera, colour, global shutter (Arducam OV9782) | 2 | $120 | Estimate; see "Cameras" below |
| LED lighting for the cameras | 1 | $10 to $15 | Estimate |
| **Still-to-buy subtotal** | | **$166 to $187** | |

Not included: the 24 V power supply and jumper wires, which are already owned. It needs about
3 A for the one-motor bench test and about 10 A for all six motors.

## Total

| | |
|---|---|
| Ordered | $261.38 |
| Still to buy | $166 to $187 |
| **Whole build** | **$427 to $448** |
| Without cameras and lighting | $297 to $314 |

## Screws

| Use | Size | Qty |
|---|---|---|
| Motors to the frame (and to the bench stand) | M3 × 10 mm | 24 |
| Towers to the base, with nuts | M3 × 10 mm | 8 |
| Pedestal to the base, from underneath | M3 × 10 mm | 4 |
| Bridge to the two tall towers | M3 × 16 mm | 4 |
| Clamp screws onto the motor bodies (4 side motors and the top motor) | M3 × 8 mm | 10 |
| Shaft adapters onto the motor shafts | M3 × 6 mm | 6 |

The motor's mounting holes are 4.5 mm deep, so a screw through a 6 mm plate
must not be longer than 10 mm.

## Cameras

One camera sees at most three faces of the cube, which is not enough to work
out the other three. The options are a second camera, mirrors, or turning
faces to bring the hidden stickers into view. The list above assumes two
cameras. Starting with one ordinary USB webcam and the turn-to-reveal method
saves about $60 and needs no extra hardware.

The existing `software/scanner.py` avoids the question for now: you hold each
face up to one webcam by hand before placing the cube in the robot.

## Printed parts

All from `cad/`. Sizes are as printed.

| File | Qty | Size | Notes |
|---|---|---|---|
| `bench_stand.stl` | 1 | 158 × 90 × 74 mm | For the one-motor test |
| `frame_base.stl` | 1 | 208 × 208 × 6 mm | Print as it sits |
| `frame_pedestal.stl` | 1 | 56 × 56 × 55 mm | Print upside down |
| `frame_tower.stl` | 2 | 58.5 × 76 × 132 mm | Print standing on its foot |
| `frame_tower_tall.stl` | 2 | 58.5 × 76 × 163 mm | Print standing on its foot |
| `frame_top.stl` | 1 | 136 × 53 × 29.5 mm | Bridge; print as it sits, collar up |
| `drive_adapter_PLACEHOLDER_15mm_tip.stl` | 6 | 18 × 18 × 28.5 mm | Tip size is a placeholder; measure the cube first |

None need supports. All fit the UTA FabLab's Prusa i3 MK3 (250 × 210 × 210 mm).

## What the datasheets confirm

- **Motor (17HE19-2004S):** 0.55 Nm holding torque, 2.0 A, 1.30 Ω, 2.40 mH,
  62 g·cm² rotor, 0.27 kg. Shaft 5 mm × 24 mm with a 15 mm flat, 4.5 mm across
  the flat. Four M3 holes on a 31 mm square, 22 mm boss.
- **Motor cable:** 1 m, 24 AWG, 4-pin 2.54 mm plug wired red, blue, green,
  black (B−, A−, B+, A+). Swap the blue and green pins before plugging it onto
  a driver; see `hardware/README.md`.
- **Driver (TMC5160 SilentStepStick):** 10 to 35 V, 3 A RMS, configured over
  SPI, 0.075 Ω sense resistors.
- **Controller (Teensy 4.1):** 3.3 V logic, not 5 V tolerant.
- **Cube (YJ YuLong V2 M):** 56.0 mm, 88.9 g, magnetic.

Not confirmed: whether the driver boards arrive with header pins soldered.
