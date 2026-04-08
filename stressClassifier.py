import asyncio, serial, time
import numpy as np
import matplotlib.style as mplstyle
import matplotlib.pyplot as plt
import random
from scipy.signal import butter, filtfilt

WINDOW = 2
V_REF = 5.0
R_BITS = 10
ADC_STEPS = (2**R_BITS) - 1
FS = 1000

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
ys = np.zeros((x_len,3)) * np.nan

line = ax.plot(xs,ys,animated=True)
ax.set_ylim(y_range)
ax.set_xlim(x_range)

plt.show(block=False)
plt.pause(0.1)
bg = fig.canvas.copy_from_bbox(fig.bbox)
for l in line:
    ax.draw_artist(l)
fig.canvas.blit(fig.bbox)

def plateau(dat,threshold=1):
   # Returns duration of plateaus
   above = dat >= threshold
   transitions = np.diff(above.astype(int))
   n_events = np.sum(transitions == 1)
   idx = np.where(transitions != 0)[0] + 1
   durations = np.diff(np.concatenate(([0], idx, [len(above)])))
   max_dur = np.max(durations)
   avg_dur = np.mean(durations)
   return n_events, max_dur, avg_dur


def peaks(dat,fold=1):
   # Return which locations are peaks in an array
   SD=np.std(dat)
   peaks = dat>SD*fold
   return peaks


def drift(dat, window):
   def rolling_std(signal, window):
       std = [signal[i:i+window].std() for i in range(len(signal)-window+1)]
       return np.array(std)
   return rolling_std(dat,window)


def rms_power(dat):
   # RMS of rectified EMG (RMS(∑|EMG|) - average muscle activation level
   b, a = butter(5, [70, 240], btype='bandpass', fs=FS)
   filt = filtfilt(b, a, np.transpose(dat))
   def rolling_rms(signal, window):
       rms = [np.sqrt(np.mean(signal[i:i+window]**2)) for i in range(len(signal)-window+1)]
       return np.array(rms)
   rms=rolling_rms(filt,100)
   return rms


def preprocess_emg(emg):
   power = rms_power(emg)
   return power


#def simulate_emg(duration=10):
#   emg = nk.emg_simulate(duration=duration,sampling_rate=1000,burst_number=6,noise=0.05,burst_duration=0.7,)
#   t=np.linspace(0,duration,duration*1000)
#   plt.figure(figsize=(14, 2))
#   plt.plot(emg)
#   plt.xlabel("Time (s)")
#   plt.ylabel("EMG amplitude (a.u.)")
#   plt.show()
#   return t, emg


def classify_emg(roll_rms):
   # Jaw Clench: Larger RMS = stress
   n_events, max_dur, avg_dur= plateau(roll_rms*5,2)
   rate = n_events/WINDOW
   return rate, max_dur, avg_dur


def preprocess_eog(eog):
   eog = np.array(eog)
   # Blink rate
   b, a = butter(4, [2,10], btype='bandpass', fs=FS)
   eog_filt = filtfilt(b, a, np.transpose(eog))
   blinks = peaks(eog_filt)


   # Saccades
   b, a = butter(2, [0.25,7.5], btype='band', fs=FS)
   eog_filt = filtfilt(b, a, np.transpose(eog))
   # saccades = drift(eog_filt)


   return blinks

def classify_eog(blinks):
   # Count of blinks: High blink rate = low alertness
   n_events, max_dur, avg_dur= plateau(blinks,1)
   rate = n_events/WINDOW
   return rate, max_dur, avg_dur


def classify(eog, emg):
   alertness = True
   stress = False
   blink_rate, max_blink_dur, avg_blink_dur = classify_eog(eog)
   n_clenches, max_clench_dur, avg_clench_dur = classify_emg(emg)
   HIGH_BLINK_RATE = 5
   LOW_BLINK_RATE = 0
   LONG_BLINK = 1
   LONG_CLENCH = 1.5
   MANY_CLENCHES = 2
   print(blink_rate)
   print(max_blink_dur)
   print(avg_blink_dur)
   print(n_clenches)
   # (High blink rate OR Prolonged blink) AND (No clench)
   if (blink_rate>=HIGH_BLINK_RATE \
       or max_blink_dur>=LONG_BLINK)\
       and not (n_clenches>MANY_CLENCHES):
       alertness = False
   if (max_clench_dur>LONG_CLENCH or n_clenches>MANY_CLENCHES) or (blink_rate<=LOW_BLINK_RATE):
       stress = True
  
   return stress, alertness
  
def preprocess(samples):
   emg = np.array(samples)[:,0:2]
   eog = np.array(samples)[:,2:5]
   eog = preprocess_eog(eog)
   emg = preprocess_emg(emg)
   return eog, emg

# ── async pipeline ───────────────────────────────────────────────
async def main():
    print("I'm in main")
    ser = serial.Serial('COM7', 115200, timeout=0.1)

    async def read():
        readStartTime = time.time()
        while True:
            if ser.in_waiting:
                try:
                    data = ser.read(size=7)
                    #splitData = data.strip().split(",")
                    splitData = [data[i:i+2] for i in range(0,6,2)]
                    #print(splitData)
                    intData = [0.0] * 3
                    for i in range(3):
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
                processedEOG, processedEMG = preprocess(snap)
                stressed, alert = classify(processedEOG, processedEMG)
                print(f"n={len(snap)}, stressed?={stressed}, alert?={alert},compute time={time.time()-startTime}")
                if stressed:
                    ser.write(b'\x07')
                if not alert:
                    ser.write(b'\x08')
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
            
    # async def plot():
    #     global xs,ys,fig,bg,tstamps,buf
    #     stopPlotting = False
    #     # Higher numbers take up less compute resources
    #     # The following code results in a substantial incoming sampling rate reduction in optimal graphing conditions
    #     # Sampling rate on the Arduino should be adjusted accordingly
    #     # From tests with asyncio.sleep() A sampling rate of around 2500 Hz or higher is appropriate
    #     plotPeriod = 100
    #     while not stopPlotting:
    #         #print(len(buf))
    #         if (len(buf)+1) % plotPeriod == 0:
    #             # Plotting part
    #             data_sample = np.array(buf[-x_len:],ndmin=2)
    #             t_sample = tstamps[-x_len:]
    
    #             #nanPoints = np.zeros((x_len - numPoints,5))*np.nan
    #             #ys = np.concatenate((data_sample,nanPoints),0)
    
    #             fig.canvas.restore_region(bg)
    #             for l in range(len(line)):
    #                 line[l].set_ydata(data_sample[:,l])
    #                 line[l].set_xdata(t_sample)
    #                 ax.set_xlim([t_sample[0],t_sample[0]+2])
    #                 #print(np.shape(ys[:,l]))
    #                 ax.draw_artist(line[l])
    #                 #print("succeeded")
    #             fig.canvas.blit(fig.bbox)
    #             fig.canvas.flush_events()
    #             # Stops plotting
    #             if not plt.fignum_exists(fig.number):
    #                 stopPlotting = True
    #         await asyncio.sleep(0)
    await asyncio.gather(read(), process())

print("Started Running")
asyncio.run(main())