import threading
import queue
import time
import csv
import itertools
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import nidaqmx
from nidaqmx.constants import AcquisitionType,TerminalConfiguration

# 匯入您提供的函式庫
try:
    from lockin_lib import SoftwareLockInAmplifier
    from sr865a_lib import SR865AHighSpeedCapture
except ImportError as e:
    print(f"錯誤: 找不到必要的函式庫檔案 ({e})。請確保 lockin_lib.py 和 sr865a_lib.py 在同一目錄下。")
    exit()

# ==========================================
#              實驗參數設定
# ==========================================
# 共通參數
DURATION = 20.0       # 擷取時間 (秒)
TIME_CONSTANT = 0.001 # 時間常數 1 ms (軟體與硬體皆設為此值)

# --- NI DAQ (軟體鎖相) 設定 ---
DAQ_SAMPLING_RATE = 9765.625 # 10 kHz (量測頻率固定)
DAQ_DEV = "Dev1"            # DAQ 設備名稱
DAQ_REF_CH = "ai2"          # 參考訊號輸入通道
DAQ_SIG_CH = "ai3"         # 待測訊號輸入通道
DAQ_VOLTAGE_RANGE = 10.0    # DAQ 輸入範圍 (+-10V)

# --- SR865A (硬體鎖相) 設定 ---
VISA_ADDRESS = "USB0::0xB506::0x2000::004937::INSTR" # 請修改為您的 SR865A VISA 位址
SR865A_SENSITIVITY = 0.2    # 200 mV
# Max Rate 會根據時間常數調整
# Rate Index 說明: Rate = MaxRate / 2^n
# 建議值: 10~12 (約 500Hz ~ 2kHz)
# 若設太低 (頻率太高) 可能導致 SR865A 內部 Buffer (4MB) 在 20秒內爆滿
SR865A_RATE_INDEX = 3      

# ==========================================
#              工作執行緒函數
# ==========================================

def task_software_lockin(result_queue):
    """
    執行緒 1: NI DAQ 擷取 + 軟體鎖相運算
    """
    print("[Software] 執行緒啟動，準備擷取...")
    
    # 1. 硬體擷取 (NI DAQ)
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                f"{DAQ_DEV}/{DAQ_REF_CH}", 
                min_val=-DAQ_VOLTAGE_RANGE, max_val=DAQ_VOLTAGE_RANGE,
                terminal_config=TerminalConfiguration.DIFF
            )
            task.ai_channels.add_ai_voltage_chan(
                f"{DAQ_DEV}/{DAQ_SIG_CH}", 
                min_val=-DAQ_VOLTAGE_RANGE, max_val=DAQ_VOLTAGE_RANGE,
                terminal_config=TerminalConfiguration.DIFF
            )

            n_samples = int(DAQ_SAMPLING_RATE * DURATION)
            
            task.timing.cfg_samp_clk_timing(
                rate=DAQ_SAMPLING_RATE,
                sample_mode=AcquisitionType.FINITE,
                samps_per_chan=n_samples
            )

            print(f"[Software] 開始 DAQ 擷取 ({DURATION}s)...")
            # 讀取數據 (阻塞直到完成)
            data = task.read(number_of_samples_per_channel=n_samples, timeout=DURATION + 5.0)
            data_np = np.array(data)
            
            ref_raw = data_np[0, :]
            sig_raw = data_np[1, :]
            
            print("[Software] 擷取完成，開始 LIA 運算...")

    except Exception as e:
        print(f"[Software] DAQ 錯誤: {e}")
        result_queue.put(None)
        return

    # 2. 軟體運算 (使用 lockin_lib)
    try:
        lia = SoftwareLockInAmplifier(DAQ_SAMPLING_RATE)
        
        # A. 產生參考訊號
        ref_sin, ref_cos, freq = lia.generate_reference_oscillator(ref_raw)
        print(f"[Software] 偵測到的參考頻率: {freq:.2f} Hz")
        
        # B. 解調訊號
        r_rms, theta = lia.process_channel(sig_raw, ref_sin, ref_cos, TIME_CONSTANT)
        
        # 建立時間軸
        t = np.arange(len(r_rms)) / DAQ_SAMPLING_RATE
        
        result_queue.put({
            "type": "Software",
            "time": t,
            "R": r_rms,
            "Theta": theta,
            "Freq": freq
        })
        print("[Software] 處理完成")

    except Exception as e:
        print(f"[Software] 運算錯誤: {e}")
        result_queue.put(None)


def task_hardware_sr865a(result_queue):
    """
    執行緒 2: SR865A 硬體擷取
    """
    print("[Hardware] 執行緒啟動，連接儀器...")
    sr = SR865AHighSpeedCapture(VISA_ADDRESS)
    
    try:
        sr.connect()
        
        # 設定參數
        sr.set_parameters(time_constant=TIME_CONSTANT, sensitivity=SR865A_SENSITIVITY)
        
        # 執行擷取
        print(f"[Hardware] 開始 SR865A 擷取 ({DURATION}s)...")
        t_axis, r_data, theta_data, actual_rate = sr.capture(DURATION, rate_index=SR865A_RATE_INDEX)
        
        result_queue.put({
            "type": "Hardware",
            "time": t_axis,
            "R": r_data,
            "Theta": theta_data,
            "fs": actual_rate
        })
        print(f"[Hardware] 擷取完成 (Rate: {actual_rate:.2f} Hz)")
        
    except Exception as e:
        print(f"[Hardware] 錯誤: {e}")
        result_queue.put(None)
    finally:
        sr.disconnect()

def save_comparison_to_csv(filename, res_soft, res_hard):
    """
    將兩組數據存入同一個 CSV 檔案。
    由於採樣率可能不同，採用並排 (Side-by-Side) 格式。
    """
    print(f"\n正在儲存數據至 {filename} ...")
    
    try:
        # 準備標頭
        headers = [
            "Soft_Time(s)", "Soft_R(V)", "Soft_Theta(deg)", 
            "", # 空隔分隔視覺
            "Hard_Time(s)", "Hard_R(V)", "Hard_Theta(deg)"
        ]

        # 準備數據行 (使用 zip_longest 處理不同長度的陣列)
        # 軟體數據
        soft_rows = zip(res_soft['time'], res_soft['R'], res_soft['Theta'])
        # 硬體數據
        hard_rows = zip(res_hard['time'], res_hard['R'], res_hard['Theta'])
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 寫入實驗資訊表頭
            # writer.writerow(["# Experiment Comparison Data"])
            # writer.writerow([f"# Date: {datetime.now().isoformat()}"])
            # writer.writerow([f"# Software Params: FS={DAQ_SAMPLING_RATE}Hz, TC={TIME_CONSTANT}s"])
            # writer.writerow([f"# Hardware Params: FS={res_hard['fs']:.2f}Hz, TC={TIME_CONSTANT}s, Sens={SR865A_SENSITIVITY}V"])
            # writer.writerow([]) # 空行
            
            # 寫入欄位名稱
            writer.writerow(headers)
            
            # 逐行寫入 (zip_longest 會自動補 None，我們將其轉為空字串)
            for s_row, h_row in itertools.zip_longest(soft_rows, hard_rows, fillvalue=(None, None, None)):
                # 處理軟體數據欄位
                row_data = []
                if s_row[0] is not None:
                    row_data.extend([f"{s_row[0]:.6f}", f"{s_row[1]:.8f}", f"{s_row[2]:.4f}"])
                else:
                    row_data.extend(["", "", ""])
                
                row_data.append("") # 分隔欄
                
                # 處理硬體數據欄位
                if h_row[0] is not None:
                    row_data.extend([f"{h_row[0]:.6f}", f"{h_row[1]:.8f}", f"{h_row[2]:.4f}"])
                else:
                    row_data.extend(["", "", ""])
                
                writer.writerow(row_data)
                
        print("儲存成功！")
        
    except Exception as e:
        print(f"儲存失敗: {e}")

# ==========================================
#              主程式
# ==========================================

if __name__ == "__main__":
    # 建立用於接收結果的 Queue
    q_soft = queue.Queue()
    q_hard = queue.Queue()

    # 建立執行緒
    # 使用 Threading 適合 I/O Bound 任務 (等待儀器回應)
    t_soft = threading.Thread(target=task_software_lockin, args=(q_soft,))
    t_hard = threading.Thread(target=task_hardware_sr865a, args=(q_hard,))

    print("=== 開始同步量測實驗 (20s) ===")
    start_time = time.time()

    # 同時啟動
    t_hard.start()
    t_soft.start()

    # 等待結束
    t_hard.join()
    t_soft.join()
    
    print(f"=== 實驗結束 (總耗時: {time.time() - start_time:.2f}s) ===")

    # 取出結果
    res_soft = q_soft.get()
    res_hard = q_hard.get()

    if res_soft is None or res_hard is None:
        print("錯誤: 其中一個測量任務失敗，無法進行比較。")
        exit()

    # 儲存 CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lockin_compare_{timestamp}.csv"
    save_comparison_to_csv(filename, res_soft, res_hard)

    # ==========================================
    #              繪圖比較
    # ==========================================
    plt.figure(figsize=(10, 8))
    
    # 振幅比較 (R)
    plt.subplot(2, 1, 1)
    plt.title(f"Lock-in Comparison (Duration: {DURATION}s, TC: {TIME_CONSTANT}s)")
    
    plt.plot(res_soft['time'], res_soft['R'], label=f"Software (DAQ {DAQ_SAMPLING_RATE}Hz)", 
             color='blue', alpha=0.6, linewidth=1)

    plt.plot(res_hard['time'], res_hard['R'], label=f"Hardware (SR865A {res_hard['fs']}Hz)", 
             color='orange', alpha=0.8, linewidth=1)

    plt.ylabel("Amplitude R (Vrms)")
    plt.grid(True)
    plt.legend()

    # 相位比較 (Theta)
    plt.subplot(2, 1, 2)
    
    plt.plot(res_soft['time'], res_soft['Theta'], label="Software", 
             color='blue', alpha=0.6, linewidth=1)
    
    plt.plot(res_hard['time'], res_hard['Theta'], label="Hardware", 
             color='orange', alpha=0.8, linewidth=1)
    
    plt.ylabel("Phase Theta (deg)")
    plt.xlabel("Time (s)")
    plt.ylim(-180, 180)
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()

    # 簡單統計比較
    print("\n=== 統計比較 ===")
    print(f"Software Avg R: {np.mean(res_soft['R']):.6f} V")
    print(f"Hardware Avg R: {np.mean(res_hard['R']):.6f} V")