import serial

ser = serial.Serial('COM7', 115200, timeout=0.1)

ser.write(b'\x08')

# while True:
#     data = ser.readline()
#     print(data)