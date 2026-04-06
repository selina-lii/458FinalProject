import asyncio, serial, time
import numpy as np
import matplotlib.style as mplstyle
import matplotlib.pyplot as plt
import random

WINDOW = 2
V_REF = 5.0
R_BITS = 10
ADC_STEPS = (2**R_BITS) - 1
# Lines below are for performance purposes, can comment out
#mpl.rcParams['path.simplify_threshold'] = 1.0
mplstyle.use('fast')

buf = []
# Specific timestamps of each data point for accurate graphing and rate calculations
tstamps = []

x_len = 3000
y_range = [0,5]
x_range = [0,2]

fig,ax = plt.subplots()
xs = range(x_len)
ys = np.zeros((x_len,5)) * np.nan

line = ax.plot(xs,ys,animated=True)
ax.set_ylim(y_range)
ax.set_xlim(x_range)

plt.show(block=False)
plt.pause(0.1)
bg = fig.canvas.copy_from_bbox(fig.bbox)
for l in line:
    ax.draw_artist(l)
fig.canvas.blit(fig.bbox)

def preprocess(samples):
    # First two values are EMG, last three values are EOG
    emg = np.array(samples)[:,0:2]
    eog = np.array(samples)[:,2:5]
    # Band Pass EOG and EMG
    
    # Notch Filter EMG
    
    return emg,eog

def classify(features):
    
    return 1

# ── async pipeline ───────────────────────────────────────────────
async def main():
    print("I'm in main")
    ser = serial.Serial('COM7', 115200, timeout=0.1)

    async def read():
        readStartTime = time.time()
        while True:
            if ser.in_waiting:
                try:
                    data = ser.read(size=11)
                    #splitData = data.strip().split(",")
                    splitData = [data[i:i+2] for i in range(0,10,2)]
                    #print(splitData)
                    intData = [0.0] * 5
                    for i in range(5):
                        # Turn ints into voltage values
                        #intData[i] = (int(splitData[i])/ADC_STEPS) * V_REF
                        intData[i] = (int.from_bytes(splitData[i], "little")/ADC_STEPS) * V_REF
                    #await asyncio.sleep(0.0004)
                    #intData = [-2,-1,0,1,2]
                    buf.append(intData)
                    tstamps.append(time.time()-readStartTime)
                except Exception as e:
                    print(e)
                    pass
                await asyncio.sleep(0)

    async def process():
        global tstamps, buf
        timeToSleep = WINDOW
        stopPlotting = False
        while True:
            await asyncio.sleep(timeToSleep)
            print("Slept for", timeToSleep)
            startTime = time.time()
            if buf:
                snap, buf = buf, []
                print("data period=", tstamps[-1]-tstamps[0])
                print(f"n={len(snap)}, result={classify(preprocess(snap))}, compute time={time.time()-startTime}")
                if not stopPlotting:
                    # Plotting part
                    data_sample = np.array(snap[-x_len:],ndmin=2)
                    for i in range(np.shape(data_sample)[1]):
                        data_sample[:,i] = data_sample[:,i] + i
                    t_sample = tstamps[-x_len:]
    
                    #nanPoints = np.zeros((x_len - numPoints,5))*np.nan
                    #ys = np.concatenate((data_sample,nanPoints),0)
    
                    fig.canvas.restore_region(bg)
                    for l in range(len(line)):
                        line[l].set_ydata(data_sample[:,l])
                        line[l].set_xdata(t_sample)
                        ax.set_xlim([t_sample[0],t_sample[0]+2])
                        #print(np.shape(ys[:,l]))
                        ax.draw_artist(line[l])
                        #print("succeeded")
                    fig.canvas.blit(fig.bbox)
                    fig.canvas.flush_events()
                    # Stops plotting
                    if not plt.fignum_exists(fig.number):
                        stopPlotting = True
                tstamps = []
            timeToSleep = WINDOW - (time.time()-startTime)
            
    async def plot():
        global xs,ys,fig,bg,tstamps,buf
        stopPlotting = False
        # Higher numbers take up less compute resources
        # The following code results in a substantial incoming sampling rate reduction in optimal graphing conditions
        # Sampling rate on the Arduino should be adjusted accordingly
        # From tests with asyncio.sleep() A sampling rate of around 2500 Hz or higher is appropriate
        plotPeriod = 100
        while not stopPlotting:
            #print(len(buf))
            if (len(buf)+1) % plotPeriod == 0:
                # Plotting part
                data_sample = np.array(buf[-x_len:],ndmin=2)
                t_sample = tstamps[-x_len:]
    
                #nanPoints = np.zeros((x_len - numPoints,5))*np.nan
                #ys = np.concatenate((data_sample,nanPoints),0)
    
                fig.canvas.restore_region(bg)
                for l in range(len(line)):
                    line[l].set_ydata(data_sample[:,l])
                    line[l].set_xdata(t_sample)
                    ax.set_xlim([t_sample[0],t_sample[0]+2])
                    #print(np.shape(ys[:,l]))
                    ax.draw_artist(line[l])
                    #print("succeeded")
                fig.canvas.blit(fig.bbox)
                fig.canvas.flush_events()
                # Stops plotting
                if not plt.fignum_exists(fig.number):
                    stopPlotting = True
            await asyncio.sleep(0)
    await asyncio.gather(read(), process())

print("Started Running")
asyncio.run(main())