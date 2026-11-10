// Stand-in SPI bus with six simulated TMC5160 drivers behind it.
#pragma once
#include "Arduino.h"
#define MSBFIRST 1
#define SPI_MODE3 3
struct SPISettings { SPISettings(uint32_t, int, int) {} };
struct SPIStub {
  void begin() {}
  void beginTransaction(const SPISettings &) {}
  void endTransaction() {}
  uint8_t transfer(uint8_t b);
};
extern SPIStub SPI;
