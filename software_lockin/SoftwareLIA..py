import numpy as np
from scipy.signal import butter, filtfilt, hilbert

class LockInAmplifier:
    def __init__(self, fs, cutoff=10.0, order=4):
        """
        fs: 取樣率 (Hz)
        cutoff: 低通濾波器截止頻率 (Hz)
        order: 濾波器階數
        """
        self.fs = fs
        self.cutoff = cutoff
        self.order = order
        self.b, self.a = self._design_filter()

    def _design_filter(self):
        nyquist = 0.5 * self.fs
        normal_cutoff = self.cutoff / nyquist
        b, a = butter(self.order, normal_cutoff, btype='low', analog=False)
        return b, a

    def _lowpass(self, data):
        return filtfilt(self.b, self.a, data)

    def process(self, signal, ref):
        """
        signal: 輸入訊號 (numpy array)
        ref: 參考訊號 (numpy array，和 signal 長度相同)
        return: dict 包含 I, Q, R, theta
        """
        if len(signal) != len(ref):
            raise ValueError("signal 與 ref 必須長度相同")

        # Hilbert transform 產生正交參考訊號
        analytic_ref = hilbert(ref)
        ref_cos = np.real(analytic_ref)   # 同相
        ref_sin = np.imag(analytic_ref)   # 正交

        # 混頻
        I_raw = signal * ref_cos
        Q_raw = signal * ref_sin

        # 低通濾波
        I = self._lowpass(I_raw)
        Q = self._lowpass(Q_raw)

        # 幅度與相位
        R = np.sqrt(I**2 + Q**2)
        theta = np.arctan2(Q, I)

        return {
            "I": I,
            "Q": Q,
            "R": R,
            "theta": theta
        }
