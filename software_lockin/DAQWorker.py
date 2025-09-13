from PySide6.QtCore import QObject, Signal
import nidaqmx
import numpy as np


class DAQWorker(QObject):
    data_acquired = Signal(np.ndarray)

    def __init__(self, /, parent=None):
        super(DAQWorker, self).__init__(parent)

    def get_read_time_data(self, data: dict):
        task = nidaqmx.Task()
        daq_name = data["daq_name"]
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
        new_data = task.read(data["SAMPLE_PER_READ"])
        if not isinstance(new_data, (list, np.ndarray)):
            new_data = [new_data]
        new_data = np.array(new_data)
        self.data_acquired.emit(new_data)

    def get_record_data(self):
        pass
