import sounddevice as sd
import numpy as np
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

device_list = sd.query_devices()
print(device_list)

sd.default.device = [1, 6]  # Input, Outputデバイス指定

def callback(indata, frames, time, status):
    global plotdata
    data = indata[::downsample, 0]
    shift = len(data)
    plotdata = np.roll(plotdata, -shift, axis=0)
    plotdata[-shift:] = data

def update_plot(frame):
    global plotdata
    line.set_ydata(plotdata)
    return line,

downsample = 10
length = int(1000 * 44100 / (1000 * downsample))
plotdata = np.zeros((length))

fig, ax = plt.subplots()
fig.patch.set_facecolor('black')
ax.set_facecolor('black')
line, = ax.plot(plotdata, color='yellow', linewidth=2)  # 色を黄色に変更し、線を太くする
ax.set_ylim([-0.3, 0.3])  # y軸のスケールを調整
ax.set_xlim([0, length])
ax.yaxis.grid(True, color='gray')
ax.xaxis.grid(True, color='gray')
fig.tight_layout()

stream = sd.InputStream(
    channels=1,
    dtype='float32',
    callback=callback
)
ani = FuncAnimation(fig, update_plot, interval=80, blit=True)  # 更新間隔を50msに設定
with stream:
    plt.show()
