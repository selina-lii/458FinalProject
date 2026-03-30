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
  //Want a sampling rate of 1000 samples/s
  //Each sample is 11 bytes including the newline character
  //That gives us a bitrate of 88 *1000 bits/s
  Serial.begin(88000);
  Serial.setTimeout(1);
}

void loop() {
  // put your main code here, to run repeatedly:
  int val0 = 200;//analogRead(A0)
  int val1 = 300;//analogRead(A1)
  int val2 = 400;//;analogRead(A2)
  int val3 = 500;//analogRead(A3)
  int val4 = 600;//analogRead(A4)
  //Serial.println(Serial.availableForWrite());
  if(Serial.availableForWrite() > 11){
    int buf[] = {val0, val1, val2, val3, val4};
    //Serial.println(sizeof(buf));
    byte *p = reinterpret_cast<byte*>(buf);
    Serial.write(p, 10);
    Serial.write('\n');
  }
}
