import asyncio, serial, time
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random

WINDOW = 2
V_REF = 5.0
R_BITS = 10
ADC_STEPS = (2**R_BITS) - 1

buf = []

y_range = [-5,5]
x_range = [0,100]
x_len = 100

fig = plt.figure(figsize=(7,3.5))
ax = fig.add_subplot(111)
ax.set_ylim(y_range)
ax.set_xlim(x_range)
plt.subplots_adjust(bottom=0.20)
xs = [0]
ys = [[0,0,0,0,0]]

line = ax.plot(xs,ys)

def preprocess(samples):
    # First two values are EMG, last three values are EOG
    arr = np.array(samples)
    # Band Pass EOG and EMG
    
    # Notch Filter EMG
    
    return arr

def classify(features):
    return 1

# ── async pipeline ───────────────────────────────────────────────
async def main():
    print("I'm in main")
    #ser = serial.Serial('COM7', 115200, timeout=0)

    async def read():
        global xs,ys,fig
        while True:
            #if ser.in_waiting:
                try:
                    #data = ser.readline()
                    #splitData = [data[i:i+2] for i in range(0,10,2)]
                    #intData = [0.0] * 5
                    #for i in range(5):
                    #    # Turn ints into voltage values
                    #    intData[i] = (int.from_bytes(splitData[i], "little")/ADC_STEPS) * V_REF
                    intData = [random.randrange(-5,5),
                               random.randrange(-5,5),
                               random.randrange(-5,5),
                               random.randrange(-5,5),
                               random.randrange(-5,5)]
                    buf.append(intData)
                    #print(intData)
                except Exception as e:
                    print(e)
                    pass
                
                # Plotting part
                timestamp = xs[-1]+1
                data_sample = intData
                if len(xs) < x_len:
                    xs.append(timestamp % x_len)
                    xs = xs[-x_len:]
    
                ys.append(data_sample)
    
                ys = ys[-x_len:]
    
                #print(len(xs))
                #print(xs)
                plt.cla()
                ax.plot(xs,ys)
                ax.set_xlim(x_range)
                plt.pause(0.01)
                if not plt.fignum_exists(fig.number):
                    break
                await asyncio.sleep(0)

    async def process():
        timeToSleep = WINDOW
        while True:
            await asyncio.sleep(timeToSleep)
            startTime = time.time()
            if buf:
                snap, buf[:] = buf[:], []
                print(f"n={len(snap)}, result={classify(preprocess(snap))}, time elapsed={time.time()-startTime}")
            timeToSleep = WINDOW - (time.time()-startTime)
            
    await asyncio.gather(read(), process())

print("Started Running")
plt.ion()
plt.show()
asyncio.run(main())