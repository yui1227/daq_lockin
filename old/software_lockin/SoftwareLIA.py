import numpy as np
from scipy.signal import butter, filtfilt, hilbert, lfilter


class LockInAmplifier:
    def __init__(self, fs, time_constant=0.1,
                 ref_source="internal", ref_freq=1000.0, ref_phase=0.0, filter_order=4):
        """
        fs            : 採樣頻率 [Hz]
        time_constant : 低通濾波器時間常數 [s]
        ref_source    : "internal" 或 "external"
        ref_freq      : internal reference 頻率 [Hz]
        ref_phase     : internal reference 初始相位 [rad]
        filter_order  : 低通濾波器階數
        """
        self.fs = fs
        self.time_constant = time_constant
        self.ref_source = ref_source
        self.ref_freq = ref_freq
        self.ref_phase = ref_phase
        self.filter_order = filter_order
        self.b, self.a = self._design_filter()

    def _design_filter(self):
        nyq = 0.5 * self.fs
        fc = 1.0 / (2 * np.pi * self.time_constant)  # cutoff freq ~ 1/(2πτ)
        normal_cutoff = min(fc / nyq, 0.99)
        b, a = butter(self.filter_order, normal_cutoff, btype='low')
        return b, a

    def _lowpass(self, data: np.ndarray, mode: str):
        if mode == "realtime":
            return lfilter(self.b, self.a, data)
        elif mode == "record":
            return filtfilt(self.b, self.a, data)

    def process(self, signal, ref_signal, mode):
        """
        signal: 輸入訊號 (numpy array)
        ref_signal: 參考訊號 (numpy array，和 signal 長度相同)
        mode: 可為"realtime" or "record"
        return: dict 包含 I, Q, R, theta
        """
        if self.ref_source=='external' and len(signal) != len(ref_signal):
            raise ValueError("signal 與 ref 必須長度相同")

        N = len(signal)

        if self.ref_source == 'internal':
            if mode == 'realtime':
                phase_inc = 2*np.pi*self.ref_freq/self.fs
                idx = np.arange(N)
                phase = self.ref_phase + phase_inc * idx
                ref_cos = np.cos(phase)
                ref_sin = np.sin(phase)
                self.ref_phase = (phase[-1]+phase_inc) % (2*np.pi)
            elif mode == "record":
                t = np.arange(N)/self.fs
                ref_cos = np.cos(2*np.pi*self.ref_freq*t + self.ref_phase)
                ref_sin = np.sin(2*np.pi*self.ref_freq*t + self.ref_phase)
        elif self.ref_source == 'external':
            if ref_signal is None:
                raise ValueError(
                    "External reference source requires ref_signal input")
            # Hilbert transform 產生正交參考訊號
            analytic_ref = hilbert(ref_signal)
            ref_cos = np.real(analytic_ref)   # 同相
            ref_sin = np.imag(analytic_ref)   # 正交

        # 混頻
        I_raw = signal * ref_cos
        Q_raw = signal * ref_sin

        # 低通濾波
        I = self._lowpass(I_raw, mode)
        Q = self._lowpass(Q_raw, mode)

        # 幅度與相位
        R = np.sqrt(I**2 + Q**2)
        theta = np.arctan2(Q, I)

        return {
            "I": I,
            "Q": Q,
            "R": R,
            "theta": theta
        }
