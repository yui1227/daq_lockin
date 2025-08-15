import time
import numpy as np
from abc_instrument import Instrument
from srsinst.sr860 import SR865A
import pyvisa
import math

class SR865a(Instrument):
    """SR865a 類別，繼承自 Instrument。
    用於控制 SR865a 鎖相放大器的行為。
    """

    def __init__(self, **kwargs):
        """
        設定連接方式。

        Args:
            interface_type (str): 使用介面(serial or visa)。
            port (str): 埠號。
        """
        super().__init__()
        self.config = kwargs
        self.interface_type = kwargs.get('interface')
        self.port = kwargs.get('port')
        if self.interface_type == 'serial':
            self.inst = SR865A('serial', self.port)
        elif self.interface_type == 'visa':
            rm = pyvisa.ResourceManager()
            self.inst = SR865A('visa', rm.open_resource(self.port))
        else:
            raise ValueError("Invalid interface type. Use 'serial' or 'visa'.")

    def set_real_time_acquisition_params(self, **params):
        """
        設定即時資料擷取的參數。
        """
        self.inst.ref.reference_source = 'external'

    def acquire_real_time_data(self) -> float | np.ndarray:
        """
        獲取即時資料
        """
        return self.inst.data.channel_value[3]

    def set_timed_acquisition_params(self, **params):
        """
        設定定時資料擷取的參數。

        Args:
            time_constant (float): 時間常數，參考SR865a說明書。
            rate_divisor_exponent (int): 速率除數指數，參考SR865a說明書，範圍介於0~20。
            measurement_time (int): 量測時間，單位為秒。
        """
        self.time_constant = params.get('time_constant')
        self.rate_divisor_exponent = params.get('rate_divisor_exponent')
        self.measurement_time = params.get('measurement_time')
        # 設定捕捉模式
        self.inst.capture.config = 'RT'
        # 設定參考光
        self.inst.ref.reference_source = 'external'
        # 設定時間常數
        self.inst.signal.time_constant = self.time_constant
        # 獲取這個時間常數下可獲得的最大頻率
        max = self.inst.capture.max_rate
        self.inst.capture.rate_divisor_exponent = self.rate_divisor_exponent
        current_capture_rate = max/(2**self.rate_divisor_exponent)
        buffer_size = 16*math.ceil(current_capture_rate)*4*2/1024
        self.inst.capture.buffer_size_in_kilobytes = math.ceil(buffer_size)
        self.wait_time_s = buffer_size*1024/math.ceil(current_capture_rate)/2/4

    def acquire_timed_data(self):
        self.inst.capture.start(0,0)
        time.sleep(self.wait_time_s+2)
        data = self.inst.capture.get_all_data()
        return data
