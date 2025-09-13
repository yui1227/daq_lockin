import numpy as np
from UI_SoftwareLIA_ui import Ui_SoftwareLIA
from PySide6.QtWidgets import QMainWindow, QListWidgetItem
from PySide6.QtCore import Qt, QThread, Signal
import SoftwareLIA
import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType
from DAQWorker import DAQWorker


class Ui_SoftwareLIA_func(QMainWindow, Ui_SoftwareLIA):
    StartRealTime = Signal(dict)
    StopRealTime = Signal()
    StartRecord = Signal(dict)

    def __init__(self, parent=None):
        super(Ui_SoftwareLIA_func, self).__init__(parent)
        self.setupUi(self)
        self.lockin = SoftwareLIA.LockInAmplifier(fs=1000)
        self.initUi()

        self.worker = DAQWorker()
        self.daq_thread = QThread(self)
        self.StartRealTime.connect(self.worker.get_real_time_data)
        self.StopRealTime.connect(self.worker.stop_real_time)
        self.StartRecord.connect(self.worker.get_record_data)
        self.worker.data_acquired.connect(self.plot_data)
        self.worker.moveToThread(self.daq_thread)
        self.daq_thread.start()

    def initUi(self):
        for dev in nidaqmx.system.System.local().devices:
            self.cmbDAQ.addItem(dev.name)
        self.cmbDAQ.setCurrentIndex(0)

        self.dsbSamplingRate.setValue(self.lockin.fs)
        self.dsbTimeConstant.setValue(self.lockin.time_constant)
        self.sbFilterOrder.setValue(self.lockin.filter_order)
        self.dsbRefFreq.setValue(self.lockin.ref_freq)
        self.dsbRefInitPhase.setValue(self.lockin.ref_phase)

        self.event_bind()

        self.cmbRefSignal.addItems(self.get_all_available_input())

        self.graphicsView.setYRange(min=-10, max=10)

    def spinBoxChanged(self, caller: str, value: int | float):
        if caller == 'fs':
            self.lockin.fs = value
        elif caller == 'time_constant':
            self.lockin.time_constant = value
        elif caller == 'filter_order':
            self.lockin.filter_order = value

    def get_all_available_input(self):
        return ['Internal']+[ch.name for ch in nidaqmx.system.Device(self.cmbDAQ.currentText()).ai_physical_chans]

    def get_selected_input(self):
        return [self.lstSelectedInputSignals.item(idx).text()
                for idx in range(self.lstSelectedInputSignals.count())]

    def event_bind(self):
        self.cmbDAQ.currentTextChanged.connect(self.daq_selected)
        self.cmbRefSignal.currentTextChanged.connect(self.refresh_input_signal)
        self.btnAddInputSignal.clicked.connect(self.add_input)

        self.dsbSamplingRate.valueChanged.connect(
            lambda value: self.spinBoxChanged('fs', value))
        self.dsbTimeConstant.valueChanged.connect(
            lambda value: self.spinBoxChanged('time_constant', value))
        self.sbFilterOrder.valueChanged.connect(
            lambda value: self.spinBoxChanged('filter_order', value))

        self.lstSelectedInputSignals.itemDoubleClicked.connect(
            self.remove_item_double_click)

        self.btnStartRealtime.clicked.connect(self.start_real_time)
        self.btnStartRecordSave.clicked.connect(self.start_record)

    def add_input(self):
        selected_input = self.cmbInputSignal.currentText()
        if selected_input.isspace() or len(selected_input) == 0:
            return
        self.lstSelectedInputSignals.addItem(selected_input)
        idx = self.cmbInputSignal.currentIndex()
        self.cmbInputSignal.removeItem(idx)
        self.set_max_sample_rate()

    def set_max_sample_rate(self):
        if self.lstSelectedInputSignals.count() != 0:
            self.dsbSamplingRate.setMaximum(1e6/self.lstSelectedInputSignals.count())
        else:
            return self.dsbSamplingRate.setMaximum(1e6)

    def daq_selected(self, text):
        # 選好DAQ後，先清空參考訊號，輸入訊號和已選輸入訊號清單，去查詢可用類比輸入，先填到參考訊號
        self.cmbRefSignal.clear()

        all_input = self.get_all_available_input()
        self.cmbRefSignal.addItems(all_input)
        self.cmbRefSignal.setCurrentIndex(0)

        self.refresh_input_signal()

    def refresh_input_signal(self, text=''):
        self.cmbInputSignal.clear()
        ref_signal_items = self.lstSelectedInputSignals.findItems(
            self.cmbRefSignal.currentText(), Qt.MatchFlag.MatchExactly)
        if len(ref_signal_items) > 0:
            row = self.lstSelectedInputSignals.row(ref_signal_items[0])
            self.lstSelectedInputSignals.takeItem(row)
        self.set_max_sample_rate()

        # ref選完之後把剩下的選項加入輸入訊號
        current_ref = self.cmbRefSignal.currentText()
        self.cmbInputSignal.addItems(
            [ch for ch in self.get_all_available_input() if (ch != current_ref) and (ch != 'Internal')])

    def remove_item_double_click(self, item: QListWidgetItem):
        # 獲取被雙擊項目的索引
        row = self.lstSelectedInputSignals.row(item)
        # 使用 takeItem() 移除該索引的項目
        self.lstSelectedInputSignals.takeItem(row)
        # 將被移除的通道加回去
        self.cmbInputSignal.addItem(item.text())
        self.set_max_sample_rate()

    def start_real_time(self):
        sample_setting = {
            "SAMPLE_RATE": self.dsbSamplingRate.value(),
            "SAMPLE_PER_READ": int(self.dsbSamplingRate.value()),
            "daq_name":self.cmbDAQ.currentText(),
            "ref_source": self.cmbRefSignal.currentText(),
            "source": self.get_selected_input(),
        }
        self.StartRealTime.emit(sample_setting)

    def start_record(self):
        sample_setting = {
            "SAMPLE_RATE": self.dsbSamplingRate.value(),
            "MEASUREMENT_DURATION": 0,
            "ref_source": self.cmbRefSignal.currentText(),
            "source": self.get_selected_input(),
        }
        self.StartRecord.emit(sample_setting)

    def plot_data(self, data: np.ndarray):
        if data.ndim ==1:
            self.graphicsView.plotItem.plot(data)
        else:
            for col in data.shape[1]:
                self.graphicsView.plotItem.plot(data[:,col])

    def closeEvent(self, event):
        return super().closeEvent(event)
