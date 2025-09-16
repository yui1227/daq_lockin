from PySide6.QtCore import QObject, Signal
import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np


class DAQWorker(QObject):
    data_acquired = Signal(np.ndarray,str)

    def __init__(self, /, parent=None):
        super(DAQWorker, self).__init__(parent)
        self.is_start_real_time_acquisition = False

    def get_real_time_data(self, data: dict):
        task = nidaqmx.Task()
        ref_source = data["ref_source"]
        # REF
        if ref_source != 'Internal':
            task.ai_channels.add_ai_voltage_chan(
                ref_source, min_val=-10.0, max_val=10.0
            )
        # Input
        for ch in data["source"]:
            task.ai_channels.add_ai_voltage_chan(
                ch, min_val=-10.0, max_val=10.0)
            
        task.timing.cfg_samp_clk_timing(
            rate=data["SAMPLE_RATE"],
            sample_mode=AcquisitionType.CONTINUOUS,  # 連續採樣
            samps_per_chan=data["SAMPLE_PER_READ"]  # 每次讀取點數
        )
        task.start()
        self.is_start_real_time_acquisition = True
        while self.is_start_real_time_acquisition:
            new_data = task.read(data["SAMPLE_PER_READ"])
            if not isinstance(new_data, (list, np.ndarray)):
                new_data = [new_data]
            new_data = np.array(new_data)
            self.data_acquired.emit(new_data,"realtime")
        task.stop()
        task.close()
        
    def stop_real_time(self):
        self.is_start_real_time_acquisition = False

    def get_record_data(self, data: dict):
        task = nidaqmx.Task()
        number_of_samples = int(
            data["SAMPLE_RATE"] * data["MEASUREMENT_DURATION"])
        ref_source = data["ref_source"]
        # REF
        if ref_source != 'Internal':
            task.ai_channels.add_ai_voltage_chan(
                ref_source, min_val=-10.0, max_val=10.0
            )
        # Input
        for ch in data["source"]:
            task.ai_channels.add_ai_voltage_chan(
                ch, min_val=-10.0, max_val=10.0)
            
        task.timing.cfg_samp_clk_timing(
            rate=data["SAMPLE_RATE"],
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=number_of_samples
        )
        task.start()
        task.wait_until_done(
            timeout=data["MEASUREMENT_DURATION"] + 2.0)  # 給予額外的時間裕度
        acquired_data = task.read(
            number_of_samples_per_channel=number_of_samples)
        data_array = np.array(acquired_data)
        task.stop()
        task.close()
        self.data_acquired.emit(data_array,"record")
