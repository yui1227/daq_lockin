from UI_SoftwareLIA_ui import Ui_SoftwareLIA
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
import SoftwareLIA
import nidaqmx
import nidaqmx.system


class Ui_SoftwareLIA_func(QMainWindow, Ui_SoftwareLIA):
    def __init__(self, parent=None):
        super(Ui_SoftwareLIA_func, self).__init__(parent)
        self.setupUi(self)
        self.lockin = SoftwareLIA.LockInAmplifier(fs=1000)
        self.initUi()

    def initUi(self):
        # for dev in nidaqmx.system.System.local().devices:
        #     self.cmbDAQ.addItems(dev.name)
        # self.cmbDAQ.setCurrentIndex(0)

        self.dsbSamplingRate.setValue(self.lockin.fs)
        self.dsbTimeConstant.setValue(self.lockin.time_constant)
        self.sbFilterOrder.setValue(self.lockin.filter_order)
        self.dsbRefFreq.setValue(self.lockin.ref_freq)
        self.dsbRefInitPhase.setValue(self.lockin.ref_phase)

        self.event_bind()

        # self.cmbRefSignal.addItems(self.get_all_input())

    def spinBoxChanged(self, caller: str, value: int | float):
        if caller == 'fs':
            self.lockin.fs = value
        elif caller == 'time_constant':
            self.lockin.time_constant = value
        elif caller == 'filter_order':
            self.lockin.filter_order = value

    def get_all_input(self):
        return ['Internal']+[ch.name for ch in nidaqmx.system.Device(self.cmbDAQ.currentText()).ai_physical_chans]

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

    def add_input(self):
        self.lstSelectedInputSignals.addItem(self.cmbInputSignal.currentText())

    def daq_selected(self, text):
        # 選好DAQ後，先清空參考訊號，輸入訊號和已選輸入訊號清單，去查詢可用類比輸入，先填到參考訊號
        self.cmbRefSignal.clear()

        all_input = self.get_all_input()
        self.cmbRefSignal.addItems(all_input)
        self.cmbRefSignal.setCurrentIndex(0)

        self.refresh_input_signal()

    def refresh_input_signal(self, text=''):
        self.cmbInputSignal.clear()
        # self.lstSelectedInputSignals.clear()
        ref_signal_items = self.lstSelectedInputSignals.findItems(
            self.cmbRefSignal.currentText(), Qt.MatchFlag.MatchExactly)
        if len(ref_signal_items) > 0:
            row = self.lstSelectedInputSignals.row(ref_signal_items[0])
            self.lstSelectedInputSignals.takeItem(row)

        # ref選完之後把剩下的選項加入輸入訊號
        current_ref = self.cmbRefSignal.currentText()
        self.cmbInputSignal.addItems(
            [ch for ch in self.get_all_input() if (ch != current_ref) and (ch != 'Internal')])

    def remove_item_double_click(self, item):
        # 獲取被雙擊項目的索引
        row = self.lstSelectedInputSignals.row(item)
        # 使用 takeItem() 移除該索引的項目
        self.lstSelectedInputSignals.takeItem(row)
