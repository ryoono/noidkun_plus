#include <Servo.h>

Servo myServo;
const int servoPin = 7;
const int defaultAngle = 15;
const int activeAngle = 70;
const int activeDuration = 2000; // 2秒（ミリ秒）

void setup() {
  Serial.begin(9600);       // シリアル通信開始（9600bps）
  myServo.attach(servoPin); // サーボを3番ピンに接続
  myServo.write(defaultAngle);  // 初期角度は20度
}

void loop() {
  if (Serial.available() > 0) {
    char received = Serial.read();
    if (received == 'D') {
      activateServo();
    }
  }
}

void activateServo() {
  myServo.write(activeAngle);       // 70度に動かす
  delay(activeDuration);            // 2秒間待機
  myServo.write(defaultAngle);      // 元の15度に戻す
}
