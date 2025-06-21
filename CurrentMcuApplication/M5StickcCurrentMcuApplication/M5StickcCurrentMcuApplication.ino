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
#include <ADS1X15.h>

ADS1015 ADS(0x48);

#define SAMPLING_COUNT 500
float voltageBuffer[SAMPLING_COUNT] = { 0.0 };
float currentBuffer[SAMPLING_COUNT] = { 0.0 };
float Goukeichi = 0.0;
float minusBunMizumashi = 0.0;
float jikkouchi = 0.0;
unsigned long measureStartTime = 0;
unsigned long measureEndTime = 0;

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
    M5.Lcd.println(
        "Button example");  // The screen prints the formatted string and wraps
                            // the line.  输出格式化字符串并换行
    M5.Lcd.println("Press button B for 700ms");
    M5.Lcd.println("to clear screen.");

    if(!ADS.begin())
    {
      M5.Lcd.setTextColor(RED);
      M5.Lcd.println("ADS1015 is NOT found");

    }
    else
    {
      M5.Lcd.setTextColor(GREEN);
      M5.Lcd.println("ADS1015 is FOUND");
    }

    if(!ADS.isConnected())
    {
      M5.Lcd.setTextColor(RED);
      M5.Lcd.println("ADS1015 is NOT found");
    }
    else
    {
      M5.Lcd.setTextColor(GREEN);
      M5.Lcd.println("ADS1015 is FOUND");
    }
    
    delay(3000); // 少しだけ画面を表示しておく
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
    measureCurrent(); // 電流の測定
    sendCurrent();
  }
}

void sendCurrent()
{
  char currentChar[16] = {0};
  dtostrf(jikkouchi,8,6,currentChar);

  Serial1.write(0x00); // アドレス上位
  Serial1.write(0x00); // アドレス下位
  Serial1.write(0x01); // チャンネル
  Serial1.write('C'); // コマンド
  Serial1.write(currentChar);
  Serial1.write("\r\n");

}

void measureCurrent()
{
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.print("measure:start");
  Serial.print("measure:start");
  measureStartTime = micros(); // 計測開始時間
  for(int loop_count = 0;loop_count < SAMPLING_COUNT;loop_count++) // サンプリング数分だけ連続ADS1105に対して連続読み取り
  {
    ADS.setGain(0);
    int val_0 = ADS.readADC(); //pin0
    float f= ADS.toVoltage(1);
    voltageBuffer[loop_count] = val_0 * f; //pin0からI2C経由で値を読み取り、電圧値に変換したものを配列格納
  }
  measureEndTime = micros(); // 計測終了時間
  M5.Lcd.println("end");
  Serial.println("end");

  M5.Lcd.print("calc:start");
  Serial.print("calc:start");
  calcJikkouchi();
  M5.Lcd.println("end");
  Serial.println("end");
  M5.Lcd.print("print:start");
  Serial.print("print:start");
  printValue();
  M5.Lcd.println("end");
  Serial.println("end");
  Serial.println("");
  M5.Lcd.setTextSize(3);
  M5.Lcd.setTextColor(RED);
  M5.Lcd.print(jikkouchi,6);
}

void calcJikkouchi()
{
  Goukeichi = 0;
  minusBunMizumashi = 0;
  jikkouchi = 0;


  for(int loop_count = 0;loop_count < SAMPLING_COUNT;loop_count++) // サンプリング数分だけ連続ADS1105に対して連続読み取り
  {
    if(voltageBuffer[loop_count] > 0.0){
      currentBuffer[loop_count] = ConvertVoltageToCurrentOn100ohm(voltageBuffer[loop_count]);
    }
    else
    {
      currentBuffer[loop_count] = 0.0;
    }

    Goukeichi += pow(currentBuffer[loop_count],2);
  }

  minusBunMizumashi = Goukeichi * 2.0;

  // 実効値を求める
  jikkouchi = sqrt(minusBunMizumashi / SAMPLING_COUNT);
}

float ConvertVoltageToCurrentOn100ohm(float voltage)
{
  // V変換 + 係数
  return 0.0275 * pow(fabs(voltage * 1000), 0.996);
}

void printValue()
{
  unsigned long measureAllTime = measureEndTime - measureStartTime;
  Serial.print("measureAllTime: ");
  Serial.print(measureAllTime);
  Serial.println(" us");
  Serial.print("measureSampleTime: ");
  Serial.print(measureAllTime / SAMPLING_COUNT);
  Serial.println(" us");
  for(int loop_count = 0;loop_count < SAMPLING_COUNT;loop_count++)
  {
    Serial.print(voltageBuffer[loop_count],6);
    Serial.print(" ");
    Serial.println(currentBuffer[loop_count],6);
  }
  Serial.print("Goukeichi:");
  Serial.println(Goukeichi,6);
  Serial.print("minusBunMizumashi:");
  Serial.println(minusBunMizumashi,6);
  Serial.print("jikkouchi:");
  Serial.println(jikkouchi,6);
}