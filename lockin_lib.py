import numpy as np
from scipy.signal import butter, filtfilt

class SoftwareLockInAmplifier:
    """
    軟體鎖相放大器核心類別
    負責處理已經數位化的數據陣列，不涉及硬體控制。
    """
    def __init__(self, sampling_rate):
        """
        初始化
        :param sampling_rate: 數據的採樣率 (Hz)
        """
        self.fs = sampling_rate

    def generate_reference_oscillator(self, ref_channel_data):
        """
        步驟 1: 分析參考通道
        從參考通道數據中提取主頻率，並生成標準的正弦(Sin)與餘弦(Cos)波。
        
        :param ref_channel_data: 參考通道的原始數據陣列 (numpy array)
        :return: (ref_sin, ref_cos, detected_freq)
        """
        # 去除 DC 偏移，只看交流成分
        ref_ac = ref_channel_data - np.mean(ref_channel_data)
        
        # 使用 FFT 找到主頻率
        n = len(ref_ac)
        freqs = np.fft.fftfreq(n, d=1/self.fs)
        fft_vals = np.fft.fft(ref_ac)
        
        # 只看正頻率部分，找到振幅最大的頻點
        positive_freqs = freqs[:n//2]
        positive_magnitude = np.abs(fft_vals[:n//2])
        peak_idx = np.argmax(positive_magnitude)
        detected_freq = positive_freqs[peak_idx]
        
        # 找初始相位
        t = np.arange(n) / self.fs
        test_sin = np.sin(2 * np.pi * detected_freq * t)
        test_cos = np.cos(2 * np.pi * detected_freq * t)
        
        # 利用鎖相原理計算參考通道本身相對於標準波的相位差
        # 這裡不需濾波，直接積分(平均)即可得到粗略相位
        x_ref = np.mean(ref_ac * test_sin)
        y_ref = np.mean(ref_ac * test_cos)
        ref_phase_offset = np.arctan2(y_ref, x_ref)
        
        # 生成對齊後的參考波
        # 將計算出的偏移量加回去，這樣 generated_sin 就會跟 ref_channel_data 同步
        # 這樣做完，Reference 通道的相位理論上會變成 0 (或接近 0)
        # 而其他 Signal 通道的相位就會是真實的 "相對相位"
        # 注意：這裡的符號修正取決於 sin/cos 定義，
        # 為了讓 Ref Channel 解調後相位歸零，我們讓生成的波帶有同樣的偏移
        ref_sin_aligned = np.sin(2 * np.pi * detected_freq * t + ref_phase_offset)
        ref_cos_aligned = np.cos(2 * np.pi * detected_freq * t + ref_phase_offset)
        
        return ref_sin_aligned, ref_cos_aligned, detected_freq

    def _butter_lowpass_filter(self, data, cutoff, order=4):
        """
        內部函數：低通濾波器 implementation
        """
        nyquist = 0.5 * self.fs
        normal_cutoff = cutoff / nyquist
        # 避免 cutoff 超過 Nyquist 頻率導致錯誤
        if normal_cutoff >= 1:
            normal_cutoff = 0.99
            
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        # 使用 filtfilt 進行零相位濾波 (Zero-phase filtering)
        y = filtfilt(b, a, data)
        return y

    def process_channel(self, signal_data, ref_sin, ref_cos, time_constant_sec):
        """
        步驟 2: 處理訊號通道 (解調)
        
        :param signal_data: 輸入訊號的數據陣列 (numpy array)
        :param ref_sin: 由 generate_reference_oscillator 生成的正弦波
        :param ref_cos: 由 generate_reference_oscillator 生成的餘弦波
        :param time_constant_sec: 積分時間常數 (秒)，決定濾波器的頻寬
        :return: (R, Theta) 振幅陣列與相位陣列
        """
        # 計算截止頻率 f_c = 1 / (2 * pi * tau)
        cutoff_freq = 1 / (2 * np.pi * time_constant_sec)
        
        # 混頻 (Mixing)
        # 乘以 2 是為了補償 sin^2 的平均值 0.5，還原真實振幅
        x_raw = signal_data * ref_sin * 2
        y_raw = signal_data * ref_cos * 2
        
        # 低通濾波 (Low Pass Filter)
        x_filtered = self._butter_lowpass_filter(x_raw, cutoff_freq)
        y_filtered = self._butter_lowpass_filter(y_raw, cutoff_freq)
        
        # 計算振幅 R 和 相位 Theta
        r = np.sqrt(x_filtered**2 + y_filtered**2)
        # 計算相位 (弧度轉角度)
        theta = np.arctan2(y_filtered, x_filtered) * (180 / np.pi)
        
        return r, theta