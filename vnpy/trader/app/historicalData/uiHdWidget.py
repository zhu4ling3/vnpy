# encoding: UTF-8

'''
行情记录模块相关的GUI控制组件
'''

from vnpy.event import Event
from vnpy.trader.uiQt import QtWidgets, QtCore
from .language import text
from vnpy.trader.gateway import ibGateway
from vnpy.trader.vtEvent import EVENT_LOG


########################################################################
class TableCell(QtWidgets.QTableWidgetItem):
    """居中的单元格"""

    # ----------------------------------------------------------------------
    def __init__(self, text=None, mainEngine=None):
        """Constructor"""
        super(TableCell, self).__init__()
        self.data = None
        self.setTextAlignment(QtCore.Qt.AlignCenter)
        if text:
            self.setContent(text)

    # ----------------------------------------------------------------------
    def setContent(self, text):
        """设置内容"""
        if text == '0' or text == '0.0':
            self.setText('')
        else:
            self.setText(text)


########################################################################
class HdEngineManager(QtWidgets.QWidget):
    """行情数据记录引擎管理组件"""
    signal = QtCore.Signal(type(Event()))

    # ----------------------------------------------------------------------
    def __init__(self, hdEngine, eventEngine, parent=None):
        """Constructor"""
        super(HdEngineManager, self).__init__(parent)

        self.hdEngine = hdEngine
        self.eventEngine = eventEngine

        self.__tickBtn = None
        self.__barBtn = None

        self.initUi()
        self.updateSetting()
        self.registerEvent()

    # ----------------------------------------------------------------------
    def initUi(self):
        """初始化界面"""
        self.setWindowTitle(text.DATA_RECORDER)

        # 记录合约配置监控
        tickLabel = QtWidgets.QLabel(text.TICK_RECORD)
        tickBtn = QtWidgets.QCheckBox(text.TICK_SWITCH)
        self.tickTable = QtWidgets.QTableWidget()
        self.tickTable.setColumnCount(4)
        self.tickTable.verticalHeader().setVisible(False)
        self.tickTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.tickTable.setAlternatingRowColors(True)
        self.tickTable.setHorizontalHeaderLabels([text.CONTRACT_SYMBOL, text.GATEWAY, text.START, text.END])

        barLabel = QtWidgets.QLabel(text.BAR_RECORD)
        barBtn = QtWidgets.QCheckBox(text.BAR_SWITCH)
        self.barTable = QtWidgets.QTableWidget()
        self.barTable.setColumnCount(5)
        self.barTable.verticalHeader().setVisible(False)
        self.barTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        self.barTable.setAlternatingRowColors(True)
        self.barTable.setHorizontalHeaderLabels([text.CONTRACT_SYMBOL, text.GATEWAY, text.START, text.END, text.SIZE])

        # activeLabel = QtWidgets.QLabel(text.DOMINANT_CONTRACT)
        # self.activeTable = QtWidgets.QTableWidget()
        # self.activeTable.setColumnCount(2)
        # self.activeTable.verticalHeader().setVisible(False)
        # self.activeTable.setEditTriggers(QtWidgets.QTableWidget.NoEditTriggers)
        # self.activeTable.setAlternatingRowColors(True)
        # self.activeTable.setHorizontalHeaderLabels([text.DOMINANT_SYMBOL, text.CONTRACT_SYMBOL])

        # 日志监控
        self.logMonitor = QtWidgets.QTextEdit()
        self.logMonitor.setReadOnly(True)
        self.logMonitor.setMinimumHeight(600)

        # 设置布局
        g1 = QtWidgets.QGridLayout()
        g1.addWidget(tickLabel, 0, 0)
        g1.addWidget(tickBtn, 0, 1)

        g2 = QtWidgets.QGridLayout()
        g2.addWidget(barLabel, 0, 0)
        g2.addWidget(barBtn, 0, 1)

        grid = QtWidgets.QGridLayout()
        grid.addLayout(g1, 0, 0)
        grid.addLayout(g2, 0, 1)

        # grid.addWidget(activeLabel, 0, 2)
        grid.addWidget(self.tickTable, 1, 0)
        grid.addWidget(self.barTable, 1, 1)
        # grid.addWidget(self.activeTable, 1, 2)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(grid)
        vbox.addWidget(self.logMonitor)
        self.setLayout(vbox)

        tickBtn.setCheckState(
            QtCore.Qt.Checked if self.hdEngine.mainEngine.getGateway(
                ibGateway.gatewayName).historicalTicksReq.getRunning() else QtCore.Qt.Unchecked
        )
        barBtn.setCheckState(
            QtCore.Qt.Checked if self.hdEngine.mainEngine.getGateway(
                ibGateway.gatewayName).historicalBarReq.getRunning() else QtCore.Qt.Unchecked
        )

        tickBtn.stateChanged.connect(self.tickBtn_onStateChanged)
        barBtn.stateChanged.connect(self.barBtn_onStateChanged)

    # ----------------------------------------------------------------------
    def updateLog(self, event):
        """更新日志"""
        log = event.dict_['data']
        # content = '\t'.join([log.logTime, log.logContent])
        content = '\t'.join([str(k)+'='+str(v) for k,v in log.items()])
        self.logMonitor.append(content)

    # ----------------------------------------------------------------------
    def registerEvent(self):
        """注册事件监听"""
        self.signal.connect(self.updateLog)
        self.eventEngine.register(EVENT_LOG+'.histLog', self.signal.emit)

    # ----------------------------------------------------------------------
    def updateSetting(self):
        """显示引擎行情记录配置"""
        setting, activeSetting = self.hdEngine.getSetting()

        for d in setting.values():
            if 'tick' in d and d['tick']:
                self.tickTable.insertRow(0)
                self.tickTable.setItem(0, 0, TableCell(d['symbol']))
                self.tickTable.setItem(0, 1, TableCell(d['gateway']))
                self.tickTable.setItem(0, 2, TableCell(d['start']))
                self.tickTable.setItem(0, 3, TableCell(d['end']))

            if 'bar' in d and d['bar']:
                self.barTable.insertRow(0)
                self.barTable.setItem(0, 0, TableCell(d['symbol']))
                self.barTable.setItem(0, 1, TableCell(d['gateway']))
                self.barTable.setItem(0, 2, TableCell(d['start']))
                self.barTable.setItem(0, 3, TableCell(d['end']))
                self.barTable.setItem(0, 4, TableCell(d['size']))

        for vtSymbol, activeSymbol in activeSetting.items():
            self.activeTable.insertRow(0)
            self.activeTable.setItem(0, 0, TableCell(activeSymbol))
            self.activeTable.setItem(0, 1, TableCell(vtSymbol))

        self.tickTable.resizeColumnsToContents()
        self.barTable.resizeColumnsToContents()
        # self.activeTable.resizeColumnsToContents()

    # ------------------------------------------------------------------------
    def tickBtn_onStateChanged(self, state):
        if state == QtCore.Qt.Unchecked:
            self.hdEngine.mainEngine.getGateway(ibGateway.gatewayName).historicalTicksReq.setRunning(False)
        else:
            self.hdEngine.mainEngine.getGateway(ibGateway.gatewayName).historicalTicksReq.setRunning(True)

    # ------------------------------------------------------------------------
    def barBtn_onStateChanged(self, state):
        if state == QtCore.Qt.Unchecked:
            self.hdEngine.mainEngine.getGateway(ibGateway.gatewayName).historicalBarReq.setRunning(False)
        else:
            self.hdEngine.mainEngine.getGateway(ibGateway.gatewayName).historicalBarReq.setRunning(True)
