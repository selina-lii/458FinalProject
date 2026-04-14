import asyncio, serial, time
import numpy as np
import matplotlib.style as mplstyle
import matplotlib.pyplot as plt
import random
import csv
from scipy.signal import butter, filtfilt

WINDOW = 5
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

x_len = WINDOW * 1000
y_range = [0,5]
x_range = [0,WINDOW]

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

def plateau(dat,threshold=1,isEOG=False):
   # Returns duration of plateaus
   above = dat >= threshold
   transitions = np.diff(above.astype(int))
   n_events = np.sum(transitions == 1)
   idx = np.where(transitions != 0)[0] + 1
   
   transitionIndices = np.nonzero(transitions)
   print(np.shape(transitionIndices))
   if not np.shape(transitionIndices)[1] == 0:
       if isEOG:
          transitionIndices = transitionIndices[1]
       else:
          transitionIndices = transitionIndices[0]
   else:
       return above,0,[],[]
   print(transitionIndices)
   if isEOG:
       if transitionIndices.shape[0] % 2 == 1:
          np.append(transitionIndices,np.shape(transitions)[1])
   amplitudes = np.zeros(np.shape(transitionIndices[1::2]))
   amplitudeIndices = np.zeros(np.shape(transitionIndices[1::2]))
   for i,(end,start) in enumerate(zip(transitionIndices[1::2],transitionIndices[::2])):
       if isEOG:
          amplitudes[i]=np.max(dat[0,start:end])
          amplitudeIndices[i]=np.argmax(dat[0,start:end])
       else:
          amplitudes[i]=np.max(dat[start:end])
          amplitudeIndices[i]=np.argmax(dat[start:end])
   if isEOG:
       longShort = amplitudes > .5
       n_events = np.sum(longShort)
   else:
       durations = transitionIndices[1::2] - transitionIndices[::2]
       longShort = durations > 500
   return above, n_events, longShort, amplitudeIndices


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
   emgfilt = filtfilt(b, a, np.transpose(dat))
   t = np.linspace(0,WINDOW,WINDOW*FS)
   def rolling_rms(signal, t, window):
       rms = [np.sqrt(np.mean(signal[i:i+window]**2)) for i in range(len(signal)-window+1)]
       t_center = t[window//2 : window//2 + len(rms)]
       return np.array(t_center), np.array(rms)
   t_RMS, RMS=rolling_rms(emgfilt,t,100)
   return t_RMS, RMS


def preprocess_emg(emg):
   t, power = rms_power(emg)
   return t, power*10


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
   above, n_events, longShort, _ = plateau(roll_rms,0.1,False)
   return np.sum(longShort) > 0


def preprocess_eog(eog):
   eog = np.array(eog)
   ## Blink rate
   #b, a = butter(4, [2,10], btype='bandpass', fs=FS)
   #eog_filt = filtfilt(b, a, np.transpose(eog))

   # Saccades
   b, a = butter(4, [2,10], btype='band', fs=FS)
   eog_filt = filtfilt(b, a, np.transpose(eog))
   blinks = peaks(eog_filt)
   # saccades = drift(eog_filt)


   return eog_filt * -20

def classify_eog(blinks):
   # Count of blinks: High blink rate = low alertness
   rect, n_events, longShort, amplitudeIndices = plateau(blinks,0.2,True)
   rate = n_events/WINDOW
   return rect, rate, longShort


def classify(eog, emg):
   alertness = True
   rect, blink_rate, isLong = classify_eog(eog)
   if not np.shape(isLong)[0] == 0:
      sequentialShort = ~np.array(isLong[:-1]) & ~np.array(isLong[1:])
   else:
      sequentialShort = []
   if sum(sequentialShort) > 0:
       alertness = False
   elif blink_rate <= 1:
       alertness = True
   stress = classify_emg(emg)
#    HIGH_BLINK_RATE = 5
#    LOW_BLINK_RATE = 0
#    LONG_CLENCH = 1.5
#    MANY_CLENCHES = 2
   #print(blink_rate)
   #print(max_blink_dur)
   #print(avg_blink_dur)
   #print(n_clenches)
   # (High blink rate OR Prolonged blink) AND (No clench)
#    if (blink_rate>=HIGH_BLINK_RATE \
#        or True)\
#        and not (n_clenches>MANY_CLENCHES):
#        alertness = False
#    if (max_clench_dur>LONG_CLENCH or n_clenches>MANY_CLENCHES) or (blink_rate<=LOW_BLINK_RATE):
#        stress = True
  
   return rect, stress, alertness
  
def preprocess(samples):
   emg = np.array(samples)[:,0]
   eog = np.array(samples)[:,1:2]
   eog = preprocess_eog(eog)
   emg_t, emg = preprocess_emg(emg)
   return eog, emg, emg_t

# ── async pipeline ───────────────────────────────────────────────
async def main():
    print("I'm in main")
    ser = serial.Serial('COM7', 115200, timeout=0.1)

    async def read():
        readStartTime = time.time()
        with open("testingData.csv", "a") as f:
            writer = csv.writer(f)
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
                        writer.writerow(intData)
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
                processedEOG, processedEMG, emg_t = preprocess(snap)
                rect, stressed, alert = classify(processedEOG, processedEMG)
                print(f"n={len(snap)}, stressed?={stressed}, alert?={alert},compute time={time.time()-startTime}")
                if stressed:
                    ser.write(b'\x07')
                    pass
                if not alert:
                    ser.write(b'\x08')
                    pass
                if not stopPlotting:
                    # Plotting part
                    data_sample = np.array(snap[-x_len:],ndmin=2)
                    for i in range(np.shape(data_sample)[1]):
                        data_sample[:,i] = data_sample[:,i] + i
                    t_sample = tstamps[-x_len:]

                    #data_sample= processedEMG * 10
                    #t_sample = np.arange(np.shape(processedEMG)[0]) / FS
                    
                    #data_sample = np.hstack([np.transpose(processedEOG),np.transpose(rect)])
                    #t_sample = tstamps[-x_len:]
    
                    #nanPoints = np.zeros((x_len - numPoints,5))*np.nan
                    #ys = np.concatenate((data_sample,nanPoints),0)
    
                    fig.canvas.restore_region(bg)
                    for l in range(len(line)):
                        line[l].set_ydata(data_sample[:,l])
                        #line[l].set_ydata(data_sample)
                        line[l].set_xdata(t_sample)
                        ax.set_xlim([t_sample[0],t_sample[0]+WINDOW])
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