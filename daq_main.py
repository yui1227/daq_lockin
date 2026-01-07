import numpy as np
import matplotlib.pyplot as plt
import time
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

from lockin_lib import SoftwareLockInAmplifier

# 設定模擬模式
# True: 使用模擬數據 (測試演算法用)
# False: 連接真實 NI DAQ 硬體 (正式實驗用)
SIMULATION_MODE = True 

# --- 硬體設定參數 ---
DAQ_DEVICE_NAME = "Dev1"          # NI MAX 中看到的裝置名稱
REF_CHANNEL_ID = "ai0"            # 參考訊號接在 ai0
SIGNAL_CHANNEL_IDS = ["ai1", "ai2"] # 訊號分別接在 ai1, ai2...
SAMPLING_RATE = 50000             # 採樣率 50kHz (根據 EOM 頻率調整)
ACQUISITION_TIME = 1.0            # 錄製長度 (秒)
TIME_CONSTANT = 0.05              # 鎖相放大器時間常數 (秒)

def acquire_real_data():
    """從 NI DAQ 擷取真實數據"""
    try:
        import nidaqmx
        from nidaqmx.constants import AcquisitionType
    except ImportError:
        print("錯誤: 找不到 'nidaqmx' 套件。請執行 pip install nidaqmx")
        return None, None

    # 計算總採樣點數
    num_samples = int(SAMPLING_RATE * ACQUISITION_TIME)
    
    # 建立通道列表 (Reference + Signals)
    all_channels = [f"{DAQ_DEVICE_NAME}/{REF_CHANNEL_ID}"]
    for ch in SIGNAL_CHANNEL_IDS:
        all_channels.append(f"{DAQ_DEVICE_NAME}/{ch}")
    
    print(f"正在從 NI DAQ ({DAQ_DEVICE_NAME}) 擷取數據...")
    print(f"通道: {all_channels}")
    print(f"長度: {ACQUISITION_TIME} 秒, 採樣率: {SAMPLING_RATE} Hz")

    with nidaqmx.Task() as task:
        # 1. 設定類比輸入通道 (Voltage)
        for ch_name in all_channels:
            task.ai_channels.add_ai_voltage_chan(ch_name)
        
        # 2. 設定時脈與採樣模式 (Finite Samples)
        task.timing.cfg_samp_clk_timing(
            rate=SAMPLING_RATE,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=num_samples
        )
        
        # 3. 開始擷取 (這會阻塞直到擷取完成)
        # data 格式: [通道數, 樣本數] 的 2D list
        data = task.read(number_of_samples_per_channel=num_samples, timeout=ACQUISITION_TIME + 5.0)
        
    return np.array(data), num_samples

def generate_mock_data():
    """生成模擬數據 (當沒有硬體時使用)"""
    print("--- 模擬模式：生成假數據中 ---")
    num_samples = int(SAMPLING_RATE * ACQUISITION_TIME)
    t = np.arange(num_samples) / SAMPLING_RATE
    mod_freq = 1000.0 # 1kHz 調變
    
    # 模擬參考 (Row 0)
    ref_data = np.sin(2 * np.pi * mod_freq * t) + 0.05 * np.random.randn(num_samples)
    
    # 模擬訊號 1 (Row 1): 強訊號
    sig1 = 0.5 * np.sin(2 * np.pi * mod_freq * t + np.radians(45)) + 0.2 * np.random.randn(num_samples)
    
    # 模擬訊號 2 (Row 2): 弱訊號
    sig2 = 0.02 * np.sin(2 * np.pi * mod_freq * t + np.radians(180)) + 0.2 * np.random.randn(num_samples)
    
    # 堆疊成 (3, N) 的陣列
    data = np.vstack([ref_data, sig1, sig2])
    return data, num_samples

def main():
    # 1. 獲取數據
    if SIMULATION_MODE:
        raw_data, n_samples = generate_mock_data()
    else:
        raw_data, n_samples = acquire_real_data()
        if raw_data is None: return

    # 確保數據形狀正確
    if raw_data.shape[0] != (1 + len(SIGNAL_CHANNEL_IDS)):
        print("警告: 數據通道數量與設定不符")

    # 分離參考與訊號
    # 假設第 0 行是參考，後面是訊號
    ref_data = raw_data[0, :]
    signal_channels_data = raw_data[1:, :]
    
    # 2. 初始化鎖相放大器庫
    lia = SoftwareLockInAmplifier(SAMPLING_RATE)
    
    print("正在處理數據...")
    
    # 3. 分析參考頻率 (只做一次)
    ref_sin, ref_cos, detected_freq = lia.generate_reference_oscillator(ref_data)
    print(f"偵測到的參考頻率: {detected_freq:.2f} Hz")
    
    # 4. 迴圈處理每個訊號通道
    results = []
    for i, sig_data in enumerate(signal_channels_data):
        ch_name = SIGNAL_CHANNEL_IDS[i]
        r, theta = lia.process_channel(sig_data, ref_sin, ref_cos, TIME_CONSTANT)
        
        # 計算平均值 (如果是穩態測量)
        avg_r = np.mean(r[int(SAMPLING_RATE*0.1):]) # 忽略前 0.1秒的濾波暫態
        print(f"通道 {ch_name} -> 平均振幅: {avg_r:.4f} V")
        
        results.append({"name": ch_name, "R": r, "Theta": theta})

    # 5. 繪圖顯示
    t = np.arange(n_samples) / SAMPLING_RATE
    
    plt.figure(figsize=(10, 8))
    
    # 上圖: 原始參考訊號 (Zoom in)
    plt.subplot(3, 1, 1)
    zoom = 500
    plt.plot(t[:zoom], ref_data[:zoom], 'k', label='Ref Raw')
    plt.plot(t[:zoom], ref_sin[:zoom], 'g--', label='LIA Generated Sin', alpha=0.7)
    plt.title(f"參考訊號檢查 (前 {zoom} 點) - Freq: {detected_freq:.1f}Hz")
    plt.legend()
    plt.grid(True)
    
    # 中圖: 解調振幅 R
    plt.subplot(3, 1, 2)
    for res in results:
        plt.plot(t, res["R"], label=f'{res["name"]} R')
    plt.title(f"解調振幅 (Time Constant = {TIME_CONSTANT}s)")
    plt.ylabel("Voltage (V)")
    plt.legend()
    plt.grid(True)
    
    # 下圖: 解調相位 Theta
    plt.subplot(3, 1, 3)
    for res in results:
        plt.plot(t, res["Theta"], label=f'{res["name"]} Phase')
    plt.title("解調相位 (Degrees)")
    plt.xlabel("Time (s)")
    plt.ylabel("Phase (deg)")
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()