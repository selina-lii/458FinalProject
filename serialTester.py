import serial
import time
import threading

arduino = serial.Serial(port='COM7', baudrate=115200, timeout=.1)

debugCounter = 0
# 10 second buffer, can change later
buffer = [[None]*5]*10000
bufferPtr = 0
quit = False

# Constantly checks if the buffer has more than 1000 samples
# Grabs 1000 samples to do analysis on when available
def dataAnalysis():
    dataBufferPtr = 0
    while True:
        if quit == True: break
        #print(dataBufferPtr)
        if abs(bufferPtr - dataBufferPtr) >= 1000:
            dataBufferPtr = dataBufferPtr + 1000
            if dataBufferPtr >= len(buffer):
                dataBufferPtr = 0
            print("Grabbed one second of data")


#t = threading.Thread(target=dataAnalysis)
#t.start()
startTime = time.time()

try:
    while True:
        data = arduino.readline()
        if data != None:
            splitData = [data[i:i+2] for i in range(0,10,2)]
            intData = [0] * 5
            for i in range(5):
                intData[i] = int.from_bytes(splitData[i], "little")
            # Debug Print
            print(intData,bufferPtr)
            buffer[bufferPtr] = intData
            bufferPtr = bufferPtr+1
            if bufferPtr >= len(buffer):
                bufferPtr = 0
except KeyboardInterrupt:
    print("Terminating")
    quit = True
