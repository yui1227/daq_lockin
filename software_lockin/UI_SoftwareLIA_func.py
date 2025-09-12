from UI_SoftwareLIA_ui import Ui_SoftwareLIA
from PySide6.QtWidgets import QMainWindow
import nidaqmx
import nidaqmx.system

class Ui_SoftwareLIA_func(QMainWindow, Ui_SoftwareLIA):
    def __init__(self, parent=None):
        super(Ui_SoftwareLIA_func, self).__init__(parent)
        self.setupUi(self)
        for dev in nidaqmx.system.System.local().devices:
            self.cmbDAQ.addItems(dev.name)