# LuxSense Pro — Sensor Firmware & Hardware Architecture

## 1. Hardware Pinout Table

| Arduino Uno Pin | BH1750 / GY-30 Pin | Function | Recommended Wire Color |
|-----------------|--------------------|----------|------------------------|
| 5V (or 3.3V)    | VCC                | Regulated DC power | Red |
| GND             | GND                | Ground reference | Black |
| A4 (SDA)        | SDA                | I2C Serial Data | Blue |
| A5 (SCL)        | SCL                | I2C Serial Clock | Yellow |
| GND             | ADDR               | I2C Address Select (0x23) | Grey |

## 2. Wiring Schematic
```text
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

## 3. Communication Protocol & Telemetry Encryption
- **Baud Rate:** `115200` bps, 8 data bits, no parity, 1 stop bit (8N1).
- **Handshake Protocol:**
  - Workstation sends: `DISCOVER_LUX_SENSOR\n`
  - Arduino acknowledges: `ID:GY30_LUX_PRO_2026\n`
- **Rolling-128 XOR Cipher:**
  - Raw payload format: `[packet_counter]|[lux_value]|[checksum]`
  - Encrypted byte-wise: `payload[i] ^ SECRET_KEY[(i + packet_counter) % 16]`
  - Checksum equation: `(packet_counter + round(lux * 100)) % 256`
  - Prevents packet injection and guarantees transmission integrity.

## 4. Firmware Flashing Instructions
1. Open `firmware/LuxSense_Arduino/LuxSense_Arduino.ino` in Arduino IDE or compile via Arduino CLI.
2. Ensure the `BH1750` library by Christopher Laws is installed.
3. Select board **Arduino Uno** and your COM port.
4. Upload the sketch to the board.

