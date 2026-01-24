import threading
import time
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from daq import DAQ
from helper import Helper
from sr865a import SR865a
from collections import deque

daq_config = {
    'DAQ_NAME': Helper.list_daq_devices()[0],
    'DAQ_CHANNEL': 'ai3',
}
daq_param = {
    'SAMPLE_RATE': 152,
    'SAMPLES_PER_READ': 35
}
sr865a_config = {
    'interface_type': 'visa',
    'port': Helper.list_lockin_devices_visa()[0],
}
sr865a_param = {}

MAX_POINTS = 1000  # 只顯示最新 200 筆

# 用於儲存即時資料（只保留最新 MAX_POINTS 筆）
daq_data = deque(maxlen=MAX_POINTS)
daq_timestamps = deque(maxlen=MAX_POINTS)
lockin_data = deque(maxlen=MAX_POINTS)
lockin_timestamps = deque(maxlen=MAX_POINTS)

def daq_worker(stop_event):
    daq = DAQ(**daq_config)
    daq.set_real_time_acquisition_params(**daq_param)
    dt = 1.0 / daq_param['SAMPLE_RATE']
    while not stop_event.is_set():
        data = daq.acquire_real_time_data()  # 回傳多個點
        now = time.time()
        for i, v in enumerate(data):
            daq_data.append(v)
            daq_timestamps.append(now + i * dt)
        # time.sleep(daq_param['SAMPLES_PER_READ'] * dt)
    daq.close_task()

def lockin_worker(stop_event):
    lockin = SR865a(**sr865a_config)
    lockin.set_real_time_acquisition_params(**sr865a_param)
    while not stop_event.is_set():
        data = lockin.acquire_real_time_data()  # 單一點
        lockin_data.append(data)
        lockin_timestamps.append(time.time())
        # time.sleep(0.05)  # 20Hz
    lockin.inst.disconnect()

def main():
    stop_event = threading.Event()
    t1 = threading.Thread(target=daq_worker, args=(stop_event,))
    t2 = threading.Thread(target=lockin_worker, args=(stop_event,))
    t1.start()
    t2.start()

    fig, axes = plt.subplots(1,2,figsize=(10,5))
    ax1:plt.Axes = axes[0]
    ax2:plt.Axes = axes[1]

    ax1.set_ylim(-10, 10)
    ax2.set_ylim(-180, 180)

    line1, = ax1.plot([], [], 'g.', label='DAQ')
    line2, = ax2.plot([], [], 'b.', label='Lock-in')

    ax1.set_ylabel('DAQ Value (V)', color='g')
    ax2.set_ylabel('Lock-in Value (Degree)', color='b')

    ax1.set_xticklabels([])  # 隱藏 x 軸 tick label
    ax2.set_xticklabels([])  # 隱藏 x 軸 tick label

    def update(frame):
        if len(daq_timestamps) == 0 or len(lockin_timestamps) == 0:
            return line1, line2
        t0 = min(daq_timestamps[0], lockin_timestamps[0])
        daq_times = [ts - t0 for ts in daq_timestamps]
        lockin_times = [ts - t0 for ts in lockin_timestamps]
        line1.set_data(daq_times, daq_data)
        line2.set_data(lockin_times, lockin_data)
        ax1.relim()
        ax1.autoscale_view()
        ax2.relim()
        ax2.autoscale_view()
        return line1, line2
    ani = FuncAnimation(fig, update, interval=10, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

    stop_event.set()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()