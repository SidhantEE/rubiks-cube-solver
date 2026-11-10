"""Scan -> solve -> send moves to the robot.

Usage:
  python solver.py --demo                 # solve a built-in scrambled state, no hardware
  python solver.py --state <54 chars>     # solve a state you typed in
  python solver.py --port COM3            # scan with webcam, solve, run on robot
  python solver.py --port COM3 --moves "R U R' U'"   # send moves directly (testing)
"""

import argparse
import sys
import time

# A random valid scramble (URFDLB facelet order), used by --demo.
DEMO_STATE = "LUBRUFDUDBRRBRDUUFLBLDFDFFFLLRLDFURDBDFLLFRUUDRULBBRBB"


def _solve_twophase(state: str) -> str:
    """Pure-Python fallback (pip install RubikTwoPhase).

    The first run builds lookup tables, which takes a few minutes.
    Output like "R1 U3 F2 (3f)" is converted to standard notation "R U' F2".
    """
    import twophase.solver as sv

    raw = sv.solve(state, 20, 3)
    if raw.startswith("Error"):
        raise ValueError(f"Invalid cube state: {raw}")
    suffix = {"1": "", "2": "2", "3": "'"}
    tokens = [t for t in raw.split() if not t.startswith("(")]
    return " ".join(t[0] + suffix[t[1]] for t in tokens)


def solve(state: str) -> str:
    if len(state) != 54:
        raise ValueError(f"State must be 54 characters, got {len(state)}")
    try:
        import kociemba  # fast C version; needs a C compiler on Windows
    except ImportError:
        return _solve_twophase(state)
    try:
        return kociemba.solve(state)
    except ValueError as e:
        raise ValueError(f"Invalid cube state (check the scan): {e}") from e


def send_moves(port: str, moves: str, baud: int = 115200, timeout: float = 120.0):
    import serial  # imported here so --demo works without pyserial

    with serial.Serial(port, baud, timeout=1) as ser:
        time.sleep(2)  # the Mega resets when the port opens
        ser.reset_input_buffer()
        ser.write(b"PING\n")
        if ser.readline().decode().strip() != "PONG":
            raise RuntimeError("Robot did not answer PING. Check the port and firmware.")

        ser.write((moves + "\n").encode())
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = ser.readline().decode().strip()
            if not line:
                continue
            if line.startswith("DONE"):
                ms = int(line.split()[1])
                return ms / 1000.0
            if line.startswith("ERR"):
                raise RuntimeError(f"Robot error: {line}")
        raise TimeoutError("Robot did not finish in time")


def main():
    ap = argparse.ArgumentParser(description="Rubik's cube solver robot")
    ap.add_argument("--demo", action="store_true", help="solve a built-in example state")
    ap.add_argument("--state", help="54-char facelet string in URFDLB order")
    ap.add_argument("--moves", help="skip solving and send these moves")
    ap.add_argument("--port", help="serial port of the Arduino, e.g. COM3")
    ap.add_argument("--camera", type=int, default=0, help="webcam index")
    args = ap.parse_args()

    if args.moves:
        moves = args.moves
    else:
        if args.demo:
            state = DEMO_STATE
        elif args.state:
            state = args.state.upper()
        else:
            from scanner import scan
            state = scan(args.camera)
        print(f"State:    {state}")
        t0 = time.time()
        moves = solve(state)
        print(f"Solution: {moves}  ({len(moves.split())} moves, {time.time() - t0:.2f}s)")

    if args.port:
        secs = send_moves(args.port, moves)
        print(f"Robot finished in {secs:.2f}s")
    elif not args.demo and not args.state:
        print("No --port given, so nothing was sent to the robot.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, TimeoutError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
