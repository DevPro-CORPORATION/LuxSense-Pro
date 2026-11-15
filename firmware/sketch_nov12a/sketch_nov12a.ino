#include <Wire.h>
#include <BH1750.h>

BH1750 lightMeter;

// 16-byte Secret Key (Must match Python software exactly)
const byte SECRET_KEY[16] = {
  0x4A, 0x91, 0x2C, 0x7E, 0x10, 0xF3, 0x88, 0x5B, 
  0xD2, 0x64, 0x39, 0xA7, 0x05, 0xE1, 0x4F, 0xB8
};

bool isPaired = false;
uint16_t packetCounter = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin();
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
}

void loop() {
  // 1. Listen for Windows App Handshake
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "DISCOVER_LUX_SENSOR") {
      Serial.println("ID:GY30_LUX_PRO_2026");
      isPaired = true;
      packetCounter = 0;
    } else if (cmd == "DISCONNECT") {
      isPaired = false;
    }
  }

  // 2. Encrypt and Stream Data if Paired
  if (isPaired) {
    float lux = lightMeter.readLightLevel();
    if (lux < 0) lux = 0.0;
    packetCounter++;

    // Format payload: "COUNTER|LUX|CHECKSUM"
    long luxInt = (long)(lux * 100.0 + 0.5);
    int checksum = (packetCounter + luxInt) % 256;
    String payload = String(packetCounter) + "|" + String(lux, 2) + "|" + String(checksum);

    // Encrypt payload using rolling XOR cipher and send as HEX
    for (unsigned int i = 0; i < payload.length(); i++) {
      byte encryptedByte = payload[i] ^ SECRET_KEY[(i + packetCounter) % 16];
      if (encryptedByte < 16) Serial.print("0");
      Serial.print(encryptedByte, HEX);
    }
    Serial.println();
    delay(400);
  }
}
