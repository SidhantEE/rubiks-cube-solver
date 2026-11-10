// Minimal stand-in for the Arduino/Teensy API so the firmware can be compiled
// and exercised on a computer. Time is simulated: every call to micros()
// advances the clock by one microsecond.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

#define HIGH 1
#define LOW 0
#define OUTPUT 1
#define HEX 16
using std::min;

struct StepEvent { uint64_t us; uint8_t pin; };
extern uint64_t simNowUs;
extern std::vector<StepEvent> simSteps;
extern std::map<uint8_t, int> simPinLevel;
extern int simSelectedCs;

inline void pinMode(uint8_t, uint8_t) {}
void digitalWrite(uint8_t pin, uint8_t level);
inline void digitalWriteFast(uint8_t pin, uint8_t level) { digitalWrite(pin, level); }
inline uint32_t micros() { return (uint32_t)(++simNowUs); }
inline uint32_t millis() { return (uint32_t)(simNowUs / 1000); }
inline void delay(uint32_t ms) { simNowUs += (uint64_t)ms * 1000; }
inline void delayMicroseconds(uint32_t us) { simNowUs += us; }
inline void delayNanoseconds(uint32_t) {}

struct SerialStub {
  std::string in, out;
  size_t pos = 0;
  void begin(long) {}
  int available() { return (int)(in.size() - pos); }
  char read() { return in[pos++]; }
  void print(const char *s) { out += s; }
  void print(char c) { out += c; }
  void print(unsigned long v, int base = 10) {
    char b[32]; snprintf(b, sizeof b, base == 16 ? "%lX" : "%lu", v); out += b;
  }
  void print(int v, int base = 10) { print((unsigned long)v, base); }
  void print(unsigned int v, int base = 10) { print((unsigned long)v, base); }
  void println() { out += "\n"; }
  template <class T> void println(T v) { print(v); out += "\n"; }
};
extern SerialStub Serial;
