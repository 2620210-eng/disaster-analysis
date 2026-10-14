#include <Servo.h>
#include <Adafruit_NeoPixel.h>
#include <avr/wdt.h> // 하드웨어 강제 리셋용

// 핀 번호 설정
const int TRIG_PIN = 2;        // 초음파 Trig (D2)
const int ECHO_PIN = 3;        // 초음파 Echo (D3)
const int BUZZER_PIN = 4;      // 부저 (D4)
const int SERVO_PIN = 5;       // 서보모터 (D5)
const int NEOPIXEL_PIN = 6;    // 네오픽셀 (D6)
const int PUMP_PIN = 7;        // 모터 릴레이 (D7)
const int VIB_PIN = A0;        // 진동 센서 (A0)

const int NUM_PIXELS = 4;      // LED 개수

// 1. 산사태/지진 감지 민감도 (15: 미세한 진동에도 즉시 반응)
const int VIB_THRESHOLD = 15; 

// 2. 초음파 센서 보정값 (1.5cm 차감)
const float DISTANCE_OFFSET = 1.5; 

// 3. 타이머 변수 (3초 주기 초음파 측정)
unsigned long lastDistanceTime = 0;
float currentDistance = 999.0;

Servo barrierServo;
Adafruit_NeoPixel strip(NUM_PIXELS, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

void setSinglePixel(int pixelIndex, uint32_t color) {
  strip.clear();
  strip.setPixelColor(pixelIndex, color);
  strip.show();
}

void setPixelColorAll(uint32_t color) {
  for(int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, color);
  }
  strip.show();
}

// 하드웨어 강제 재부팅 함수
void hardReset() {
  wdt_enable(WDTO_15MS); // 15ms 후 강제 리셋
  while (1) {} 
}

// 초음파 거리 측정 함수
float readDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  float rawDistance = duration * 0.034 / 2;
  float dist = rawDistance - DISTANCE_OFFSET;
  return (dist < 0) ? 0 : dist;
}

void setup() {
  wdt_disable(); // 부팅 시 워치독 해제
  
  Serial.begin(9600);
  
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  
  digitalWrite(PUMP_PIN, LOW);

  barrierServo.attach(SERVO_PIN);
  barrierServo.write(0); // 차단막 열림
  noTone(BUZZER_PIN);

  strip.begin();
  strip.setBrightness(30);
  
  // 부팅 초기화 표시 (흰색 LED 1초)
  setPixelColorAll(strip.Color(255, 255, 255));
  delay(1000);
  strip.clear();
  strip.show();

  // 첫 거리 측정
  currentDistance = readDistance();
  lastDistanceTime = millis();

  delay(1000); 
}

void loop() {
  unsigned long currentTime = millis();

  // 초음파 센서: 정확히 3초(3000ms)마다 1번씩만 측정
  if (currentTime - lastDistanceTime >= 3000) {
    currentDistance = readDistance();
    lastDistanceTime = currentTime;
  }

  // 진동 센서: 실시간 감지
  int vibVal = analogRead(VIB_PIN);

  // 시리얼 출력 (파이썬 관제용)
  Serial.print(currentDistance);
  Serial.print(",");
  Serial.println(vibVal);

  // 1. [🔴 산사태/지진 발생 감지]
  if (vibVal > VIB_THRESHOLD) {
    barrierServo.write(90);                    
    setPixelColorAll(strip.Color(255, 0, 0));  
    digitalWrite(PUMP_PIN, LOW);               
    tone(BUZZER_PIN, 1000);                    
    
    delay(5000); // 5초 경보
    
    noTone(BUZZER_PIN);                        
    barrierServo.write(0);                     
    
    delay(1000);
    hardReset(); // 경보 후 완전 초기화
  }

  // 2. [🔴 침수 심각 단계] (11.0cm 이하)
  if (currentDistance > 0.5 && currentDistance <= 11.0) {
    setSinglePixel(0, strip.Color(255, 0, 0)); 
    barrierServo.write(90);                     
    digitalWrite(PUMP_PIN, HIGH);              
    tone(BUZZER_PIN, 1000);                    
    
    delay(5000); // 5초 경보 및 펌프 가동
    
    digitalWrite(PUMP_PIN, LOW);               
    noTone(BUZZER_PIN);                        
    barrierServo.write(0);                     
    
    delay(1000);
    hardReset(); // 경보 후 완전 초기화
  } 

  // 3. [🟢🟡🟠⚪ 일반 수위 단계]
  digitalWrite(PUMP_PIN, LOW);
  noTone(BUZZER_PIN);

  if (currentDistance > 11.0 && currentDistance <= 13.0) {
    setSinglePixel(1, strip.Color(255, 100, 0)); // 주황색
    barrierServo.write(0);
  } 
  else if (currentDistance > 13.0 && currentDistance <= 15.0) {
    setSinglePixel(2, strip.Color(255, 200, 0)); // 노란색
    barrierServo.write(0);
  } 
  else if (currentDistance > 15.0) {
    setSinglePixel(3, strip.Color(0, 255, 0)); // 초록색
    barrierServo.write(0);
  }
  else {
    setSinglePixel(0, strip.Color(255, 255, 255)); // 흰색 (미감지/오류)
    barrierServo.write(0);
  }

  delay(100); 
}
