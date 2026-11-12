# LuxSense Pro — Sensor Firmware & Hardware Architecture

## Overview
The LuxSense Pro hardware subsystem couples an **Arduino Uno R3** microcontroller with a **BH1750 (GY-30)** digital ambient light sensor module over an I2C bus.

```
+--------------------+            I2C Bus            +--------------------+
|                    |  5V  ---------------------->  | VCC                |
|                    |  GND ---------------------->  | GND                |
|    Arduino Uno     |  A4 (SDA) <---------------->  | SDA   BH1750/GY-30 |
|    ATmega328P      |  A5 (SCL) ----------------->  | SCL                |
|                    |  GND ---------------------->  | ADDR (0x23)        |
+--------------------+                               +--------------------+
          |
          | USB Serial (115200 Baud)
          v
+--------------------+
|  Host Workstation  |
|  LuxSense Pro App  |
+--------------------+
```

## Pin Connection Table
| Arduino Uno Pin | BH1750 Pin | Description |
|-----------------|------------|-------------|
| 5V / 3.3V       | VCC        | Regulated Power Supply |
| GND             | GND        | Ground reference |
| A4 (or SDA pin) | SDA        | I2C Serial Data line |
| A5 (or SCL pin) | SCL        | I2C Serial Clock line |
| GND             | ADDR       | I2C Address Select (Low = 0x23, High = 0x5C) |

## Firmware Characteristics
- **Baud Rate:** `115200` bps
- **Handshake Protocol:** Bidirectional sync (`DISCOVER_LUX_SENSOR` -> `ID:GY30_LUX_PRO_2026`)
- **Sampling Interval:** 400 ms (2.5 Hz continuous high-resolution mode)
- **Encryption:** 128-bit rolling-key XOR cipher (`SECRET_KEY[16]`) with 8-bit modular checksum verification.
