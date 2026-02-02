import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import time
from datetime import datetime
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 匯入您的核心運算庫
try:
    from lockin_lib import SoftwareLockInAmplifier
except ImportError:
    messagebox.showerror("錯誤", "找不到 lockin_lib.py，請確保它在同一個資料夾中")
    exit()

# 嘗試匯入 NI DAQ，如果沒有安裝則只能用模擬模式
try:
    import nidaqmx
    from nidaqmx.constants import AcquisitionType, TerminalConfiguration
    NIDAQ_AVAILABLE = True
except ImportError:
    NIDAQ_AVAILABLE = False


class LockinApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python 軟體鎖相放大器 (NI DAQ)")
        self.root.geometry("1000x800")

        # --- 變數儲存 ---
        self.sim_mode = tk.BooleanVar(value=False)  # 預設關閉模擬模式
        self.data_store = None  # 用來暫存數據以便存檔
        self.voltage_range = tk.DoubleVar(value=10.0)

        # --- 建立控制面板 ---
        control_frame = ttk.LabelFrame(root, text="控制參數", padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 參數輸入區
        self.create_input(control_frame, "採樣率 (Hz):", "10000", 0, 0)
        self.create_input(control_frame, "擷取時間 (s):", "10.0", 0, 1)
        self.create_input(control_frame, "時間常數 (s):", "0.001", 0, 2)

        # 設備設定
        self.create_input(control_frame, "設備名稱:", "Dev1", 1, 0)
        self.create_input(control_frame, "參考通道:", "ai7", 1, 1)
        self.create_input(control_frame, "訊號通道 (逗號隔開):", "ai19", 1, 2)

        range_frame = ttk.LabelFrame(
            control_frame, text="訊號通道輸入範圍 (Signal Input Range)")
        range_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        ranges = [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]
        for val in ranges:
            # 建立單選鈕
            rb = ttk.Radiobutton(
                range_frame,
                text=f"±{val} V",
                variable=self.voltage_range,
                value=val
            )
            rb.pack(side=tk.LEFT, padx=10, pady=5)

        # 按鈕區
        btn_frame = ttk.Frame(control_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.chk_sim = ttk.Checkbutton(
            btn_frame, text="模擬模式 (無硬體)", variable=self.sim_mode)
        self.chk_sim.pack(side=tk.LEFT, padx=10)

        self.btn_run = ttk.Button(
            btn_frame, text="開始擷取並分析", command=self.run_acquisition)
        self.btn_run.pack(side=tk.LEFT, padx=10)

        self.btn_save = ttk.Button(
            btn_frame, text="儲存數據 (.csv)", command=self.save_data, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT, padx=10)

        self.lbl_status = ttk.Label(btn_frame, text="就緒", foreground="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=20)

        # --- 建立繪圖區 ---
        self.fig, self.axs = plt.subplots(3, 1, figsize=(8, 8), sharex=True)
        plt.subplots_adjust(hspace=0.3)

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH,
                                         expand=True, padx=10, pady=5)

        # 初始化圖表標籤
        self.axs[0].set_title("原始訊號 (Raw)")
        self.axs[0].set_ylabel("Voltage (V)")
        self.axs[1].set_title("解調振幅 (R)")
        self.axs[1].set_ylabel("Amplitude (V)")
        self.axs[2].set_title("解調相位 (Theta)")
        self.axs[2].set_ylabel("Phase (deg)")
        self.axs[2].set_xlabel("Time (s)")

    def create_input(self, parent, label_text, default_val, r, c):
        frame = ttk.Frame(parent)
        frame.grid(row=r, column=c, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text=label_text).pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=15)
        entry.insert(0, default_val)
        entry.pack(side=tk.LEFT, padx=5)

        # 將 Entry 物件存入字典，以便稍後讀取
        attr_name = label_text.split(":")[0]  # 簡單用標籤當 key
        if not hasattr(self, 'inputs'):
            self.inputs = {}
        self.inputs[attr_name] = entry

    def get_input(self, name):
        return self.inputs[name].get()

    def run_acquisition(self):
        # 1. 讀取參數
        try:
            fs = float(self.get_input("採樣率 (Hz)"))
            duration = float(self.get_input("擷取時間 (s)"))
            tau = float(self.get_input("時間常數 (s)"))
            dev_name = self.get_input("設備名稱")
            ref_ch = self.get_input("參考通道")
            sig_chs_str = self.get_input("訊號通道 (逗號隔開)")
            sig_chs = [s.strip() for s in sig_chs_str.split(",")]
            selected_range = self.voltage_range.get()
        except ValueError:
            messagebox.showerror("錯誤", "輸入參數格式錯誤")
            return

        self.lbl_status.config(text="正在擷取...", foreground="red")
        self.root.update()  # 強制更新介面顯示

        # 2. 擷取數據 (模擬 或 真實)
        if self.sim_mode.get():
            data, n_samples = self.generate_mock_data(
                fs, duration, len(sig_chs))
        else:
            if not NIDAQ_AVAILABLE:
                messagebox.showerror("錯誤", "未安裝 nidaqmx 套件，無法執行硬體擷取。")
                self.lbl_status.config(text="錯誤", foreground="red")
                return
            data, n_samples = self.acquire_real_data(
                fs, duration, dev_name, ref_ch, sig_chs, selected_range)
            if data is None:
                self.lbl_status.config(text="擷取失敗", foreground="red")
                return

        # 3. 執行鎖相放大運算
        self.lbl_status.config(text="正在運算...", foreground="orange")
        self.root.update()

        lia = SoftwareLockInAmplifier(fs)

        # 分離通道 (Row 0 是參考, 之後是訊號)
        ref_data = data[0, :]
        sig_data_list = data[1:, :]

        # A. 分析參考頻率
        ref_sin, ref_cos, freq = lia.generate_reference_oscillator(ref_data)

        # B. 解調所有通道
        results = []
        for i, sig in enumerate(sig_data_list):
            r, theta = lia.process_channel(sig, ref_sin, ref_cos, tau)
            results.append({
                "name": sig_chs[i],
                "raw": sig,
                "R": r,
                "Theta": theta
            })

        # 4. 更新繪圖
        t = np.arange(n_samples) / fs

        # 清除舊圖
        for ax in self.axs:
            ax.cla()

        # 繪製參考訊號 (只畫前段以免太密)
        # zoom = min(1000, n_samples)
        # self.axs[0].plot(t[:zoom], ref_data[:zoom], 'k', alpha=0.5, label='Ref (Zoom)')
        self.axs[0].plot(t, ref_data, 'k', alpha=0.5,
                         label='Ref')

        # 繪製各通道結果
        colors = ['b', 'r', 'g', 'm']
        for i, res in enumerate(results):
            c = colors[i % len(colors)]
            # 原始訊號
            self.axs[0].plot(t, res["raw"], c=c,
                             label=f'{res["name"]} Raw')
            # self.axs[0].plot(t[:zoom], res["raw"][:zoom], c=c, label=f'{res["name"]} Raw')
            # 振幅
            self.axs[1].plot(t, res["R"], c=c,
                             label=res["name"])
            # 相位
            self.axs[2].plot(t, res["Theta"], c=c,
                             label=res["name"])

        # 設定圖表標籤
        self.axs[0].set_title(
            f"原始訊號 (Ref Freq: {freq:.2f}Hz, Range: ±{selected_range}V)")
        self.axs[0].legend(loc='upper right', fontsize='small')
        self.axs[1].set_title("解調振幅 (R)")
        self.axs[1].legend(loc='upper right', fontsize='small')
        self.axs[2].set_title("解調相位 (Theta)")
        self.axs[2].set_xlabel("Time (s)")

        self.canvas.draw()

        # 5. 儲存數據到記憶體，準備存檔
        self.data_store = {
            "time": t,
            "ref_raw": ref_data,
            "results": results,
            "params": {"fs": fs, "tau": tau, "freq": freq, "range": selected_range}
        }

        self.btn_save.config(state=tk.NORMAL)
        self.lbl_status.config(
            text=f"完成 (Ref: {freq:.2f}Hz)", foreground="green")

    def save_data(self):
        if not self.data_store:
            return

        # 開啟存檔對話框
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="儲存實驗數據"
        )

        if not filename:
            return

        try:
            # 準備寫入 CSV
            t = self.data_store["time"]
            results = self.data_store["results"]

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # # 寫入檔頭資訊
                # writer.writerow(["# Experiment Data", datetime.now().isoformat()])
                # writer.writerow(["# Sampling Rate", self.data_store["params"]["fs"]])
                # writer.writerow(["# Ref Freq", self.data_store["params"]["freq"]])
                # writer.writerow(["# Time Constant", self.data_store["params"]["tau"]])
                # writer.writerow(["# Voltage Range", f"±{self.data_store['params']['range']} V"])
                # writer.writerow([]) # 空行

                # 建立欄位名稱
                header = ["Time(s)", "Ref_Raw(V)"]
                for res in results:
                    name = res["name"]
                    header.extend(
                        [f"{name}_Raw(V)", f"{name}_R(V)", f"{name}_Theta(deg)"])
                writer.writerow(header)

                # 逐行寫入數據
                # 為了寫入效率，這裡轉置一下數據結構
                rows = len(t)
                for i in range(rows):
                    row_data = [t[i], self.data_store["ref_raw"][i]]
                    for res in results:
                        row_data.append(res["raw"][i])
                        row_data.append(res["R"][i])
                        row_data.append(res["Theta"][i])
                    writer.writerow(row_data)

            messagebox.showinfo("成功", f"數據已儲存至:\n{filename}")

        except Exception as e:
            messagebox.showerror("存檔失敗", str(e))

    def generate_mock_data(self, fs, duration, num_sigs):
        # 產生模擬數據
        n = int(fs * duration)
        t = np.arange(n) / fs
        freq = 1000.0  # 1kHz

        # 參考
        ref = np.sin(2*np.pi*freq*t) + 0.1*np.random.randn(n)

        data_list = [ref]
        for i in range(num_sigs):
            # 產生不同相位的訊號
            phase = np.radians(45 * (i+1))
            amp = 0.5 / (i+1)
            sig = amp * np.sin(2*np.pi*freq*t + phase) + 0.2*np.random.randn(n)
            data_list.append(sig)

        return np.vstack(data_list), n

    def acquire_real_data(self, fs, duration, dev, ref_ch, sig_chs, vol_range):
        # 真實 NI DAQ 擷取
        try:
            with nidaqmx.Task() as task:
                # 設定通道
                task.ai_channels.add_ai_voltage_chan(
                    f"{dev}/{ref_ch}", min_val=-vol_range, max_val=vol_range, terminal_config=TerminalConfiguration.DIFF)
                for ch in sig_chs:
                    task.ai_channels.add_ai_voltage_chan(
                        f"{dev}/{ch}", min_val=-vol_range, max_val=vol_range, terminal_config=TerminalConfiguration.DIFF)

                n_samples = int(fs * duration)
                task.timing.cfg_samp_clk_timing(
                    rate=fs,
                    sample_mode=AcquisitionType.FINITE,
                    samps_per_chan=n_samples
                )

                data = task.read(
                    number_of_samples_per_channel=n_samples, timeout=duration+5.0)
                return np.array(data), n_samples
        except Exception as e:
            messagebox.showerror("DAQ 錯誤", str(e))
            return None, 0


if __name__ == "__main__":
    root = tk.Tk()
    app = LockinApp(root)
    root.mainloop()
