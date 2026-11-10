// Compiles the real firmware against the stand-in API and runs it.
#include "Arduino.h"
#include "SPI.h"

uint64_t simNowUs = 0;
std::vector<StepEvent> simSteps;
std::map<uint8_t, int> simPinLevel;
int simSelectedCs = -1;
SerialStub Serial;
SPIStub SPI;

// ---- simulated TMC5160 drivers, keyed by chip-select pin
struct FakeTmc {
  bool present = true;
  std::map<uint8_t, uint32_t> reg;
  uint32_t pendingReply = 0;
  uint8_t bytes[5]; int n = 0;
};
std::map<int, FakeTmc> tmc;

void digitalWrite(uint8_t pin, uint8_t level) {
  int before = simPinLevel.count(pin) ? simPinLevel[pin] : -1;
  simPinLevel[pin] = level;
  if (tmc.count(pin)) {                       // chip select
    if (level == LOW) { simSelectedCs = pin; tmc[pin].n = 0; }
    else if (simSelectedCs == pin) {
      FakeTmc &t = tmc[pin];
      if (t.n == 5) {
        uint8_t addr = t.bytes[0];
        uint32_t data = ((uint32_t)t.bytes[1] << 24) | ((uint32_t)t.bytes[2] << 16) |
                        ((uint32_t)t.bytes[3] << 8) | t.bytes[4];
        if (addr & 0x80) { t.reg[addr & 0x7F] = data; if ((addr & 0x7F) == 0x01) t.reg[0x01] = 0; }
        else t.pendingReply = t.reg.count(addr) ? t.reg[addr] : 0;
      }
      simSelectedCs = -1;
    }
    return;
  }
  if (level == HIGH && before != HIGH) simSteps.push_back({simNowUs, pin});
}

uint8_t SPIStub::transfer(uint8_t b) {
  if (simSelectedCs < 0) return 0;
  FakeTmc &t = tmc[simSelectedCs];
  uint8_t out = 0;
  if (t.present && t.n >= 1 && t.n <= 4) out = (t.pendingReply >> (8 * (4 - t.n))) & 0xFF;
  if (t.n < 5) t.bytes[t.n] = b;
  t.n++;
  return out;
}

#include "../cube_solver/cube_solver.ino"

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("FAIL: %s\n", msg); failures++; } else printf("ok:   %s\n", msg); } while (0)

std::string send(const char *line) {
  Serial.out.clear();
  Serial.in = std::string(line) + "\n"; Serial.pos = 0;
  simSteps.clear();
  loop();
  return Serial.out;
}

struct Stats { int steps = 0; double firstMs = 0, lastMs = 0, peakHz = 0; };
Stats statsFor(uint8_t stepPin) {
  Stats s; uint64_t prev = 0;
  for (auto &e : simSteps) if (e.pin == stepPin) {
    if (!s.steps) s.firstMs = e.us / 1000.0;
    else if (e.us > prev) s.peakHz = std::max(s.peakHz, 1e6 / (double)(e.us - prev));
    s.lastMs = e.us / 1000.0; prev = e.us; s.steps++;
  }
  return s;
}

int main() {
  for (uint8_t i = 0; i < NUM_FACES; i++) {
    tmc[CS_PINS[i]].reg[0x04] = 0x30000000;   // IOIN: TMC5160 version
    tmc[CS_PINS[i]].reg[0x01] = 0x01;         // GSTAT: reset flag set after power-up
  }
  // step pins must not be mistaken for chip selects
  setup();
  printf("boot: %s", Serial.out.c_str());
  CHECK(Serial.out.find("U=ok") != std::string::npos && Serial.out.find("missing") == std::string::npos,
        "all six drivers detected at boot");
  FakeTmc &u = tmc[CS_PINS[0]];
  printf("U registers: GCONF=%08X GLOBAL_SCALER=%u IHOLD_IRUN=%08X CHOPCONF=%08X\n",
         u.reg[0x00], u.reg[0x0B], u.reg[0x10], u.reg[0x6C]);
  CHECK(u.reg[0x00] == 0x00000008, "GCONF selects SpreadCycle");
  CHECK(u.reg[0x0B] == 167, "GLOBAL_SCALER is 167 for 2.0 A RMS");
  CHECK(u.reg[0x10] == 0x00061F09, "IHOLD_IRUN: IRUN=31, IHOLD=9, delay=6");
  CHECK(u.reg[0x6C] == 0x150100C3, "CHOPCONF: 8 microsteps, interpolation, TOFF=3");
  double irms = 167 / 256.0 * 0.325 / 0.075 / 1.41421356;
  printf("run current from those registers: %.2f A RMS\n", irms);
  CHECK(std::fabs(irms - 2.0) < 0.03, "computed run current is 2.0 A RMS");

  CHECK(send("PING") == "PONG\n", "PING answers PONG");

  std::string r = send("R");
  Stats s = statsFor(STEP_PINS[1]);
  printf("R at TURN 60:  %d steps in %.1f ms, peak %.0f steps/s -> %s", s.steps, s.lastMs - s.firstMs, s.peakHz, r.c_str());
  CHECK(s.steps == 400, "quarter turn is 400 steps");
  // first step fires half a step in, last step half a step before the end
  CHECK((s.lastMs - s.firstMs) > 56.0 && (s.lastMs - s.firstMs) <= 60.0, "quarter turn fits in 60 ms");
  CHECK(simPinLevel[DIR_PINS[1]] == HIGH, "clockwise sets DIR high");

  send("R'");
  CHECK(simPinLevel[DIR_PINS[1]] == LOW, "counter-clockwise sets DIR low");

  send("R2"); s = statsFor(STEP_PINS[1]);
  printf("R2 at TURN 60: %d steps in %.1f ms, peak %.0f steps/s\n", s.steps, s.lastMs - s.firstMs, s.peakHz);
  CHECK(s.steps == 800, "half turn is 800 steps");

  CHECK(send("TURN 40") == "OK\n", "TURN 40 accepted");
  r = send("R"); s = statsFor(STEP_PINS[1]);
  printf("R at TURN 40:  %d steps in %.1f ms, peak %.0f steps/s (%.0f rpm)\n", s.steps, s.lastMs - s.firstMs, s.peakHz, s.peakHz / 1600 * 60);
  CHECK((s.lastMs - s.firstMs) > 37.0 && (s.lastMs - s.firstMs) <= 40.0, "quarter turn fits in 40 ms");

  r = send("U D"); Stats su = statsFor(STEP_PINS[0]), sd = statsFor(STEP_PINS[3]);
  printf("U D together:  U %.1f-%.1f ms, D %.1f-%.1f ms -> %s", su.firstMs, su.lastMs, sd.firstMs, sd.lastMs, r.c_str());
  CHECK(su.steps == 400 && sd.steps == 400, "U and D each step 400 times");
  CHECK(std::fabs(su.firstMs - sd.firstMs) < 0.5 && std::fabs(su.lastMs - sd.lastMs) < 0.5, "opposite faces turn at the same time");

  send("U D2"); su = statsFor(STEP_PINS[0]); sd = statsFor(STEP_PINS[3]);
  CHECK(su.steps == 400 && sd.steps == 800, "U with D2: 400 and 800 steps");

  r = send("U R"); su = statsFor(STEP_PINS[0]); Stats sr = statsFor(STEP_PINS[1]);
  CHECK(sr.firstMs > su.lastMs, "adjacent faces turn one after the other");

  r = send("R U' F2 D B L'");
  printf("six moves at TURN 40: %s", r.c_str());
  CHECK(r.rfind("DONE", 0) == 0, "sequence replies DONE");

  CHECK(send("R X") == "ERR bad move: X\n", "bad move rejected before anything turns");
  CHECK(simSteps.empty(), "no steps issued for a rejected sequence");
  CHECK(send("TURN 5").rfind("ERR", 0) == 0, "out-of-range TURN rejected");

  // a driver that loses power forgets its settings; it must be set up again
  tmc[CS_PINS[2]].reg.erase(0x6C); tmc[CS_PINS[2]].reg[0x01] = 0x01;
  send("F");
  CHECK(tmc[CS_PINS[2]].reg.count(0x6C) && tmc[CS_PINS[2]].reg[0x6C] == 0x150100C3, "driver re-configured after a reset");

  tmc[CS_PINS[4]].present = false; tmc[CS_PINS[4]].reg[0x01] = 0x01; driverOk[4] = false;
  r = send("L");
  CHECK(r == "ERR no driver on face L\n", "missing driver reported instead of moving");

  printf("\n%s\n", failures ? "SOME CHECKS FAILED" : "all checks passed");
  return failures ? 1 : 0;
}
