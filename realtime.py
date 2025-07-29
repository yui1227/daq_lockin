import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time
from collections import deque # 用於儲存固定數量的數據點

# --- DAQ 設置 ---
# 請根據你的 DAQ 設備和連接，修改以下參數
# 設備名稱/埠號，例如 'Dev1/ai0'，表示 Dev1 設備上的類比輸入通道 0
DAQ_CHANNEL = "Dev1/ai3"
SAMPLE_RATE = 1000       # 每秒採樣點數
SAMPLES_PER_READ = 100   # 每次從 DAQ 讀取的數據點數
READ_INTERVAL_MS = 50    # Matplotlib 更新間隔 (毫秒)。請根據 DAQ_CHANNEL 的頻率和 SAMPLES_PER_READ 調整

# --- 圖形設置 ---
MAX_DISPLAY_POINTS = 500 # 圖形上顯示的最大數據點數
Y_AXIS_RANGE = (-10.0, 10.0) # Y 軸範圍 (例如，±10V)

# 初始化數據緩衝區
# deque 用於保存最新的數據點，當超過 MAX_DISPLAY_POINTS 時會自動移除舊的點
data_x = deque(maxlen=MAX_DISPLAY_POINTS)
data_y = deque(maxlen=MAX_DISPLAY_POINTS)
current_time = 0.0 # 用於追蹤時間戳

# --- Matplotlib 初始化 ---
fig, ax = plt.subplots(figsize=(8, 6))
# 繪製一條初始的空線條，這將是我們在動畫中更新的對象
line, = ax.plot(data_x, data_y, 'b.', label='DAQ Voltage')

ax.set_title(f"Real-time Data from NI DAQ ({DAQ_CHANNEL})")
ax.set_xlabel("Time (s)")
ax.set_ylabel("Voltage (V)")
ax.set_ylim(Y_AXIS_RANGE) # 設定固定的 Y 軸範圍
ax.set_xlim(0, MAX_DISPLAY_POINTS / SAMPLE_RATE) # 初始 X 軸範圍
ax.grid(True)
ax.legend()

# --- DAQ 任務初始化 ---
# 這裡使用全局變量 `task`，方便在動畫函數中訪問和關閉
task = None

def init_daq_task():
    global task
    try:
        if task is None:
            task = nidaqmx.Task()
            # 添加類比輸入通道
            task.ai_channels.add_ai_voltage_chan(
                DAQ_CHANNEL,
                # terminal_config=TerminalConfiguration.RSE # 或者其他配置，如 DIFF, NRSE
            )
            # 配置採樣時序
            task.timing.cfg_samp_clk_timing(
                rate=SAMPLE_RATE,
                sample_mode=AcquisitionType.CONTINUOUS, # 連續採樣
                samps_per_chan=SAMPLES_PER_READ # 每次讀取點數
            )
            print(f"DAQ Task '{DAQ_CHANNEL}' initialized successfully.")
            task.start() # 啟動任務
            print("DAQ Task started.")
    except Exception as e:
        print(f"Error initializing DAQ task: {e}")
        if task:
            task.close()
        task = None # 重置 task 以防止後續錯誤

def close_daq_task():
    global task
    if task:
        try:
            task.stop()
            task.close()
            print("DAQ Task closed.")
        except Exception as e:
            print(f"Error closing DAQ task: {e}")
        task = None

# --- Matplotlib 動畫函數 ---

# 初始化函數：用於設置初始繪圖狀態（對於blit=True很重要）
def init_plot():
    line.set_data([], [])
    return line, # 返回一個可迭代對象，包含所有需要更新的 Artist

# 更新函數：每次動畫幀更新時調用
def update_plot(frame):
    global current_time
    global task

    if task is None:
        # 如果 DAQ 任務未初始化或出錯，嘗試重新初始化
        init_daq_task()
        if task is None: # 如果還是無法初始化，則跳過本次更新
            print("DAQ task not ready. Skipping update.")
            return line,

    try:
        # 從 DAQ 讀取數據
        # read() 會返回一個 numpy 數組
        new_data = task.read(number_of_samples_per_channel=SAMPLES_PER_READ)
        # 確保 new_data 是數組，即使只有一個點
        if not isinstance(new_data, (list, np.ndarray)):
            new_data = [new_data]
        new_data = np.array(new_data)

        # 計算新數據點的時間戳
        new_x_points = np.linspace(current_time,
                                   current_time + (SAMPLES_PER_READ / SAMPLE_RATE),
                                   SAMPLES_PER_READ, endpoint=False)

        # 將新數據添加到緩衝區
        data_x.extend(new_x_points)
        data_y.extend(new_data)

        # 更新當前時間戳
        current_time += (SAMPLES_PER_READ / SAMPLE_RATE)

        # 更新線條數據
        line.set_data(list(data_x), list(data_y))

        # 動態調整 X 軸範圍以顯示最新的數據
        # 確保 X 軸始終顯示最近的 MAX_DISPLAY_POINTS 數據
        if len(data_x) > 0:
            min_x = data_x[0]
            max_x = data_x[-1]
            # 讓圖形右側留出一些空間
            ax.set_xlim(min_x, max_x + (MAX_DISPLAY_POINTS / SAMPLE_RATE) * 0.1)

        return line, # 返回一個可迭代對象

    except nidaqmx.errors.DaqError as e:
        print(f"DAQ Error during read: {e}")
        # 關閉 DAQ 任務以防止進一步錯誤
        close_daq_task()
        return line, # 即使出錯也要返回 Artist
    except Exception as e:
        print(f"An unexpected error occurred during plot update: {e}")
        close_daq_task() # 發生任何錯誤時都嘗試關閉 DAQ
        return line,

# --- 主程式執行 ---
if __name__ == "__main__":
    init_daq_task() # 在動畫開始前初始化 DAQ 任務

    # 創建動畫
    # fig: 要動畫化的圖形
    # update_plot: 每幀調用的更新函數
    # init_func: 初始化函數
    # interval: 每幀之間的間隔（毫秒）
    # blit: 優化選項，只重繪改變的部分，提高性能 (推薦開啟)
    # cache_frame_data: 設置為 False 以便在動畫運行時釋放舊幀數據，有助於長時間運行
    ani = animation.FuncAnimation(fig, update_plot, init_func=init_plot,
                                  interval=READ_INTERVAL_MS, blit=True,
                                  cache_frame_data=False)

    try:
        print(f"Starting real-time plotting from '{DAQ_CHANNEL}'. Press Ctrl+C to stop.")
        plt.show() # 顯示圖形窗口，這會啟動動畫
    except KeyboardInterrupt:
        print("\nPlotting interrupted by user.")
    finally:
        # 確保在程序結束時關閉 DAQ 任務
        close_daq_task()
        print("Program finished.")