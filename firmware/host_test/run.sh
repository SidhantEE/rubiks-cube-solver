#!/bin/sh
# Builds the firmware against a stand-in Arduino API and runs it on this computer.
set -e
cd "$(dirname "$0")"
c++ -std=c++17 -Wall -Wextra -Wno-unused-parameter -I. -x c++ test_main.cpp -o /tmp/cube_fw_test
/tmp/cube_fw_test
