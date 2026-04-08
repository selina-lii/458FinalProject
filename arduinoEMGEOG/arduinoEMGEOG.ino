const float V_REF = 5.0;
const float R_BITS = 10.0;
const float ADC_STEPS = (1 << int(R_BITS)) - 1;
const int buzzer = 0;
int mode = 0;
int buzzStartTime = 0;
int beepCount = 0;
bool isBuzzing = false;

void setup() {
  // put your setup code here, to run once:
  // Five inputs
  // Pin A0 for EMG
  // Pin A1 for EOG lead 1
  // Pin A2 for EOG lead 2
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  //pinMode(A3, INPUT);
  //pinMode(A4, INPUT);
  pinMode(buzzer, OUTPUT);
  Serial.begin(115200);
  Serial.setTimeout(1);
}

void loop() {
  int startTime = micros();
  // put your main code here, to run repeatedly:
  //int val0 = random(0,100);
  int val0 = analogRead(A0);
  //int val1 = random(0,100);
  int val1 = analogRead(A1);
  //int val2 = random(0,100);
  int val2 = analogRead(A2);
  //int val3 = random(0,100);
  //analogRead(A3);
  //int val4 = random(0,100);
  //analogRead(A4);
  //Serial.println(Serial.availableForWrite());
  if(Serial.availableForWrite() > 11){
    int buf[] = {val0, val1, val2};
    //Serial.println(sizeof(buf));
    byte *p = reinterpret_cast<byte*>(buf);
    //Serial.write(p,6);
    //Serial.print("\n");
  }
  if(Serial.available()){
    byte b = Serial.read();
    if(b == byte{7} && !mode){
      //Stressed = b07
      mode = 7;
      buzzStartTime = millis();
      digitalWrite(buzzer,HIGH);
      delay(1);
      //Serial.println("Saw 7");
    }else if(b == byte{8} && !mode){
      //Not alert = b08
      mode = 8;
      buzzStartTime = millis();
      beepCount = 1;
      isBuzzing = true;
      digitalWrite(buzzer,HIGH);
      delay(1);
      //Serial.println("Saw 8");
    }
  }
  //1 second tone
  if(mode == 7 && millis()-buzzStartTime >= 1000){
    digitalWrite(buzzer,LOW);
    mode = 0;
    //Serial.println("Turn Off");
  //three 0.5 second tones
  }else if(mode == 8 && millis()-buzzStartTime >= 100){
    if(isBuzzing){
      digitalWrite(buzzer,LOW);
    }else{
      digitalWrite(buzzer,HIGH);
      beepCount = beepCount + 1;
    }
    isBuzzing = !isBuzzing;
    buzzStartTime = millis();
    if(beepCount > 3){
      mode = 0;
      beepCount = 0;
      digitalWrite(buzzer,LOW);
    }
    //Serial.println("Turn Off");
  }
  //Enforces 1000 Hz sampling rate
  //1000 microseconds in one second
  delayMicroseconds(1000-(micros()-startTime));
}
