#include <Wire.h>

#define ADS1105_ADDR 0x48  // ADDR=GND の場合

void setup() {
  uint16_t config;
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
    config = (Wire.read() << 8) | Wire.read();
    Serial.print("ADS1105 Config Reg = 0x");
    Serial.println(config, HEX);
  } else {
    Serial.println("Read error");
  }

  {
    uint8_t muxValue = (config >> 12) & 0x7;
    Serial.print("MUX = ");
    Serial.println(getMuxString(muxValue));
  }
}

const char* getMuxString(uint8_t mux)
{
  switch(mux)
  {
    case 0b00000000:
      return "AINP = AIN0 and AINN = AIN1 (default)";
    case 0b00000001:
      return "AINP = AIN0 and AINN = AIN3";
    case 0b00000010:
      return "AINP = AIN1 and AINN = AIN3";
    case 0b00000011:
      return "AINP = AIN2 and AINN = AIN3";
    case 0b00000100:
      return "AIN0 and AINN = GND";
    case 0b00000101:
      return "AINP = AIN1 and AINN = GND";
    case 0b00000110:
      return " AINP = AIN2 and AINN = GND";
    case 0b00000111:
      return " AINP = AIN3 and AINN = GND";
    default:
      return "";

  }
}

void loop() {
  delay(1000);
}

