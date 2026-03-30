import serial
import time

arduino = serial.Serial(port='COM7', baudrate=88000, timeout=.1)

while True:
    data = arduino.readline()
    if data != None:
        splitData = [data[i:i+2] for i in range(0,10,2)]
        intData = [0] * 5
        for i in range(5):
            intData[i] = int.from_bytes(splitData[i], "little")
        print(intData)
