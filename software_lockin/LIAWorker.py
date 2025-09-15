from typing import Tuple
from PySide6.QtCore import QObject, Signal
import numpy as np
from SoftwareLIA import LockInAmplifier


class LIAWorker(QObject):
    data_calculated = Signal(np.ndarray)
    query_lockin_config = Signal(dict)

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

    def caluclate(self, data: np.ndarray):
        if self.lockin.ref_source == 'external':
            lock_result = np.apply_along_axis(self.lockin.process,axis=1,arr=data[1:,:],t=0,ref_signal=data[0,:])
            self.data_calculated.emit(lock_result)
        elif self.lockin.ref_source == 'internal':

            self.data_calculated.emit(data)
        
