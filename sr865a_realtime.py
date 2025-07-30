import pyvisa
import pprint
from srsinst.sr860 import SR865A
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# plt.ion()  # 開啟互動模式
fig, ax = plt.subplots()
current = 0
x_data, y_data = deque(maxlen=1000), deque(maxlen=1000)
line, = ax.plot(x_data, y_data, '.')  # 紅色折線
ax.grid(True)
ax.set_xlim(0, 1000)
ax.set_ylim(-180, 180)

rm=pyvisa.ResourceManager()
inst = SR865A('visa',rm.list_resources()[0])
# 設定參考光
inst.ref.reference_source = 'external'

# inst.scan.start()
# # time.sleep(17)

def update(frame):
    global current
    global x_data
    global y_data
    x_data.append(current)
    y_data.append(inst.data.channel_value[3])
    current+=1

    line.set_xdata(x_data)
    line.set_ydata(y_data)
    ax.set_xlim(min(x_data), min(x_data)+1000)
    fig.canvas.draw()
    fig.canvas.flush_events()

ani=FuncAnimation(fig,update,interval=20,cache_frame_data=False)
plt.show()