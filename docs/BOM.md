# Bill of Materials

Based on the [t33devv/rubik](https://github.com/t33devv/rubik) build (frame and parts list), plus the
parts that list leaves out. Items marked **added** are not on the t33devv list.
Prices are approximate USD from typical online listings (November 2026).

The illustrated version with order tracking is `docs/bom.html`.

## Motion
| # | Part | Spec | Qty | Unit | Total | |
|---|---|---|---|---|---|---|
| 1 | NEMA 17 pancake stepper | Short body (~23 mm), 5 mm D-shaft, e.g. STEPPERONLINE pancake | 6 | $11.00 | $66.00 | |
| 2 | A4988 stepper driver, 5-pack | StepStick format, run at 1/8 microstepping | 2 | $10.00 | $20.00 | 4 spares |
| 3 | 100 µF electrolytic capacitor | 35 V or higher, one across each driver's motor power | 6 | $0.50 | $3.00 | **added** |

## Control and power
| # | Part | Spec | Qty | Unit | Total | |
|---|---|---|---|---|---|---|
| 4 | Arduino Mega 2560 R3 | e.g. ELEGOO Mega, USB cable included | 1 | $24.00 | $24.00 | |
| 5 | 12 V 5 A power supply | 60 W brick, 5.5×2.1 mm plug | 1 | $14.00 | $14.00 | **added** |
| 6 | DC barrel jack to screw terminal | 5.5×2.1 mm female adapter | 1 | $3.00 | $3.00 | **added** |
| 7 | 830-point breadboard | Holds the six drivers and capacitors | 1 | $7.00 | $7.00 | |
| 8 | Jumper wire kit | Male-to-male Dupont wires and pre-cut breadboard jumpers | 1 | $12.00 | $12.00 | |

## Vision
| # | Part | Spec | Qty | Unit | Total | |
|---|---|---|---|---|---|---|
| 9 | USB webcam | 1080p, manual exposure preferred | 1 | $25.00 | $25.00 | **added**, optional |
| 10 | USB LED ring light | 6–10 in, 5600 K daylight | 1 | $12.00 | $12.00 | **added**, optional |

## Mechanical
| # | Part | Spec | Qty | Unit | Total | |
|---|---|---|---|---|---|---|
| 11 | GAN RS 3×3 cube, **no magnets** | Non-magnetic, stickerless | 1 | $17.00 | $17.00 | |
| 12 | PLA filament | 1 kg spool | 1 | $18.00 | $18.00 | **added** |
| 13 | M3 screw assortment | Socket caps, nuts, washers | 1 | $12.00 | $12.00 | |

## Tools
| # | Part | Spec | Qty | Unit | Total | |
|---|---|---|---|---|---|---|
| 14 | Digital multimeter | Any basic DC voltmeter, for setting driver Vref | 1 | $12.00 | $12.00 | skip if you have one |

**Total: about $245** (25 parts). The t33devv list alone is about $173. The difference is the
power supply, filament, capacitors, webcam and ring light.

Ways to change the cost:
- Already have a multimeter: −$12
- Skip the ring light: −$12
- Use a phone as the webcam, or type the colors in by hand: −$25
- TMC2209 drivers instead of A4988 (much quieter): about +$4

## 3D-printed parts
STLs are in the `3D Files` folder of [t33devv/rubik](https://github.com/t33devv/rubik). That repo has
no license, so download and print them for yourself, but don't copy them into this repo.
Print counts aren't listed there. Check the [build video](https://www.youtube.com/watch?v=QUscG2dRllM).

| File | What it does |
|---|---|
| `base plate.stl` | Bottom of the frame |
| `base web.stl` | Stiffens the base |
| `side plate no magnet.stl` | Side wall that holds a motor (use with a non-magnetic cube) |
| `side plate magnet.stl` | Alternative side wall |
| `side support.stl` | Braces the side walls |
| `stepper holder.stl` | Motor mount |
| `cube connector.stl` | Joins a motor shaft to a center piece (one per face) |
| `top brace.stl` | Holds the top motor over the cube |
