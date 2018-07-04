# encoding: UTF-8

'''
本文件中实现了行情数据记录引擎，用于汇总TICK数据，并生成K线插入数据库。

使用DR_setting.json来配置需要收集的合约，以及主力合约代码。
'''

import json
import csv
import os
import copy
import traceback
from collections import OrderedDict
from datetime import datetime, timedelta
from queue import Queue, Empty
from threading import Thread
from pymongo.errors import DuplicateKeyError

from vnpy.event import Event
from vnpy.trader.vtEvent import *
from vnpy.trader.vtFunction import todayDate, getJsonPath
from vnpy.trader.vtObject import VtHistoricalTickReq, VtHistoricalBarReq, VtLogData, VtBarData, VtTickData
from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator

from .hdBase import *
from .language import text

from vnpy import settings

########################################################################
class HdEngine(object):
    """历史数据记录引擎"""

    # settingFileName = 'HD_setting.json'
    # settingFilePath = getJsonPath(settingFileName, __file__)

    # ----------------------------------------------------------------------
    def __init__(self, mainEngine, eventEngine):
        """Constructor"""
        self.mainEngine = mainEngine
        self.eventEngine = eventEngine

        # 当前日期
        self.today = todayDate()

        # 主力合约代码映射字典，key为具体的合约代码（如IF1604），value为主力合约代码（如IF0000）
        self.activeSymbolDict = {}

        # Tick对象字典
        self.tickSymbolSet = set()

        # K线合成器字典
        self.bgDict = {}

        # 配置字典
        self.settingDict = OrderedDict()

        # 负责执行数据库插入的单独线程相关
        self.active = False  # 工作状态
        self.queue = Queue()  # 队列
        self.thread = Thread(target=self.run)  # 线程

        self.tickReqList = []

        # 载入设置，订阅行情
        self.loadSetting()

        # 启动数据插入线程
        self.start()

        # 注册事件监听
        self.registerEvent()


        self.span = None

        # ----------------------------------------------------------------------

    def loadSetting(self):
        """加载配置"""


        drSetting = settings.HISTORICAL_DATA['REQUESTS']

        # 如果working设为False则不启动行情记录功能
        working = drSetting['working']
        if not working:
            return


        for setting in drSetting['list']:
            if 'workflag' in setting and not setting['workflag']:
                continue

            symbol = setting['symbol']
            gateway = setting['gateway']
            vtSymbol = symbol

            req = VtHistoricalTickReq()
            req.symbol = symbol
            req.gateway = gateway

            # 针对LTS和IB接口，订阅行情需要交易所代码
            if 'exchange' in setting:
                req.exchange = setting['exchange']
                vtSymbol = '.'.join([symbol, req.exchange])

            if 'currency' in setting:
                req.currency = setting['currency']
                req.productClass = setting['sectype']
                req.start = setting['start']
                req.end = setting['end']

            for o in setting['objects']:

                if 'type' not in o:
                    raise Exception('需要指明type')

                if o['type'] == 'tick':
                    self.mainEngine.subscribe(req, gateway)

                    # tick = VtTickData()           # 该tick实例可以用于缓存部分数据（目前未使用）
                    # self.tickDict[vtSymbol] = tick
                    self.tickSymbolSet.add(vtSymbol)

                    # 保存到配置字典中
                    if vtSymbol not in self.settingDict:
                        d = {
                            'symbol': symbol,
                            'gateway': gateway,
                            'tick': True,
                        }
                        self.settingDict[vtSymbol] = d
                    else:
                        d = self.settingDict[vtSymbol]
                        d['tick'] = True

                    if 'gen' in o:
                        # 保存到配置字典中
                        if vtSymbol not in self.settingDict:
                            d = {
                                'symbol': symbol,
                                'gateway': gateway,
                                'bar': True
                            }
                            self.settingDict[vtSymbol] = d
                        else:
                            d = self.settingDict[vtSymbol]
                            d['bar'] = True

                            # 创建BarManager对象
                        self.bgDict[vtSymbol] = BarGenerator(self.onBar)



    # ----------------------------------------------------------------------
    def getSetting(self):
        """获取配置"""
        return self.settingDict, self.activeSymbolDict



    # ----------------------------------------------------------------------
    def procecssTickEvent(self, event):
        """处理行情事件"""
        tick = event.dict_['data']
        vtSymbol = tick.vtSymbol

        # 生成datetime对象
        if not tick.datetime:
            tick.datetime = datetime.strptime(' '.join([tick.date, tick.time]), '%Y%m%d %H:%M:%S.%f')

        # IB的历史数据中的原始tick数据只有当前成交量而没有当日总成交量，故需要计算得到。
        if not 'currentDate' in self.settingDict[vtSymbol]:
            self.settingDict[vtSymbol]['currentDate'] = tick.datetime.strftime('%Y%m%d')

        if self.settingDict[vtSymbol]['currentDate'] == tick.datetime.strftime('%Y%m%d'):
            tick.volume += tick.lastVolume
        else:
            tick.volume = tick.lastVolume
            self.settingDict[vtSymbol]['currentDate'] = tick.datetime.strftime('%Y%m%d')

        self.onTick(tick)

        bm = self.bgDict.get(vtSymbol, None)
        if bm:
            bm.updateTick(tick)

    # ----------------------------------------------------------------------
    def onTick(self, tick):
        """Tick更新"""
        vtSymbol = tick.vtSymbol

        if vtSymbol in self.tickSymbolSet:
            self.insertData(TICK_DB_NAME, vtSymbol, tick)

            if vtSymbol in self.activeSymbolDict:
                activeSymbol = self.activeSymbolDict[vtSymbol]
                self.insertData(TICK_DB_NAME, activeSymbol, tick)

            self.writeDrLog(text.TICK_LOGGING_MESSAGE.format(symbol=tick.vtSymbol,
                                                             time=tick.time,
                                                             last=tick.lastPrice,
                                                             bid=tick.bidPrice1,
                                                             ask=tick.askPrice1))

    # ----------------------------------------------------------------------
    def onBar(self, bar):
        """分钟线更新"""
        vtSymbol = bar.vtSymbol

        self.insertData(MINUTE_DB_NAME, vtSymbol, bar)

        if vtSymbol in self.activeSymbolDict:
            activeSymbol = self.activeSymbolDict[vtSymbol]
            self.insertData(MINUTE_DB_NAME, activeSymbol, bar)

        self.writeDrLog(text.BAR_LOGGING_MESSAGE.format(symbol=bar.vtSymbol,
                                                        time=bar.time,
                                                        open=bar.open,
                                                        high=bar.high,
                                                        low=bar.low,
                                                        close=bar.close))

        # ----------------------------------------------------------------------

    def registerEvent(self):
        """注册事件监听"""
        self.eventEngine.register(EVENT_TICK, self.procecssTickEvent)

    # ----------------------------------------------------------------------
    def insertData(self, dbName, collectionName, data):
        """插入数据到数据库（这里的data可以是VtTickData或者VtBarData）"""
        self.queue.put((dbName, collectionName, data.__dict__))

    # ----------------------------------------------------------------------
    def run(self):
        """运行插入线程"""
        while self.active:
            try:
                dbName, collectionName, d = self.queue.get(block=True, timeout=1)

                # 这里采用MongoDB的update模式更新数据，在记录tick数据时会由于查询
                # 过于频繁，导致CPU占用和硬盘读写过高后系统卡死，因此不建议使用
                # flt = {'datetime': d['datetime']}
                # self.mainEngine.dbUpdate(dbName, collectionName, d, flt, True)

                # 使用insert模式更新数据，可能存在时间戳重复的情况，需要用户自行清洗
                try:
                    self.mainEngine.dbInsert(dbName, collectionName, d)
                except DuplicateKeyError:
                    self.writeDrLog(u'键值重复插入失败，报错信息：%s' % traceback.format_exc())
            except Empty:
                pass

    # ----------------------------------------------------------------------
    def start(self):
        """启动"""
        self.active = True
        self.thread.start()

    # ----------------------------------------------------------------------
    def stop(self):
        """退出"""
        if self.active:
            self.active = False
            self.thread.join()

    # ----------------------------------------------------------------------
    def writeDrLog(self, content):
        """快速发出日志事件"""
        log = VtLogData()
        log.logContent = content
        event = Event(type_=EVENT_HISTORICALDATA_LOG)
        event.dict_['data'] = log
        self.eventEngine.put(event)
