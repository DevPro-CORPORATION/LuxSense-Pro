#include <Wire.h>
#include <BH1750.h>

// LuxSense Pro — Arduino Uno BH1750 Scientific Radiometry Firmware
// Features:
// - Dynamic dual-address auto-detection (0x23 for ADDR=GND, 0x5C for ADDR=VCC)
// - Continuous physical sensor health monitoring (I2C ACK verification)
// - 128-bit rolling XOR stream cipher with checksum verification matching crypto_packet.py
// - Explicit ERR:SENSOR_DISCONNECTED reporting upon physical I2C disconnection
// - Automatic hot-plug recovery upon physical sensor reconnection
// - Zero fabrication: never sends fake or masked 0.00 data on sensor error

BH1750 lightMeter;
byte sensorAddress = 0x23;
bool sensorDetected = false;
bool isPaired = false;
uint16_t packetCounter = 0;
unsigned long lastSample = 0;
const unsigned long SENSOR_INTERVAL_MS = 250; // 4.0 Hz acquisition rate

// 16-byte Secret Key (Must match Python software exactly)
const byte SECRET_KEY[16] = {
  0x4A, 0x91, 0x2C, 0x7E, 0x10, 0xF3, 0x88, 0x5B, 
  0xD2, 0x64, 0x39, 0xA7, 0x05, 0xE1, 0x4F, 0xB8
};

bool checkI2CAddress(byte addr) {
  Wire.beginTransmission(addr);
  byte error = Wire.endTransmission();
  return (error == 0);
}

bool probeSensor() {
  // Test primary address 0x23 (ADDR = GND)
  if (checkI2CAddress(0x23)) {
    sensorAddress = 0x23;
    sensorDetected = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23);
    return sensorDetected;
  }

  // Test secondary address 0x5C (ADDR = VCC)
  if (checkI2CAddress(0x5C)) {
    sensorAddress = 0x5C;
    sensorDetected = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C);
    return sensorDetected;
  }

  sensorDetected = false;
  return false;
}

void sendEncryptedPacket(float lux) {
  packetCounter++;

  // Exact round-to-hundredth integer representation matching crypto_packet.py
  unsigned long luxInt = (unsigned long)(lux * 100.0f + 0.5f);
  byte checksum = (byte)((packetCounter + luxInt) % 256);

  // Format payload: "COUNTER|LUX|CHECKSUM"
  String payload = String(packetCounter) + "|" + String(lux, 2) + "|" + String(checksum);

  // Encrypt payload using rolling XOR cipher and send as HEX
  for (unsigned int i = 0; i < payload.length(); i++) {
    byte encryptedByte = ((byte)payload[i]) ^ SECRET_KEY[(i + packetCounter) % 16];
    if (encryptedByte < 16) Serial.print('0');
    Serial.print(encryptedByte, HEX);
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(50);
  Wire.begin();
  Wire.setClock(400000L); // 400kHz Fast-Mode I2C

  probeSensor();
}

void loop() {
  // 1. Command handling
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "DISCOVER_LUX_SENSOR") {
      // Re-probe sensor on discovery
      probeSensor();
      if (sensorDetected) {
        Serial.print("ID:GY30_LUX_PRO_2026:ADDR_0x");
        if (sensorAddress < 16) Serial.print("0");
        Serial.println(sensorAddress, HEX);
        isPaired = true;
        packetCounter = 0;
        lastSample = millis();
      } else {
        Serial.println("ID:GY30_LUX_PRO_2026:NO_SENSOR");
        isPaired = false;
      }
    } else if (cmd == "DISCONNECT") {
      isPaired = false;
      Serial.println("DISCONNECTED");
    } else if (cmd == "PING") {
      Serial.println("PONG");
    } else if (cmd == "SENSOR_STATUS") {
      bool ok = checkI2CAddress(sensorAddress);
      Serial.print("SENSOR_OK:");
      Serial.println(ok ? "1" : "0");
    }
  }

  // 2. Continuous measurement streaming
  if (isPaired && millis() - lastSample >= SENSOR_INTERVAL_MS) {
    lastSample = millis();

    // Verify physical I2C connection before reading
    if (!checkI2CAddress(sensorAddress)) {
      sensorDetected = false;
      Serial.println("ERR:SENSOR_DISCONNECTED");
      // Attempt to re-probe in case address changed or reconnected
      probeSensor();
      return;
    }

    float lux = lightMeter.readLightLevel();

    // If reading returned negative or NaN, sensor communication failed
    if (isnan(lux) || lux < 0.0f) {
      sensorDetected = false;
      Serial.println("ERR:SENSOR_ERROR");
      return;
    }

    sensorDetected = true;
    sendEncryptedPacket(lux);
  }
}
