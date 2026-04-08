import serial

ser = serial.Serial('COM7', 115200, timeout=0.1)

ser.write(b'\x07')

while True:
    data = ser.readline()
    print(data)