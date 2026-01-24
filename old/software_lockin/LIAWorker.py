from typing import Tuple
from PySide6.QtCore import QObject, Signal
import numpy as np
from SoftwareLIA import LockInAmplifier


class LIAWorker(QObject):
    data_calculated = Signal(dict)

    def __init__(self, /, parent=None):
        super(LIAWorker, self).__init__(parent)
        self.lockin = LockInAmplifier(fs=1000)

    def change_LIA_config(self, config: Tuple[str, float | int | str]):
        setattr(self.lockin, config[0], config[1])
        self.lockin._design_filter()

    # def get_lockin_config(self):
    #     return {
    #         "fs": self.lockin.fs,
    #         "time_constant": self.lockin.time_constant,
    #         "ref_source": self.lockin.ref_source,
    #         "ref_freq": self.lockin.ref_freq,
    #         "ref_phase": self.lockin.ref_phase,
    #         "filter_order": self.lockin.filter_order,
    #     }

    def calculate(self, data: np.ndarray, mode: str):
        if self.lockin.ref_source == 'external':
            # 外部參考ref + input一定是2D ndarray
            lock_result = np.apply_along_axis(
                self.lockin.process, axis=1, arr=data[1:, :], ref_signal=data[0, :], mode=mode)
            lock_result: dict[str,np.ndarray] = {
                    "I": np.stack([lock_data["I"] for lock_data in lock_result]),
                    "Q": np.stack([lock_data["Q"] for lock_data in lock_result]),
                    "R": np.stack([lock_data["R"] for lock_data in lock_result]),
                    "theta": np.stack([lock_data["theta"] for lock_data in lock_result]),
                }
            self.data_calculated.emit(lock_result)
        elif self.lockin.ref_source == 'internal':
            if data.ndim == 1:
                # 內部參考搭配單輸入
                lock_result: dict = self.lockin.process(data, [], mode=mode)
                self.data_calculated.emit(lock_result)
            else:
                # 內部參考搭配多輸入
                lock_result: np.ndarray[dict] = np.apply_along_axis(
                    self.lockin.process, axis=1, arr=data, ref_signal=[], mode=mode)
                # 整理，把各自通道的數據整合在一起
                lock_result: dict[str,np.ndarray] = {
                    "I": np.stack([lock_data["I"] for lock_data in lock_result]),
                    "Q": np.stack([lock_data["Q"] for lock_data in lock_result]),
                    "R": np.stack([lock_data["R"] for lock_data in lock_result]),
                    "theta": np.stack([lock_data["theta"] for lock_data in lock_result]),
                }
                self.data_calculated.emit(lock_result)
