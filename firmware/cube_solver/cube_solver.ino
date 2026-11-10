// Rubik's Cube Solver - Arduino Mega 2560 firmware
//
// Serial protocol (115200 baud, newline-terminated):
//   "R U' F2 D B L'\n"  -> executes the moves, replies "DONE <ms>"
//   "PING\n"            -> replies "PONG"
//   "ON\n" / "OFF\n"    -> enable / disable all drivers (OFF lets you turn faces by hand)
//   "SPEED <us>\n"      -> set minimum step delay in microseconds (lower = faster)
//
// Drivers: TMC2209 or A4988 in STEP/DIR mode, 1/8 microstepping.
// 200 full steps * 8 = 1600 microsteps per rev -> 400 per quarter turn.

const uint8_t NUM_FACES = 6;
const char FACE_NAMES[NUM_FACES] = {'U', 'R', 'F', 'D', 'L', 'B'};
const uint8_t STEP_PINS[NUM_FACES] = {2, 4, 6, 8, 10, 12};
const uint8_t DIR_PINS[NUM_FACES]  = {3, 5, 7, 9, 11, 13};
const uint8_t ENABLE_PIN = 22;  // shared, active LOW

// Flip any entry if that motor turns the wrong way when mounted.
const bool INVERT_DIR[NUM_FACES] = {false, false, false, false, false, false};

const uint16_t MICROSTEPS_PER_REV = 1600;
const uint16_t QUARTER_TURN = MICROSTEPS_PER_REV / 4;

uint16_t minStepDelayUs = 120;     // cruise speed
const uint16_t START_DELAY_US = 600; // start/end speed for the ramp
const uint16_t RAMP_STEPS = 80;
const uint16_t SETTLE_MS = 15;     // pause between moves

String lineBuf;

void setup() {
  Serial.begin(115200);
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    pinMode(STEP_PINS[i], OUTPUT);
    pinMode(DIR_PINS[i], OUTPUT);
    digitalWrite(STEP_PINS[i], LOW);
  }
  pinMode(ENABLE_PIN, OUTPUT);
  digitalWrite(ENABLE_PIN, LOW);  // enable drivers
  Serial.println("READY");
}

int faceIndex(char c) {
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    if (FACE_NAMES[i] == c) return i;
  }
  return -1;
}

// Turn one face. quarters: 1 = clockwise 90, -1 = counter-clockwise 90, 2 = 180.
void turnFace(uint8_t face, int8_t quarters) {
  bool cw = quarters > 0;
  if (INVERT_DIR[face]) cw = !cw;
  digitalWrite(DIR_PINS[face], cw ? HIGH : LOW);
  delayMicroseconds(5);

  uint32_t total = (uint32_t)QUARTER_TURN * abs(quarters);
  uint16_t ramp = min((uint32_t)RAMP_STEPS, total / 2);

  for (uint32_t s = 0; s < total; s++) {
    // Linear speed ramp at both ends to avoid skipped steps.
    uint16_t d = minStepDelayUs;
    uint32_t fromEnd = total - 1 - s;
    uint32_t edge = min(s, fromEnd);
    if (edge < ramp) {
      d = START_DELAY_US - (uint32_t)(START_DELAY_US - minStepDelayUs) * edge / ramp;
    }
    digitalWrite(STEP_PINS[face], HIGH);
    delayMicroseconds(3);
    digitalWrite(STEP_PINS[face], LOW);
    delayMicroseconds(d);
  }
  delay(SETTLE_MS);
}

// Parse a single token like "R", "R'", "R2". Returns false if invalid.
bool runToken(const String &tok) {
  if (tok.length() == 0) return true;
  int face = faceIndex(tok.charAt(0));
  if (face < 0) return false;
  int8_t q = 1;
  if (tok.length() > 1) {
    char m = tok.charAt(1);
    if (m == '\'') q = -1;
    else if (m == '2') q = 2;
    else return false;
  }
  turnFace(face, q);
  return true;
}

void handleLine(String line) {
  line.trim();
  if (line.length() == 0) return;

  if (line == "PING") { Serial.println("PONG"); return; }
  if (line == "ON")   { digitalWrite(ENABLE_PIN, LOW);  Serial.println("OK"); return; }
  if (line == "OFF")  { digitalWrite(ENABLE_PIN, HIGH); Serial.println("OK"); return; }
  if (line.startsWith("SPEED ")) {
    long v = line.substring(6).toInt();
    if (v >= 40 && v <= 5000) { minStepDelayUs = v; Serial.println("OK"); }
    else Serial.println("ERR speed out of range (40-5000)");
    return;
  }

  // Validate every token first so a typo never leaves the cube half-solved.
  int start = 0;
  while (start < (int)line.length()) {
    int sp = line.indexOf(' ', start);
    if (sp < 0) sp = line.length();
    String tok = line.substring(start, sp);
    if (tok.length() > 0) {
      int f = faceIndex(tok.charAt(0));
      bool ok = f >= 0 && (tok.length() == 1 ||
                (tok.length() == 2 && (tok.charAt(1) == '\'' || tok.charAt(1) == '2')));
      if (!ok) { Serial.print("ERR bad move: "); Serial.println(tok); return; }
    }
    start = sp + 1;
  }

  digitalWrite(ENABLE_PIN, LOW);
  unsigned long t0 = millis();
  start = 0;
  while (start < (int)line.length()) {
    int sp = line.indexOf(' ', start);
    if (sp < 0) sp = line.length();
    runToken(line.substring(start, sp));
    start = sp + 1;
  }
  Serial.print("DONE ");
  Serial.println(millis() - t0);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') { handleLine(lineBuf); lineBuf = ""; }
    else if (c != '\r' && lineBuf.length() < 400) lineBuf += c;
  }
}
