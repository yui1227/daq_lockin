from PySide6.QtWidgets import QApplication
from UI_SoftwareLIA_func import Ui_SoftwareLIA_func
import sys


def main():
    app = QApplication(sys.argv)
    ui = Ui_SoftwareLIA_func()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
