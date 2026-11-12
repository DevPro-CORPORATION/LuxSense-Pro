#include <Wire.h>
#include <BH1750.h>

BH1750 lightMeter;

const byte SECRET_KEY[16] = {
  0x4A, 0x91, 0x2C, 0x7E, 0x10, 0xF3, 0x88, 0x5B,
  0xD2, 0x64, 0x39, 0xA7, 0x05, 0xE1, 0x4F, 0xB8
};

const unsigned long BAUD_RATE = 115200;
const unsigned long SENSOR_INTERVAL_MS = 400;
bool isPaired = false;
uint16_t packetCounter = 0;
unsigned long lastSample = 0;

void sendEncryptedPacket(float lux) {
  packetCounter++;

  // Match Python's positive-value rounding exactly.
  unsigned long luxInt = (unsigned long)(lux * 100.0f + 0.5f);
  byte checksum = (byte)((packetCounter + luxInt) % 256);

  String payload = String(packetCounter) + "|" +
                   String(lux, 2) + "|" +
                   String(checksum);

  for (unsigned int i = 0; i < payload.length(); i++) {
    byte encryptedByte =
      ((byte)payload[i]) ^ SECRET_KEY[(i + packetCounter) % 16];

    if (encryptedByte < 16) Serial.print('0');
    Serial.print(encryptedByte, HEX);
  }
  Serial.println();
}

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.setTimeout(100);
  Wire.begin();

  // Start the sensor. If initialization fails, the app will still
  // complete the serial handshake and display zero until it is fixed.
  lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
}

void loop() {
  // Handle commands before sending sensor data.
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "DISCOVER_LUX_SENSOR") {
      isPaired = true;
      packetCounter = 0;
      Serial.println("ID:GY30_LUX_PRO_2026");
      lastSample = millis();
    } else if (command == "DISCONNECT") {
      isPaired = false;
      Serial.println("DISCONNECTED");
    }
  }

  if (isPaired && millis() - lastSample >= SENSOR_INTERVAL_MS) {
    lastSample = millis();

    float lux = lightMeter.readLightLevel();
    if (isnan(lux) || lux < 0.0f) {
      lux = 0.0f;
    }

    sendEncryptedPacket(lux);
  }
}
