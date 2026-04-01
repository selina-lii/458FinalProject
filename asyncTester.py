import asyncio, serial, time
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation


WINDOW = 2
V_REF = 5.0
R_BITS = 10
ADC_STEPS = (2**R_BITS) - 1

buf = []

y_range = [-5,5]
x_len = 1000

fig = plt.figure(figsize=(14,7))
ax = fig.add_subplot(1,1,1)
ax.set_ylim(y_range)
plt.subplots_adjust(bottom=0.20)
xs = [0]
ys = [None]

line = ax.plot(xs,ys,color='#33ebff')

def animate(frame,xs,ys):
    timestamp = xs[-1]+1
    data_sample = buf[-1]
    xs.append(timestamp)
    xs = xs[-x_len:]
    ax.set_xlim([xs[0],xs[-1]])
    
    ys.append(data_sample)
    
    ys = ys[-x_len:]
    
    ylimits = ax.get_ylim()
    if(data_sample < ylimits[0]):
        new_limit = abs(data_sample - 0.1)
        ax.set_ylim(-new_limit, new_limit)
    if(data_sample > ylimits[1]):
        new_limit = data_sample + 0.1
        ax.set_ylim(-new_limit, new_limit)
        
    ax.set_xticks(xs)
    plt.xticks(rotation=45, ha='right')
    
    line.set_data(xs,ys)
    

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
    ser = serial.Serial('COM7', 115200, timeout=0)

    async def read():
        while True:
            if ser.in_waiting:
                try:
                    data = ser.readline()
                    splitData = [data[i:i+2] for i in range(0,10,2)]
                    intData = [0.0] * 5
                    for i in range(5):
                        # Turn ints into voltage values
                        intData[i] = (int.from_bytes(splitData[i], "little")/ADC_STEPS) * V_REF
                    buf.append(intData)
                    #print(intData)
                except Exception as e:
                    print(e)
                    pass
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

    async def plot():
        try:
            plt.show(block=False)
            await asyncio.sleep(0)
        except KeyboardInterrupt:
            pass
    await asyncio.gather(read(), process(), plot())

anim = animation.FuncAnimation(fig=fig,
                func=animate,
                fargs=(xs,ys),
                interval=1)
print("Started Running")
asyncio.run(main())