const float V_REF = 5.0;
const float R_BITS = 10.0;
const float ADC_STEPS = (1 << int(R_BITS)) - 1;

void setup() {
  // put your setup code here, to run once:
  // Five inputs
  // Pin A0 for EMG lead 1
  // Pin A1 for EMG lead 2
  // Pin A2 for EOG lead 1
  // Pin A3 for EOG lead 2
  // Pin A4 for EOG lead 3
  pinMode(A0, INPUT);
  pinMode(A1, INPUT);
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A4, INPUT);
  Serial.begin(115200);
  Serial.setTimeout(1);
}

void loop() {
  int startTime = micros();
  // put your main code here, to run repeatedly:
  int val0 = random(200,299);//analogRead(A0)
  int val1 = random(300,399);//analogRead(A1)
  int val2 = random(400,499);//;analogRead(A2)
  int val3 = random(500,599);//analogRead(A3)
  int val4 = random(600,699);//analogRead(A4)
  //Serial.println(Serial.availableForWrite());
  if(Serial.availableForWrite() > 11){
    int buf[] = {val0, val1, val2, val3, val4};
    //Serial.println(sizeof(buf));
    byte *p = reinterpret_cast<byte*>(buf);
    Serial.write(p,10);
    //Serial.print(val0);
    //Serial.print(",");
    //Serial.print(val1);
    //Serial.print(",");
    //Serial.print(val2);
    //Serial.print(",");
    //Serial.print(val3);
    //Serial.print(",");
    //Serial.print(val4);
    Serial.print("\n");
  }
  //Enforces 1000 Hz sampling rate
  //1000 microseconds in one second
  delayMicroseconds(1000-(micros()-startTime));
}
