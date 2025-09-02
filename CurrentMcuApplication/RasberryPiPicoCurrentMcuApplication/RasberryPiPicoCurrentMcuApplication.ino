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
    Serial.print("OS = ");
    Serial.println(getOsString(getOsValue(config)));
    Serial.print("MUX = ");
    Serial.println(getMuxString(getMuxValue(config)));
    Serial.print("PGA = ");
    Serial.println(getPgaString(getPgaValue(config)));
    Serial.print("MODE = ");
    Serial.println(getModeString(getModeValue(config)));
    Serial.print("DR = ");
    Serial.println(getDrString(getDrValue(config)));
    Serial.print("COMPMODE = ");
    Serial.println(getCompModeString(getCompModeValue(config)));
    Serial.print("COMPPOL = ");
    Serial.println(getCompPolString(getCompPolValue(config)));
    Serial.print("COMPLAT = ");
    Serial.println(getCompLatString(getCompLatValue(config)));
    Serial.print("COMPQUE = ");
    Serial.println(getCompQueString(getCompQueValue(config)));
  }
}


uint8_t getOsValue(uint16_t config)
{
  return (uint8_t)(config >> 15);
}

const char* getOsString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "0b:Device is currently performing";
    case 0b00000001:
      return "1b:Device is not currently performing";
    default:
      return "";
  }
}

uint8_t getMuxValue(uint16_t config)
{
    return (uint8_t)((config >> 12) & 0x7);
}

const char* getMuxString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "000b:AINP = AIN0 and AINN = AIN1 (default)";
    case 0b00000001:
      return "001b:AINP = AIN0 and AINN = AIN3";
    case 0b00000010:
      return "010b:AINP = AIN1 and AINN = AIN3";
    case 0b00000011:
      return "011b:AINP = AIN2 and AINN = AIN3";
    case 0b00000100:
      return "100b:AIN0 and AINN = GND";
    case 0b00000101:
      return "101b:AINP = AIN1 and AINN = GND";
    case 0b00000110:
      return "110b:AINP = AIN2 and AINN = GND";
    case 0b00000111:
      return "111b:AINP = AIN3 and AINN = GND";
    default:
      return "";
  }
}

uint8_t getPgaValue(uint16_t config)
{
    return (uint8_t)((config >> 9) & 0x7);
}


const char* getPgaString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "000b : FSR = ±6.144V";
    case 0b00000001:
      return "001b : FSR = ±4.096V";
    case 0b00000010:
      return "010b : FSR = ±2.048V (default)";
    case 0b00000011:
      return "011b : FSR = ±1.024V";
    case 0b00000100:
      return "100b : FSR = ±0.512V";
    case 0b00000101:
      return "101b : FSR = ±0.256V";
    case 0b00000110:
      return "110b : FSR = ±0.256V";
    case 0b00000111:
      return "111b : FSR = ±0.256V";
    default:
      return "";
  }
}

uint8_t getModeValue(uint16_t config)
{
    return (uint8_t)((config >> 8) & 0x1);
}

const char* getModeString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "0b:Continuous-conversion mode";
    case 0b00000001:
      return "1b:Single-shot mode or power-down state (default)";
    default:
      return "";
  }
}

uint8_t getDrValue(uint16_t config)
{
    return (uint8_t)((config >> 5) & 0x7);
}

const char* getDrString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "000b : 128SPS";
    case 0b00000001:
      return "001b : 250SPS";
    case 0b00000010:
      return "010b : 490SPS";
    case 0b00000011:
      return "011b : 920SPS";
    case 0b00000100:
      return "100b : 1600SPS (default)";
    case 0b00000101:
      return "101b : 2400SPS";
    case 0b00000110:
      return "110b : 3300SPS";
    case 0b00000111:
      return "111b : 3300SPS";
    default:
      return "";
  }
}

uint8_t getCompModeValue(uint16_t config)
{
    return (uint8_t)((config >> 4) & 0x1);
}

const char* getCompModeString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "0b : Traditional comparator (default)";
    case 0b00000001:
      return "1b : Window comparato";
    default:
      return "";
  }
}

uint8_t getCompPolValue(uint16_t config)
{
    return (uint8_t)((config >> 3) & 0x1);
}

const char* getCompPolString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "0b : Active low (default)";
    case 0b00000001:
      return "1b : Active high";
    default:
      return "";
  }
}

uint8_t getCompLatValue(uint16_t config)
{
    return (uint8_t)((config >> 2) & 0x1);
}

const char* getCompLatString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "0b : Nonlatching comparator . The ALERT/RDY pin does not latch when asserted(default)";
    case 0b00000001:
      return "1b : Latching comparator.";
    default:
      return "";
  }
}

uint8_t getCompQueValue(uint16_t config)
{
    return (uint8_t)(config & 0x3);
}

const char* getCompQueString(uint8_t value)
{
  switch(value)
  {
    case 0b00000000:
      return "00b : Assert after one conversion";
    case 0b00000001:
      return "01b : Assert after two conversions";
    case 0b00000010:
      return "10b : Assert after four conversions";
    case 0b00000011:
      return "11b : Disable comparator and set ALERT/RDY pin to high-impedance (default)";
    default:
      return "";
  }
}






void loop() {
  delay(1000);
}

