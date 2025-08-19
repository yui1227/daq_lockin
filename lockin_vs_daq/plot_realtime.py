import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from daq import DAQ
from sr865a import SR865a

daq_config = {
    'DAQ_NAME': 'Dev1',
    'DAQ_CHANNEL': 'ai0',
}
daq_param = {
    'SAMPLE_RATE': 1000,
    'SAMPLES_PER_READ': 10  # 假設一次讀10個點
}
sr865a_config = {
    'interface': 'serial',
    'port': 'COM3',
}
sr865a_param = {}

# 用於儲存即時資料
daq_data = []
daq_timestamps = []
lockin_data = []
lockin_timestamps = []

def daq_worker(stop_event):
    daq = DAQ(**daq_config)
    daq.set_real_time_acquisition_params(**daq_param)
    while not stop_event.is_set():
        data = daq.acquire_real_time_data()  # 回傳多個點
        now = time.time()
        dt = 1.0 / daq_param['SAMPLE_RATE']
        for i, v in enumerate(data):
            daq_data.append(v)
            daq_timestamps.append(now + i * dt)
        time.sleep(daq_param['SAMPLES_PER_READ'] * dt)

def lockin_worker(stop_event):
    lockin = SR865a(**sr865a_config)
    lockin.set_real_time_acquisition_params(**sr865a_param)
    while not stop_event.is_set():
        data = lockin.acquire_real_time_data()  # 單一點
        lockin_data.append(data)
        lockin_timestamps.append(time.time())
        time.sleep(0.05)  # 20Hz

def main():
    stop_event = threading.Event()
    t1 = threading.Thread(target=daq_worker, args=(stop_event,))
    t2 = threading.Thread(target=lockin_worker, args=(stop_event,))
    t1.start()
    t2.start()

    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    line1, = ax1.plot([], [], 'g-', label='DAQ')
    line2, = ax2.plot([], [], 'b-', label='Lock-in')

    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('DAQ Value', color='g')
    ax2.set_ylabel('Lock-in Value', color='b')
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')

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

    ani = FuncAnimation(fig, update, interval=100)
    plt.title('DAQ & Lock-in Real-time Data')
    plt.tight_layout()
    plt.show()

    stop_event.set()
    t1.join()
    t2.join()

if __name__ == "__main__":
    main()