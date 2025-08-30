#include <Wire.h>

#define ADS1105_ADDR 0x48  // ADDR=GND の場合

void setup() {
  Serial.begin(115200);
  Wire.begin(); // SDA=GP4, SCL=GP5 (Picoでは自動割り当てされます)

  delay(1000);
  Serial.println("ADS1105 test start");

  // Configレジスタ (0x01) を読んでみる
  Wire.beginTransmission(ADS1105_ADDR);
  Wire.write(0x01); // Config register
  if (Wire.endTransmission(false) != 0) {
    Serial.println("ADS1105 not found!");
    while (1);
  }

  Wire.requestFrom(ADS1105_ADDR, 2);
  if (Wire.available() == 2) {
    uint16_t config = (Wire.read() << 8) | Wire.read();
    Serial.print("ADS1105 Config Reg = 0x");
    Serial.println(config, HEX);
  } else {
    Serial.println("Read error");
  }
}

void loop() {
  delay(1000);
}

