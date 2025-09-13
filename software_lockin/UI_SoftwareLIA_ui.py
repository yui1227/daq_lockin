# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'UI_SoftwareLIA.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QPushButton, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_SoftwareLIA(object):
    def setupUi(self, SoftwareLIA):
        if not SoftwareLIA.objectName():
            SoftwareLIA.setObjectName(u"SoftwareLIA")
        SoftwareLIA.resize(1070, 819)
        self.centralwidget = QWidget(SoftwareLIA)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_3 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout = QVBoxLayout(self.groupBox)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.cmbDAQ = QComboBox(self.groupBox)
        self.cmbDAQ.setObjectName(u"cmbDAQ")

        self.verticalLayout.addWidget(self.cmbDAQ)


        self.verticalLayout_5.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_4.addWidget(self.label_2)

        self.dsbSamplingRate = QDoubleSpinBox(self.groupBox_2)
        self.dsbSamplingRate.setObjectName(u"dsbSamplingRate")

        self.verticalLayout_4.addWidget(self.dsbSamplingRate)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_4.addWidget(self.label_3)

        self.dsbTimeConstant = QDoubleSpinBox(self.groupBox_2)
        self.dsbTimeConstant.setObjectName(u"dsbTimeConstant")

        self.verticalLayout_4.addWidget(self.dsbTimeConstant)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_4.addWidget(self.label_4)

        self.sbFilterOrder = QSpinBox(self.groupBox_2)
        self.sbFilterOrder.setObjectName(u"sbFilterOrder")

        self.verticalLayout_4.addWidget(self.sbFilterOrder)

        self.groupBox_5 = QGroupBox(self.groupBox_2)
        self.groupBox_5.setObjectName(u"groupBox_5")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_5)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_7 = QLabel(self.groupBox_5)
        self.label_7.setObjectName(u"label_7")

        self.verticalLayout_2.addWidget(self.label_7)

        self.dsbRefFreq = QDoubleSpinBox(self.groupBox_5)
        self.dsbRefFreq.setObjectName(u"dsbRefFreq")
        self.dsbRefFreq.setMaximum(1000000000.000000000000000)

        self.verticalLayout_2.addWidget(self.dsbRefFreq)

        self.label_8 = QLabel(self.groupBox_5)
        self.label_8.setObjectName(u"label_8")

        self.verticalLayout_2.addWidget(self.label_8)

        self.dsbRefInitPhase = QDoubleSpinBox(self.groupBox_5)
        self.dsbRefInitPhase.setObjectName(u"dsbRefInitPhase")
        self.dsbRefInitPhase.setDecimals(6)
        self.dsbRefInitPhase.setMaximum(6.283185000000000)
        self.dsbRefInitPhase.setSingleStep(0.100000000000000)

        self.verticalLayout_2.addWidget(self.dsbRefInitPhase)


        self.verticalLayout_4.addWidget(self.groupBox_5)


        self.verticalLayout_5.addWidget(self.groupBox_2)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_5 = QLabel(self.groupBox_3)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout_3.addWidget(self.label_5)

        self.cmbRefSignal = QComboBox(self.groupBox_3)
        self.cmbRefSignal.setObjectName(u"cmbRefSignal")

        self.verticalLayout_3.addWidget(self.cmbRefSignal)

        self.label_6 = QLabel(self.groupBox_3)
        self.label_6.setObjectName(u"label_6")

        self.verticalLayout_3.addWidget(self.label_6)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.cmbInputSignal = QComboBox(self.groupBox_3)
        self.cmbInputSignal.setObjectName(u"cmbInputSignal")

        self.horizontalLayout.addWidget(self.cmbInputSignal)

        self.btnAddInputSignal = QPushButton(self.groupBox_3)
        self.btnAddInputSignal.setObjectName(u"btnAddInputSignal")
        self.btnAddInputSignal.setMaximumSize(QSize(40, 16777215))

        self.horizontalLayout.addWidget(self.btnAddInputSignal)


        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.lstSelectedInputSignals = QListWidget(self.groupBox_3)
        self.lstSelectedInputSignals.setObjectName(u"lstSelectedInputSignals")

        self.verticalLayout_3.addWidget(self.lstSelectedInputSignals)


        self.verticalLayout_5.addWidget(self.groupBox_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.btnStartRealtime = QPushButton(self.centralwidget)
        self.btnStartRealtime.setObjectName(u"btnStartRealtime")

        self.horizontalLayout_2.addWidget(self.btnStartRealtime)

        self.btnStartRecordSave = QPushButton(self.centralwidget)
        self.btnStartRecordSave.setObjectName(u"btnStartRecordSave")

        self.horizontalLayout_2.addWidget(self.btnStartRecordSave)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)


        self.horizontalLayout_3.addLayout(self.verticalLayout_5)

        self.groupBox_4 = QGroupBox(self.centralwidget)
        self.groupBox_4.setObjectName(u"groupBox_4")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_4.sizePolicy().hasHeightForWidth())
        self.groupBox_4.setSizePolicy(sizePolicy)
        self.groupBox_4.setMinimumSize(QSize(800, 800))
        self.horizontalLayout_4 = QHBoxLayout(self.groupBox_4)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.graphicsView = PlotWidget(self.groupBox_4)
        self.graphicsView.setObjectName(u"graphicsView")

        self.horizontalLayout_4.addWidget(self.graphicsView)


        self.horizontalLayout_3.addWidget(self.groupBox_4)

        SoftwareLIA.setCentralWidget(self.centralwidget)

        self.retranslateUi(SoftwareLIA)

        QMetaObject.connectSlotsByName(SoftwareLIA)
    # setupUi

    def retranslateUi(self, SoftwareLIA):
        SoftwareLIA.setWindowTitle(QCoreApplication.translate("SoftwareLIA", u"SoftwareLIA", None))
        self.groupBox.setTitle(QCoreApplication.translate("SoftwareLIA", u"DAQ\u9078\u9805", None))
        self.label.setText(QCoreApplication.translate("SoftwareLIA", u"\u8acb\u9078\u64c7DAQ\uff1a", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("SoftwareLIA", u"\u9396\u76f8\u653e\u5927\u5668\u8a2d\u5b9a", None))
        self.label_2.setText(QCoreApplication.translate("SoftwareLIA", u"\u53d6\u6a23\u983b\u7387(Hz)\uff1a", None))
        self.label_3.setText(QCoreApplication.translate("SoftwareLIA", u"\u6642\u9593\u5e38\u6578(s)\uff1a", None))
        self.label_4.setText(QCoreApplication.translate("SoftwareLIA", u"\u6ffe\u6ce2\u5668\u968e\u6578", None))
        self.groupBox_5.setTitle(QCoreApplication.translate("SoftwareLIA", u"\u53c3\u8003\u8a0a\u865f\u8a2d\u5b9a(\u53ea\u5728\u9078\u64c7Internal\u6709\u6548)", None))
        self.label_7.setText(QCoreApplication.translate("SoftwareLIA", u"\u5167\u90e8\u53c3\u8003\u8a0a\u865f\u983b\u7387(Hz)\uff1a", None))
        self.label_8.setText(QCoreApplication.translate("SoftwareLIA", u"\u5167\u90e8\u53c3\u8003\u8a0a\u865f\u521d\u59cb\u76f8\u4f4d(rad)\uff1a", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("SoftwareLIA", u"\u8a0a\u865f\u8a2d\u5b9a", None))
        self.label_5.setText(QCoreApplication.translate("SoftwareLIA", u"\u53c3\u8003\u8a0a\u865f\uff1a", None))
        self.label_6.setText(QCoreApplication.translate("SoftwareLIA", u"\u8f38\u5165\u8a0a\u865f\uff1a", None))
        self.btnAddInputSignal.setText(QCoreApplication.translate("SoftwareLIA", u"+", None))
        self.btnStartRealtime.setText(QCoreApplication.translate("SoftwareLIA", u"\u5373\u6642\u91cf\u6e2c", None))
        self.btnStartRecordSave.setText(QCoreApplication.translate("SoftwareLIA", u"\u8a18\u9304\u4e26\u5b58\u6a94", None))
        self.groupBox_4.setTitle(QCoreApplication.translate("SoftwareLIA", u"\u5373\u6642\u7e6a\u5716", None))
    # retranslateUi

