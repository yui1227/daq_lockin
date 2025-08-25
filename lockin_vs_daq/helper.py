from enum import Enum
from math import ceil

class PointMode(Enum):
    X = 0
    XY = 1
    RTheta = 2
    XYRTheta = 3

    SizeMapping = {
        "X": 1,
        "XY": 2,
        "RTheta": 2,
        "XYRTheta": 4
    }
    def convert(self) -> int:
        """
        將 PointMode 轉換為整數值。
        """
        return PointMode.SizeMapping[self.name]

class Helper:
    """
    Helper class for various utility functions.
    """

    @staticmethod
    def calculate_buffer_size(measurement_time:float, capture_freq:float, mode: PointMode) -> int:
        """
        計算sr865a所需buffer大小。
        
        Args:
            measurement_time: 量測時間，單位為秒。
            capture_freq: 擷取頻率，單位為Hz。
            mode: 擷取模式，PointMode Enum。

        Returns:
            int: 計算出的buffer大小，單位為KBytes。
        """
        return ceil(measurement_time * ceil(capture_freq)*4*mode.convert()/1024)
    
    @staticmethod
    def calculate_rate_divisor_capture_rate_pair(max_capture_rate: float) -> dict[int, float]:
        """
        計算rate_divisor與capture_rate的對應關係。
        
        Args:
            max_capture_rate: 最大擷取頻率，單位為Hz。
        
        Returns:
            dict: 包含rate_divisor與capture_rate的對應關係。
        """
        rate_divisor_capture_rate = {}
        for rate_divisor in range(21):
            capture_rate = max_capture_rate / (2 ** rate_divisor)
            rate_divisor_capture_rate[rate_divisor] = capture_rate
        return rate_divisor_capture_rate

    
    @staticmethod
    def list_daq_devices():
        """
        列出所有可用的DAQ設備。
        
        Returns:
            list: 可用DAQ設備的列表。
        """
        import nidaqmx.system
        return list(nidaqmx.system.System.local().devices.device_names)
    
    @staticmethod
    def list_lockin_devices_visa():
        """
        列出所有可用的Lock-in設備（VISA）。
        
        Returns:
            list: 可用Lock-in設備的列表。
        """
        import pyvisa
        rm = pyvisa.ResourceManager()
        return list(rm.list_resources())
    
    @staticmethod
    def list_lockin_devices_serial():
        """
        列出所有可用的Lock-in設備（串口）。
        
        Returns:
            list: 可用Lock-in設備的列表。
        """
        import serial.tools.list_ports
        return [i.name for i in serial.tools.list_ports.comports()]