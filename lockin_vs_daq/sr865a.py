import numpy as np
from abc_instrument import Instrument
from srsinst.sr860 import SR865A
import pyvisa

class SR865a(Instrument):

    def __init__(self, **kwargs):
        """
        設定連接方式。
        
        Args:
            interface_type (str): 使用介面(serial or visa)。
            port (str): 埠號。
        """
        super().__init__()
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

    def acquire_real_time_data(self)-> float | np.ndarray:
        """
        獲取即時資料
        """
        return self.inst.data.channel_value[3]

    def set_timed_acquisition_params(self, **params):
        """
        設定定時資料擷取的參數。

        Args:
            buffer_size (int): 緩衝區大小。
            time_constant (float): 時間常數，參考SR865a說明書。
            rate_divisor_exponent (int): 速率除數指數，參考SR865a說明書。
        """
        self.buffer_size = params.get('buffer_size', 4096)
        self.time_constant = params.get('time_constant')
        self.rate_divisor_exponent = params.get('rate_divisor_exponent')
        # 設定buffer大小，這會影響到要量測多久
        # 一個X佔4Bytes
        # buffer設4MBytes，量X的話 可以存1024000組
        # buffer設4MBytes，量XY的話 可以存512000組
        # buffer設4MBytes，量r,theta的話 可以存512000組
        # buffer設4MBytes，量X,Y,r,theta的話 可以存256000組
        self.inst.capture.buffer_size_in_kilobytes = params.get('buffer_size', 4096)
        # 設定捕捉模式
        self.inst.capture.config = 'RT'
        # 設定參考光
        self.inst.ref.reference_source = 'external'
        # 設定時間常數
        self.inst.signal.time_constant = self.time_constant
        # 獲取這個時間常數下可獲得的最大頻率
        max = self.inst.capture.max_rate
        self.inst.capture.rate_divisor_exponent = self.rate_divisor_exponent

    def acquire_timed_data(self):
        raise NotImplementedError



    