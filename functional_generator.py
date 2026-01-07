import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv

class SignalGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 訊號產生器 (Signal Generator)")
        self.root.geometry("1000x700")

        # --- 初始參數設定 ---
        self.freq_var = tk.DoubleVar(value=5.0)       # 頻率 (Hz)
        self.amp_var = tk.DoubleVar(value=1.0)        # 振幅 (V)
        self.offset_var = tk.DoubleVar(value=0.0)     # 偏移 (V)
        self.phase_var = tk.DoubleVar(value=0.0)      # 相位 (度)
        self.duration_var = tk.DoubleVar(value=1.0)   # 持續時間 (秒)
        self.rate_var = tk.IntVar(value=1000)         # 取樣率 (Hz)
        self.noise_var = tk.DoubleVar(value=0.0)      # 雜訊強度
        self.waveform_var = tk.StringVar(value="Sine") # 波形類型

        # 產生的數據緩存
        self.t = None
        self.y = None

        # --- 建立 GUI 佈局 ---
        self.create_widgets()
        
        # 初始繪圖
        self.update_signal()

    def create_widgets(self):
        # 左側控制面板
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(control_frame, text="參數設定", font=("Arial", 14, "bold")).pack(pady=10)

        # 輔助函式：快速建立滑桿與輸入框
        def create_input(label_text, variable, from_, to_, resolution=0.1, command=None):
            frame = ttk.Frame(control_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=label_text).pack(anchor="w")
            
            # 滑桿
            scale = ttk.Scale(frame, from_=from_, to=to_, variable=variable, orient="horizontal", command=command)
            scale.pack(fill=tk.X)
            
            # 數字輸入框 (Spinbox)
            spin = ttk.Spinbox(frame, from_=from_, to=to_, increment=resolution, textvariable=variable, command=self.update_signal)
            # 綁定 Enter 鍵更新
            spin.bind('<Return>', lambda e: self.update_signal())
            spin.pack(fill=tk.X)

        # 1. 波形選擇
        ttk.Label(control_frame, text="波形類型 (Waveform):").pack(anchor="w", pady=(10, 0))
        waveform_cb = ttk.Combobox(control_frame, textvariable=self.waveform_var, state="readonly")
        waveform_cb['values'] = ("Sine", "Square", "Triangle", "Sawtooth")
        waveform_cb.bind("<<ComboboxSelected>>", lambda e: self.update_signal())
        waveform_cb.pack(fill=tk.X, pady=5)

        # 2. 各項參數滑桿
        create_input("頻率 (Frequency, Hz):", self.freq_var, 0.1, 100.0, 0.1, lambda e: self.update_signal())
        create_input("振幅 (Amplitude, V):", self.amp_var, 0.1, 10.0, 0.1, lambda e: self.update_signal())
        create_input("偏移 (Offset, V):", self.offset_var, -5.0, 5.0, 0.1, lambda e: self.update_signal())
        create_input("相位 (Phase, Deg):", self.phase_var, 0.0, 360.0, 10.0, lambda e: self.update_signal())
        create_input("雜訊 (Noise Level):", self.noise_var, 0.0, 1.0, 0.01, lambda e: self.update_signal())
        
        # 3. 取樣設定 (不使用滑桿，僅數字輸入)
        ttk.Separator(control_frame, orient='horizontal').pack(fill='x', pady=10)
        ttk.Label(control_frame, text="時間與取樣:").pack(anchor="w")
        
        time_frame = ttk.Frame(control_frame)
        time_frame.pack(fill=tk.X, pady=2)
        ttk.Label(time_frame, text="時長 (Sec):").pack(side=tk.LEFT)
        ttk.Entry(time_frame, textvariable=self.duration_var, width=8).pack(side=tk.RIGHT)
        
        rate_frame = ttk.Frame(control_frame)
        rate_frame.pack(fill=tk.X, pady=2)
        ttk.Label(rate_frame, text="取樣率 (Hz):").pack(side=tk.LEFT)
        ttk.Entry(rate_frame, textvariable=self.rate_var, width=8).pack(side=tk.RIGHT)
        
        # 按鈕區域
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=20)

        ttk.Button(btn_frame, text="更新預覽 (Update)", command=self.update_signal).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="儲存數據 (Save CSV)", command=self.save_csv).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="儲存圖表 (Save Plot)", command=self.save_plot).pack(fill=tk.X, pady=2)

        # 右側繪圖區域
        plot_frame = ttk.Frame(self.root)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def generate_waveform(self):
        """核心訊號產生邏輯"""
        try:
            F = self.freq_var.get()
            A = self.amp_var.get()
            Offset = self.offset_var.get()
            P_deg = self.phase_var.get()
            Duration = self.duration_var.get()
            Fs = self.rate_var.get()
            Noise = self.noise_var.get()
            Type = self.waveform_var.get()

            # 時間向量
            num_samples = int(Duration * Fs)
            t = np.linspace(0, Duration, num_samples, endpoint=False)
            
            # 將相位轉換為弧度
            phi = np.deg2rad(P_deg)
            # 角頻率
            omega = 2 * np.pi * F

            # 產生基礎波形
            if Type == "Sine":
                y = A * np.sin(omega * t + phi)
            elif Type == "Square":
                # 使用 sign(sin(...)) 產生方波
                y = A * np.sign(np.sin(omega * t + phi))
            elif Type == "Triangle":
                # 使用 arcsin(sin(...)) 產生精確三角波
                y = (2 * A / np.pi) * np.arcsin(np.sin(omega * t + phi))
            elif Type == "Sawtooth":
                # 鋸齒波公式
                # 週期 T = 1/F
                # (t * F + phase_shift) % 1  產生 0~1 的斜坡
                # 再調整為 -1 ~ 1
                phase_shift = P_deg / 360.0
                y = 2 * A * ((t * F + phase_shift) % 1) - A
            else:
                y = np.zeros_like(t)

            # 加入偏移
            y += Offset

            # 加入雜訊 (高斯分佈)
            if Noise > 0:
                noise_signal = np.random.normal(0, Noise, len(t))
                y += noise_signal

            return t, y

        except Exception as e:
            print(f"Error generating signal: {e}")
            return None, None

    def update_signal(self):
        """更新圖表"""
        t, y = self.generate_waveform()
        
        if t is None or y is None:
            return

        # 儲存到物件變數供儲存使用
        self.t = t
        self.y = y

        self.ax.clear()
        self.ax.plot(t, y, color='blue', linewidth=1.5, label='Signal')
        self.ax.set_title(f"Waveform Preview ({self.waveform_var.get()})")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Amplitude (V)")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.legend(loc='upper right')
        
        # 為了視覺效果，如果時間很長，只限制顯示前幾個週期或固定區間，
        # 除非使用者想看全部。這裡我們自動調整 X 軸範圍。
        # 如果頻率很高，顯示太多週期會變成一團色塊，這裡做一點智慧縮放
        freq = self.freq_var.get()
        if freq > 0 and self.duration_var.get() > (5/freq):
             # 如果總時長超過 5 個週期，預設縮放到顯示前 5 個週期方便觀察波形細節
             # 使用者仍可透過 Matplotlib 的工具列進行縮放，但這裡設定預設視圖
             self.ax.set_xlim(0, 5/freq)
        else:
             self.ax.set_xlim(0, self.duration_var.get())

        self.canvas.draw()

    def save_csv(self):
        """儲存數據為 CSV"""
        if self.t is None or self.y is None:
            messagebox.showwarning("警告", "沒有數據可儲存！")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            title="儲存波形數據"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Time (s)", "Amplitude (V)"])
                    # 使用 zip 打包寫入
                    writer.writerows(zip(self.t, self.y))
                messagebox.showinfo("成功", f"檔案已儲存至：\n{filepath}")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗：{e}")

    def save_plot(self):
        """儲存圖表為圖片"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("All Files", "*.*")],
            title="儲存波形圖表"
        )
        
        if filepath:
            try:
                self.fig.savefig(filepath)
                messagebox.showinfo("成功", f"圖片已儲存至：\n{filepath}")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗：{e}")

if __name__ == "__main__":
    root = tk.Tk()
    # 設定一些樣式
    style = ttk.Style()
    style.theme_use('clam') # 使用較現代的風格
    
    app = SignalGeneratorApp(root)
    root.mainloop()