# Bill of Materials

Audited on 10 November 2026 against the shopping carts and the parts' own
datasheets. `docs/build-plan.html` has the research behind each choice.

Prices are US dollars. "Seen" means the price was read from the cart or
checkout page. "Listed" means it was read from the product page but the order
itself was not seen. "Estimate" is a rough figure to check before buying.

## Ordered

| Part | Qty | Each | Subtotal | Source | Basis |
|---|---|---|---|---|---|
| StepperOnline 17HE19-2004S stepper motor, US warehouse | 6 | $8.45 | $50.70 | StepperOnline | Seen |
| StepperOnline packing fee | | | $1.90 | StepperOnline | Seen |
| TMC5160 SilentStepStick driver (one is a spare) | 7 | $19.20 | $134.40 | Mouser 700-TMC5160SILENTSTE | Seen |
| Teensy 4.1 with headers, SparkFun DEV-16996 | 1 | $35.95 | $35.95 | Mouser 474-DEV-16996 | Seen |
| Jumper wires, 6 in, male to female, pack of 20 | 1 | $2.75 | $2.75 | Mouser 474-PRT-12794 | Seen |
| Jumper wires, 6 in, female to female, pack of 20 | 1 | $2.75 | $2.75 | Mouser 474-PRT-12796 | Seen |
| 22 AWG stranded wire, black, 25 ft | 1 | $5.95 | $5.95 | Mouser 474-PRT-08867 | Seen |
| Mouser estimated tariff | | | $12.88 | Mouser | Seen |
| Mouser UPS Ground shipping | | | $9.39 | Mouser | Seen |
| YJ YuLong V2 M speed cube | 1 | $8.99 | $8.99 | TheCubicle | Listed |
| Cubicle Silicone Lube, Weight 3, 5 cc | 1 | $3.89 | $3.89 | TheCubicle | Listed |
| **Ordered subtotal** | | | **$269.55** | | |

The carts were seen but the final orders were not, so three things may differ:

- If the motors were bought as a 5-pack plus one single, they cost about $6.78 less.
- If the red 22 AWG wire (Mouser 474-PRT-08865) was added, add $5.95.
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

Not included: the 24 V power supply, which is already owned. It needs about
3 A for the one-motor bench test and about 10 A for all six motors.

## Total

| | |
|---|---|
| Ordered | $269.55 |
| Still to buy | $166 to $187 |
| **Whole build** | **$436 to $457** |
| Without cameras and lighting | $306 to $322 |

## Screws

| Use | Size | Qty |
|---|---|---|
| Motors to the frame (and to the bench stand) | M3 × 10 mm | 24 |
| Towers to the deck, with nuts | M3 × 12 mm | 8 |
| Top plate to the towers | M3 × 16 mm | 8 |
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
| `frame_base.stl` | 1 | 200 × 200 × 61 mm | Print upside down |
| `frame_tower.stl` | 4 | 42 × 76 × 108 mm | Print standing on its foot |
| `frame_top.stl` | 1 | 140 × 140 × 10 mm | Print upside down |
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
