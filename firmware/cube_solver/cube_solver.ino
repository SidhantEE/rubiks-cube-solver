// Rubik's Cube Solver - Teensy 4.1 with six TMC5160 SilentStepStick drivers
//
// Serial protocol (USB serial, newline-terminated):
//   "R U' F2 D B L'"   executes the moves, replies "DONE <ms>"
//   "PING"             replies "PONG"
//   "ON" / "OFF"       enable / disable all drivers (OFF lets you turn faces by hand)
//   "TURN <ms>"        time for one quarter turn, 10 to 1000 (lower = faster)
//   "SETTLE <ms>"      pause after each move, 0 to 500
//   "CURRENT <mA>"     motor run current in mA RMS, 200 to 2800
//   "STATUS"           one line per driver: chip version and fault flags
//
// Consecutive moves on opposite faces (U/D, R/L, F/B) run at the same time.
//
// Hardware
//   Motors   StepperOnline 17HE19-2004S, 1.8 deg, 2.0 A RMS
//   Drivers  TMC5160 SilentStepStick in STEP/DIR mode, configured over SPI
//            (the board has no standalone mode, so SPI is required)
//   Logic    3.3 V. The Teensy 4.1 is NOT 5 V tolerant.
//   Supply   24 V to each driver's VM, 100 uF across VM/GND at each driver
//
// Wiring (Teensy pin numbers)
//   SPI shared by all six drivers: MOSI 11 -> SDI, MISO 12 <- SDO, SCK 13 -> SCK
//   EN shared: pin 23 (LOW = drivers on)
//   Face   STEP  DIR  CS
//   U      2     3    4
//   R      5     6    7
//   F      8     9    10
//   D      14    15   16
//   L      17    18   19
//   B      20    21   22

#include <Arduino.h>
#include <SPI.h>

const uint8_t NUM_FACES = 6;
const char FACE_NAMES[NUM_FACES] = {'U', 'R', 'F', 'D', 'L', 'B'};
const uint8_t STEP_PINS[NUM_FACES] = {2, 5, 8, 14, 17, 20};
const uint8_t DIR_PINS[NUM_FACES] = {3, 6, 9, 15, 18, 21};
const uint8_t CS_PINS[NUM_FACES] = {4, 7, 10, 16, 19, 22};
const uint8_t OPPOSITE[NUM_FACES] = {3, 4, 5, 0, 1, 2};  // U-D, R-L, F-B
const uint8_t ENABLE_PIN = 23;                           // shared, active LOW

// Flip any entry if that motor turns the wrong way when mounted.
const bool INVERT_DIR[NUM_FACES] = {false, false, false, false, false, false};

// ---- driver settings
const float R_SENSE_OHM = 0.075f;  // sense resistor on the TMC5160 SilentStepStick
const float V_FULL_SCALE = 0.325f; // TMC5160 full-scale sense voltage
const uint8_t MRES_8_MICROSTEPS = 5;
const uint16_t MICROSTEPS = 8;
const uint8_t HOLD_CURRENT_31THS = 9;  // standstill current, about 30% of run current
uint16_t runCurrentMa = 2000;          // 17HE19-2004S rated current

const uint8_t REG_GCONF = 0x00;
const uint8_t REG_GSTAT = 0x01;
const uint8_t REG_IOIN = 0x04;
const uint8_t REG_GLOBAL_SCALER = 0x0B;
const uint8_t REG_IHOLD_IRUN = 0x10;
const uint8_t REG_TPOWERDOWN = 0x11;
const uint8_t REG_CHOPCONF = 0x6C;
const uint8_t REG_DRV_STATUS = 0x6F;
const uint8_t TMC5160_VERSION = 0x30;

// ---- motion settings
const uint32_t STEPS_PER_REV = 200UL * MICROSTEPS;
const uint32_t QUARTER_TURN = STEPS_PER_REV / 4;
const float MAX_STEPS_PER_S = 1000.0f / 60.0f * STEPS_PER_REV;  // 1000 rpm ceiling
float quarterTurnMs = 60.0f;  // start slow; shorten with TURN until steps are lost
uint16_t settleMs = 5;
float accel = 0.0f;           // steps/s^2, derived from quarterTurnMs

bool driverOk[NUM_FACES] = {false, false, false, false, false, false};
char lineBuf[401];
uint16_t lineLen = 0;

// One face's move in progress. This must stay above the first function: the
// Arduino build inserts function prototypes there, and they need the type.
struct Axis {
  uint8_t face;
  uint32_t total;   // steps in this move
  uint32_t done;
  float nAcc;       // steps spent accelerating
  float tAcc;       // seconds spent accelerating
  float vPeak;      // steps/s at the top of the profile
  float tTotal;     // seconds for the whole move
  uint32_t nextUs;  // time of the next step, microseconds from the start
};

// ------------------------------------------------------------- TMC5160 SPI
SPISettings tmcSpi(1000000, MSBFIRST, SPI_MODE3);

// One 40-bit datagram: address byte, then four data bytes. Returns the four
// bytes clocked back, which answer the PREVIOUS datagram sent to this driver.
uint32_t tmcTransfer(uint8_t face, uint8_t address, uint32_t data) {
  SPI.beginTransaction(tmcSpi);
  digitalWrite(CS_PINS[face], LOW);
  SPI.transfer(address);
  uint32_t reply = SPI.transfer((data >> 24) & 0xFF);
  reply = (reply << 8) | SPI.transfer((data >> 16) & 0xFF);
  reply = (reply << 8) | SPI.transfer((data >> 8) & 0xFF);
  reply = (reply << 8) | SPI.transfer(data & 0xFF);
  digitalWrite(CS_PINS[face], HIGH);
  SPI.endTransaction();
  return reply;
}

void tmcWrite(uint8_t face, uint8_t reg, uint32_t value) {
  tmcTransfer(face, reg | 0x80, value);
}

uint32_t tmcRead(uint8_t face, uint8_t reg) {
  tmcTransfer(face, reg, 0);
  return tmcTransfer(face, reg, 0);
}

// GLOBAL_SCALER that gives the requested RMS current with the run current
// setting at its maximum (31), which keeps the best current resolution.
uint32_t globalScalerFor(uint16_t currentMa) {
  float peakA = currentMa / 1000.0f * 1.41421356f;
  long scaler = lroundf(256.0f * peakA * R_SENSE_OHM / V_FULL_SCALE);
  if (scaler < 32) scaler = 32;
  if (scaler > 255) scaler = 0;  // 0 means full scale
  return (uint32_t)scaler;
}

// Returns true if a TMC5160 answered on this chip select.
bool configureDriver(uint8_t face) {
  uint8_t version = tmcRead(face, REG_IOIN) >> 24;
  if (version != TMC5160_VERSION) return false;

  tmcWrite(face, REG_GSTAT, 0x07);        // clear reset / error flags
  tmcWrite(face, REG_GCONF, 0x00000008);  // SpreadCycle (best at speed), step filter on
  tmcWrite(face, REG_GLOBAL_SCALER, globalScalerFor(runCurrentMa));
  // IHOLDDELAY = 6, IRUN = 31, IHOLD = HOLD_CURRENT_31THS
  tmcWrite(face, REG_IHOLD_IRUN, (6UL << 16) | (31UL << 8) | HOLD_CURRENT_31THS);
  tmcWrite(face, REG_TPOWERDOWN, 10);
  // TOFF = 3, HSTRT = 4, HEND = 1, TBL = 2, SpreadCycle, interpolation on, 8 microsteps
  tmcWrite(face, REG_CHOPCONF, 0x100100C3UL | ((uint32_t)MRES_8_MICROSTEPS << 24));
  return true;
}

void configureAllDrivers() {
  for (uint8_t i = 0; i < NUM_FACES; i++) driverOk[i] = configureDriver(i);
}

// A driver forgets its settings whenever its 24 V supply is switched off.
// Set up any driver that is missing or reports that it has been reset.
void ensureDrivers() {
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    if (!driverOk[i] || (tmcRead(i, REG_GSTAT) & 0x01)) driverOk[i] = configureDriver(i);
  }
}

void printStatus() {
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    uint8_t version = tmcRead(i, REG_IOIN) >> 24;
    uint32_t drv = tmcRead(i, REG_DRV_STATUS);
    uint32_t gstat = tmcRead(i, REG_GSTAT);
    Serial.print(FACE_NAMES[i]);
    Serial.print(" version=0x");
    Serial.print(version, HEX);
    if (version != TMC5160_VERSION) {
      Serial.println(" NO DRIVER (check wiring, 24 V and CS pin)");
      continue;
    }
    if (drv & (1UL << 25)) Serial.print(" OVERTEMP");
    if (drv & (1UL << 26)) Serial.print(" overtemp-warning");
    if (drv & (3UL << 27)) Serial.print(" SHORT-TO-GROUND");
    if (drv & (3UL << 29)) Serial.print(" open-load");
    if (gstat & 0x01) Serial.print(" was-reset");
    if (gstat & 0x02) Serial.print(" DRIVER-ERROR");
    if (gstat & 0x04) Serial.print(" UNDERVOLTAGE");
    Serial.println(" ok");
  }
}

// ----------------------------------------------------------------- motion
void updateAccel() {
  // A quarter turn that accelerates for half its steps and brakes for the rest.
  float t = quarterTurnMs / 1000.0f;
  accel = 4.0f * QUARTER_TURN / (t * t);
}

// Time in seconds at which step i (0-based) of a move should fire.
float stepTime(const Axis &a, uint32_t i) {
  float p = i + 0.5f;
  if (p <= a.nAcc) return sqrtf(2.0f * p / accel);
  if (p <= a.total - a.nAcc) return a.tAcc + (p - a.nAcc) / a.vPeak;
  return a.tTotal - sqrtf(2.0f * (a.total - p) / accel);
}

void planAxis(Axis &a, uint8_t face, int8_t quarters) {
  a.face = face;
  a.total = QUARTER_TURN * (uint32_t)abs(quarters);
  a.done = 0;
  float toTopSpeed = MAX_STEPS_PER_S * MAX_STEPS_PER_S / (2.0f * accel);
  a.nAcc = min(toTopSpeed, a.total / 2.0f);
  a.tAcc = sqrtf(2.0f * a.nAcc / accel);
  a.vPeak = accel * a.tAcc;
  a.tTotal = 2.0f * a.tAcc + (a.total - 2.0f * a.nAcc) / a.vPeak;
  a.nextUs = (uint32_t)(stepTime(a, 0) * 1e6f);

  bool cw = quarters > 0;
  if (INVERT_DIR[face]) cw = !cw;
  digitalWrite(DIR_PINS[face], cw ? HIGH : LOW);
}

inline void stepIfDue(Axis &a, uint32_t elapsedUs) {
  if (a.done >= a.total || elapsedUs < a.nextUs) return;
  digitalWriteFast(STEP_PINS[a.face], HIGH);
  delayNanoseconds(300);
  digitalWriteFast(STEP_PINS[a.face], LOW);
  a.done++;
  if (a.done < a.total) a.nextUs = (uint32_t)(stepTime(a, a.done) * 1e6f);
}

// Runs one move, or two moves on opposite faces together when second is set.
void runMoves(Axis &first, Axis *second) {
  delayMicroseconds(2);  // direction setup time before the first step
  uint32_t start = micros();
  while (first.done < first.total || (second && second->done < second->total)) {
    uint32_t elapsed = micros() - start;
    stepIfDue(first, elapsed);
    if (second) stepIfDue(*second, elapsed);
  }
  if (settleMs) delay(settleMs);
}

// ---------------------------------------------------------------- parsing
int faceIndex(char c) {
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    if (FACE_NAMES[i] == c) return i;
  }
  return -1;
}

// Parses one token such as "R", "R'" or "R2". Returns false if it is invalid.
bool parseToken(const char *tok, uint8_t &face, int8_t &quarters) {
  int f = faceIndex(tok[0]);
  if (f < 0) return false;
  face = (uint8_t)f;
  if (tok[1] == '\0') { quarters = 1; return true; }
  if (tok[2] != '\0') return false;
  if (tok[1] == '\'') { quarters = -1; return true; }
  if (tok[1] == '2') { quarters = 2; return true; }
  return false;
}

const uint8_t MAX_MOVES = 120;
uint8_t moveFace[MAX_MOVES];
int8_t moveQuarters[MAX_MOVES];

void runSequence(char *line) {
  // Validate every token first so a typo never leaves the cube half-solved.
  uint8_t count = 0;
  for (char *tok = strtok(line, " "); tok; tok = strtok(NULL, " ")) {
    if (count >= MAX_MOVES) { Serial.println("ERR too many moves"); return; }
    if (!parseToken(tok, moveFace[count], moveQuarters[count])) {
      Serial.print("ERR bad move: ");
      Serial.println(tok);
      return;
    }
    count++;
  }
  ensureDrivers();
  for (uint8_t i = 0; i < count; i++) {
    if (!driverOk[moveFace[i]]) {
      Serial.print("ERR no driver on face ");
      Serial.println(FACE_NAMES[moveFace[i]]);
      return;
    }
  }

  digitalWrite(ENABLE_PIN, LOW);
  uint32_t t0 = millis();
  uint8_t i = 0;
  while (i < count) {
    Axis a, b;
    planAxis(a, moveFace[i], moveQuarters[i]);
    if (i + 1 < count && moveFace[i + 1] == OPPOSITE[moveFace[i]]) {
      planAxis(b, moveFace[i + 1], moveQuarters[i + 1]);
      runMoves(a, &b);
      i += 2;
    } else {
      runMoves(a, NULL);
      i += 1;
    }
  }
  Serial.print("DONE ");
  Serial.println(millis() - t0);
}

bool startsWith(const char *line, const char *prefix) {
  return strncmp(line, prefix, strlen(prefix)) == 0;
}

void handleLine(char *line) {
  while (*line == ' ') line++;
  size_t n = strlen(line);
  while (n > 0 && (line[n - 1] == ' ' || line[n - 1] == '\r')) line[--n] = '\0';
  if (n == 0) return;

  if (strcmp(line, "PING") == 0) { Serial.println("PONG"); return; }
  if (strcmp(line, "ON") == 0) { digitalWrite(ENABLE_PIN, LOW); Serial.println("OK"); return; }
  if (strcmp(line, "OFF") == 0) { digitalWrite(ENABLE_PIN, HIGH); Serial.println("OK"); return; }
  if (strcmp(line, "STATUS") == 0) { printStatus(); return; }
  if (startsWith(line, "TURN ")) {
    long v = atol(line + 5);
    if (v < 10 || v > 1000) { Serial.println("ERR turn time out of range (10-1000 ms)"); return; }
    quarterTurnMs = (float)v;
    updateAccel();
    Serial.println("OK");
    return;
  }
  if (startsWith(line, "SETTLE ")) {
    long v = atol(line + 7);
    if (v < 0 || v > 500) { Serial.println("ERR settle out of range (0-500 ms)"); return; }
    settleMs = (uint16_t)v;
    Serial.println("OK");
    return;
  }
  if (startsWith(line, "CURRENT ")) {
    long v = atol(line + 8);
    if (v < 200 || v > 2800) { Serial.println("ERR current out of range (200-2800 mA)"); return; }
    runCurrentMa = (uint16_t)v;
    configureAllDrivers();
    Serial.println("OK");
    return;
  }
  runSequence(line);
}

void setup() {
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, HIGH);  // drivers off until they are configured
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    pinMode(STEP_PINS[i], OUTPUT);
    pinMode(DIR_PINS[i], OUTPUT);
    pinMode(CS_PINS[i], OUTPUT);
    digitalWrite(STEP_PINS[i], LOW);
    digitalWrite(CS_PINS[i], HIGH);
  }
  Serial.begin(115200);
  SPI.begin();
  delay(100);  // let the drivers power up
  updateAccel();
  configureAllDrivers();
  digitalWrite(ENABLE_PIN, LOW);

  Serial.print("READY drivers:");
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    Serial.print(' ');
    Serial.print(FACE_NAMES[i]);
    Serial.print(driverOk[i] ? "=ok" : "=missing");
  }
  Serial.println();
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      lineBuf[lineLen] = '\0';
      handleLine(lineBuf);
      lineLen = 0;
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    }
  }
}
