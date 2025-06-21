/*
*******************************************************************************
* Copyright (c) 2023 by M5Stack
*                  Equipped with M5StickC sample source code
*                          配套  M5StickC 示例源代码
* Visit for more information: https://docs.m5stack.com/en/core/m5stickc
* 获取更多资料请访问: https://docs.m5stack.com/zh_CN/core/m5stickc
*
* Describe: Button.
* Date: 2021/11/16
*******************************************************************************
*/
#include <M5StickC.h>

#define CONTINUOUSLY_H_RESOLUTION_MODE  B00010000

uint16_t value1;
uint16_t value2;
uint16_t value3;

unsigned long loopStartTime = 0;

/* After M5StickC is started or reset
  the program in the setUp () function will be run, and this part will only be
  run once. 在 M5StickC
  启动或者复位后，即会开始执行setup()函数中的程序，该部分只会执行一次。 */
void setup() {
    M5.begin();  // Initialize the M5StickC object.  初始化 M5StickC 对象
    Serial1.begin(9600,SERIAL_8N1,0,26);
    Wire.begin();  // Init wire and join the I2C network.
    Wire.setClock(400000);
    M5.Lcd.setTextColor(
        YELLOW);  // Set the font color to yellow.  设置字体颜色为黄色
    M5.Lcd.setRotation(3);
    
    delay(3000); // 少しだけ画面
// #define CONTINUOUSLY_H_RESOLUTION_MODE  B00010000を表示しておく
    selectChannel(0);
    setMode(0x23,CONTINUOUSLY_H_RESOLUTION_MODE);
    selectChannel(1);
    setMode(0x23,CONTINUOUSLY_H_RESOLUTION_MODE);
    selectChannel(2);
    setMode(0x23,CONTINUOUSLY_H_RESOLUTION_MODE);
    loopStartTime = micros();
}

/* After the program in setup() runs, it runs the program in loop()
The loop() function is an infinite loop in which the program runs repeatedly
在setup()函数中的程序执行完后，会接着执行loop()函数中的程序
loop()函数是一个死循环，其中的程序会不断的重复运行 */
void loop() {
  // 1病経過したら、計測して送信する
  if(labs(micros() - loopStartTime) > 60000000) // 1分に一回
  {
    loopStartTime = micros();
    measureLUX(); // 電流の測定
    sendCurrent();
  }
}

void measureLUX()
{
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.print("measure:start");
  Serial.print("measure:start");
  selectChannel(0);
  value1 = getLUX(0x23);
  selectChannel(1);
  value2 = getLUX(0x23);
  selectChannel(2);
  value3 = getLUX(0x23);
  M5.Lcd.println("end");
  Serial.println("end");
  M5.Lcd.setTextSize(3);
  M5.Lcd.setTextColor(RED);
  M5.Lcd.print("DLT1:");
  Serial.print("DLT1:");
  M5.Lcd.println(value1);
  Serial.println(value1);
  M5.Lcd.print("DLT2:");
  Serial.print("DLT2:");
  M5.Lcd.println(value2);
  Serial.println(value2);
  M5.Lcd.print("DLT3:");
  Serial.print("DLT3:");
  M5.Lcd.println(value3);
  Serial.println(value3);
}

void sendCurrent()
{
  Serial1.write(0x00); // アドレス上位
  Serial1.write(0x00); // アドレス下位
  Serial1.write(0x01); // チャンネル
  Serial1.write('D'); // コマンド

  Serial1.write((uint8_t)((value1 >> 8) & 0xFF));
  Serial1.write((uint8_t)(value1 & 0xFF));
  Serial1.write((uint8_t)((value2 >> 8) & 0xFF));
  Serial1.write((uint8_t)(value2 & 0xFF));
  Serial1.write((uint8_t)((value3 >> 8) & 0xFF));
  Serial1.write((uint8_t)(value3 & 0xFF));
  Serial1.write("\r\n");

}

void writeByte(uint8_t addr,byte cmd) {
    Wire.beginTransmission(addr);
    Wire.write(cmd);
    Wire.endTransmission();
}

void setMode(uint8_t addr,byte mode) {
    writeByte(addr,mode);
}

uint16_t getLUX(uint8_t addr) {
    uint16_t lux;
    uint8_t buffer[2];
    readBytes(addr,buffer, 2);
    lux = buffer[0] << 8 | buffer[1];
    return lux / 1.2;
}

void readBytes(uint8_t addr,uint8_t *buffer, size_t size) {
    Wire.requestFrom(addr, size);
    for (uint16_t i = 0; i < size; i++) {
        buffer[i] = Wire.read();
    }
}

#define MUX_ADDR 0x70  // PCA9548のI2Cアドレス（A0～A2によって変わる）

void selectChannel(uint8_t channel) {
  if (channel > 7) return; // 最大8チャンネル
  Wire.beginTransmission(0x70);
  Wire.write(1 << channel); // 指定チャネルを有効化
  Wire.endTransmission();
}
