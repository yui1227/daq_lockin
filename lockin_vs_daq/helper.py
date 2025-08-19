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
        return ceil(measurement_time * ceil(capture_freq)*4*PointMode.convert(mode)/1024)
    
    @staticmethod
    def list_daq_devices() -> list:
        """
        列出所有可用的DAQ設備。
        
        Returns:
            list: 可用DAQ設備的列表。
        """
        import nidaqmx.system
        return nidaqmx.system.System.local().devices
    
    @staticmethod
    def list_lockin_devices_visa() -> list:
        """
        列出所有可用的Lock-in設備（VISA）。
        
        Returns:
            list: 可用Lock-in設備的列表。
        """
        import pyvisa
        rm = pyvisa.ResourceManager()
        return rm.list_resources()
    
    @staticmethod
    def list_lockin_devices_serial() -> list:
        """
        列出所有可用的Lock-in設備（串口）。
        
        Returns:
            list: 可用Lock-in設備的列表。
        """
        import serial.tools.list_ports
        return serial.tools.list_ports.comports()