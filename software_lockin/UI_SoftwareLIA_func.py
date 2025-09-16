import numpy as np
from UI_SoftwareLIA_ui import Ui_SoftwareLIA
from PySide6.QtWidgets import QMainWindow, QListWidgetItem
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QCloseEvent
import SoftwareLIA
import nidaqmx
import nidaqmx.system
from nidaqmx.constants import AcquisitionType
from DAQWorker import DAQWorker
from LIAWorker import LIAWorker


class Ui_SoftwareLIA_func(QMainWindow, Ui_SoftwareLIA):
    StartRealTime = Signal(dict)
    StopRealTime = Signal()
    StartRecord = Signal(dict)
    LockinSettingChanged = Signal(tuple)

    def __init__(self, parent=None):
        super(Ui_SoftwareLIA_func, self).__init__(parent)
        self.setupUi(self)
        # self.lockin = SoftwareLIA.LockInAmplifier(fs=1000)

        self.daq_worker = DAQWorker()
        self.daq_thread = QThread(self)
        self.StartRealTime.connect(self.daq_worker.get_real_time_data)
        self.StopRealTime.connect(self.daq_worker.stop_real_time)
        self.StartRecord.connect(self.daq_worker.get_record_data)
        # self.daq_worker.data_acquired.connect(self.plot_data)

        self.lia_worker = LIAWorker()
        self.lia_thread = QThread(self)
        self.LockinSettingChanged.connect(self.lia_worker.change_LIA_config)
        self.daq_worker.data_acquired.connect(self.lia_worker.caluclate)
        self.lia_worker.data_calculated.connect(self.plot_data)
        # 放在這邊是因為有一些鎖相數值需要填到視窗
        self.initUi()

        self.daq_worker.moveToThread(self.daq_thread)
        self.lia_worker.moveToThread(self.lia_thread)
        self.daq_thread.start()
        self.lia_thread.start()
        self.color_list = [
            (255, 0, 0),    # 紅
            (0, 255, 0),    # 綠
            (0, 0, 255),    # 藍
            (255, 255, 0),  # 黃
            (0, 255, 255),  # 青
            (255, 0, 255),  # 紫
            (255, 128, 0)   # 橘
        ]

    def initUi(self):
        for dev in nidaqmx.system.System.local().devices:
            self.cmbDAQ.addItem(dev.name)
        self.event_bind()

        self.cmbDAQ.setCurrentIndex(0)
        self.dsbSamplingRate.setValue(self.lia_worker.lockin.fs)
        self.dsbTimeConstant.setValue(self.lia_worker.lockin.time_constant)
        self.sbFilterOrder.setValue(self.lia_worker.lockin.filter_order)
        self.dsbRefFreq.setValue(self.lia_worker.lockin.ref_freq)
        self.dsbRefPhase.setValue(self.lia_worker.lockin.ref_phase)

        self.cmbRefSignal.addItems(self.get_all_available_input())

        self.graphicsView.setYRange(min=-10, max=10)

    def spinBoxChanged(self, caller: str, value: int | float):
        self.LockinSettingChanged.emit((caller, value))

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
        self.dsbRefFreq.valueChanged.connect(
            lambda value: self.spinBoxChanged('ref_freq', value))
        self.dsbRefPhase.valueChanged.connect(
            lambda value: self.spinBoxChanged('ref_phase', value))

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
            self.dsbSamplingRate.setMaximum(
                1e6/self.lstSelectedInputSignals.count())
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

        ref_source = 'external' if self.cmbRefSignal.currentText() != 'Internal' else 'internal'
        self.LockinSettingChanged.emit(('ref_source', ref_source))

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
            "SAMPLE_PER_READ": int(self.dsbSamplingRate.value()/10),
            "daq_name": self.cmbDAQ.currentText(),
            "ref_source": self.cmbRefSignal.currentText(),
            "source": self.get_selected_input(),
        }
        self.graphicsView.plotItem.addLegend()

        self.curves = [
            self.graphicsView.plotItem.plot(
                name=source,
                pen=self.color_list[idx % len(self.color_list)],
                symbolPen=self.color_list[idx % len(self.color_list)])
            for idx, source in enumerate(self.get_selected_input())
        ]
        
        self.StartRealTime.emit(sample_setting)

    def start_record(self):
        sample_setting = {
            "SAMPLE_RATE": self.dsbSamplingRate.value(),
            "MEASUREMENT_DURATION": 0,
            "ref_source": self.cmbRefSignal.currentText(),
            "source": self.get_selected_input(),
        }
        self.graphicsView.plotItem.addLegend()

        self.curves = [
            self.graphicsView.plotItem.plot(
                name=source,
                pen=self.color_list[idx % len(self.color_list)],
                symbolPen=self.color_list[idx % len(self.color_list)])
            for idx, source in enumerate(self.get_selected_input())
        ]

        self.StartRecord.emit(sample_setting)

    def plot_data(self, data: dict[str, np.ndarray]):
        if data["theta"].ndim == 1:
            self.curves[0].setData(data["theta"])
        else:
            start = 0 if self.cmbRefSignal.currentText() == 'Internal' else 1
            for row in range(start, data["theta"].shape[0]):
                self.curves[row-start].setData(data["theta"][row, :])

    def closeEvent(self, event: QCloseEvent):
        self.StopRealTime.emit()
        self.daq_thread.exit(0)
        event.accept()
        return super().closeEvent(event)
