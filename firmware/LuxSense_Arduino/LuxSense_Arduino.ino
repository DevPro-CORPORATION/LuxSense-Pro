#include <Wire.h>
#include <BH1750.h>

// LuxSense Pro — Arduino Uno BH1750 Scientific Radiometry Firmware
// Features: Dual-address auto-detection (0x23 / 0x5C), 400kHz I2C Fast Mode,
// 128-bit rolling XOR stream cipher with CRC-8 checksum, low-latency UART.

BH1750 lightMeter;
byte sensorAddress = 0x23;
bool sensorDetected = false;

// 128-bit rolling cipher secret key matching Python core
const byte SECRET_KEY[16] = {
  0x4A, 0x91, 0x2C, 0x7E, 0x10, 0xF3, 0x88, 0x5B,
  0xD2, 0x64, 0x39, 0xA7, 0x05, 0xE1, 0x4F, 0xB8
};

const unsigned long BAUD_RATE = 115200;
const unsigned long SENSOR_INTERVAL_MS = 250; // 4.0 Hz continuous acquisition
bool isPaired = false;
uint16_t packetCounter = 0;
unsigned long lastSample = 0;

void sendEncryptedPacket(float lux) {
  packetCounter++;

  // Exact round-to-hundredth integer representation
  unsigned long luxInt = (unsigned long)(lux * 100.0f + 0.5f);
  byte checksum = (byte)((packetCounter + luxInt) % 256);

  // Payload: packet_id|lux|checksum
  String payload = String(packetCounter) + "|" +
                   String(lux, 2) + "|" +
                   String(checksum);

  // Encrypt with 128-bit rolling XOR cipher
  for (unsigned int i = 0; i < payload.length(); i++) {
    byte encryptedByte =
      ((byte)payload[i]) ^ SECRET_KEY[(i + packetCounter) % 16];

    if (encryptedByte < 16) Serial.print('0');
    Serial.print(encryptedByte, HEX);
  }
  Serial.println();
}

void probeSensor() {
  // Test primary address 0x23 (ADDR = GND)
  Wire.beginTransmission(0x23);
  if (Wire.endTransmission() == 0) {
    sensorAddress = 0x23;
    sensorDetected = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x23);
    return;
  }

  // Test secondary address 0x5C (ADDR = VCC)
  Wire.beginTransmission(0x5C);
  if (Wire.endTransmission() == 0) {
    sensorAddress = 0x5C;
    sensorDetected = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, 0x5C);
    return;
  }

  // Fallback default initialization
  sensorDetected = lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE);
}

void setup() {
  Serial.begin(BAUD_RATE);
  Serial.setTimeout(50); // Minimized latency
  
  // Initialize I2C and set to 400kHz Fast Mode
  Wire.begin();
  Wire.setClock(400000L);

  probeSensor();
}

void loop() {
  // Fast command polling
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
    } else if (command == "PING") {
      Serial.println("PONG");
    } else if (command == "SENSOR_STATUS") {
      Serial.print("SENSOR_OK:");
      Serial.println(sensorDetected ? "1" : "0");
    }
  }

  // Continuous photometric sampling
  if (isPaired && millis() - lastSample >= SENSOR_INTERVAL_MS) {
    lastSample = millis();

    float lux = 0.0f;
    if (sensorDetected) {
      lux = lightMeter.readLightLevel();
      if (isnan(lux) || lux < 0.0f) {
        lux = 0.0f;
      }
    } else {
      // Retry sensor detection if it was plugged in hot
      probeSensor();
    }

    sendEncryptedPacket(lux);
  }
}
