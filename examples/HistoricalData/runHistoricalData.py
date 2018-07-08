# encoding: UTF-8

from __future__ import print_function

import multiprocessing
from time import sleep
from datetime import datetime, time

from pytz import timezone

from vnpy.event import EventEngine2
from vnpy.trader.vtEvent import EVENT_LOG, EVENT_ERROR, EVENT_TIMER
from vnpy.trader.vtEngine import MainEngine, LogEngine
from vnpy.trader.gateway import ibGateway
from vnpy.trader.app import historicalData
from vnpy import settings

#----------------------------------------------------------------------
def processErrorEvent(event):
    """
    处理错误事件
    错误信息在每次登陆后，会将当日所有已产生的均推送一遍，所以不适合写入日志
    """
    error = event.dict_['data']
    print(u'错误代码：%s，错误信息：%s' %(error.errorID, error.errorMsg))

#----------------------------------------------------------------------
def runChildProcess():
    """子进程运行函数"""
    print('-'*20)

    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    le.info(u'启动行情记录运行子进程')

    ee = EventEngine2()
    le.info(u'事件引擎创建成功')

    me = MainEngine(ee)
    me.addGateway(ibGateway)
    me.addApp(historicalData)
    le.info(u'主引擎创建成功')

    ee.register(EVENT_LOG, le.processLogEvent)
    ee.register(EVENT_ERROR, processErrorEvent)
    le.info(u'注册日志事件监听')

    me.connect('IB')
    le.info(u'连接IB接口')

    # 建立连接后，启动收取队列数据的主循环过程。这个过程是在独立的子进程里面执行的。
    me.getGateway(ibGateway.gatewayName).start()

    # while True:
    #     sleep(1)

#----------------------------------------------------------------------
def runParentProcess():
    """父进程运行函数"""
    # 创建日志引擎
    le = LogEngine()
    le.setLogLevel(le.LEVEL_INFO)
    le.addConsoleHandler()
    le.info(u'启动行情记录守护父进程')
    
    tz = timezone(settings.HISTORICAL_DATA['TIME_ZONE'])
    DAY_START = time(8, 42, tzinfo=tz)         # 日盘启动和停止时间
    DAY_END = time(15, 18, tzinfo=tz)
    NIGHT_START = time(20, 57, tzinfo=tz)      # 夜盘启动和停止时间
    NIGHT_END = time(2, 33, tzinfo=tz)

    
    p = None        # 子进程句柄

    while True:
        currentTime = datetime.now(tz).time()
        recording = False

        # 判断当前处于的时间段
        if ((currentTime >= DAY_START and currentTime <= DAY_END) or
            (currentTime >= NIGHT_START) or
            (currentTime <= NIGHT_END)):
            recording = True
            
        # 过滤周末时间段：周六全天，周五夜盘，周日日盘
        if ((datetime.today().weekday() == 6) or 
            (datetime.today().weekday() == 5 and currentTime > NIGHT_END) or 
            (datetime.today().weekday() == 0 and currentTime < DAY_START)):
            recording = False

        # TODO: 调试完毕后移除 recording = True
        recording = True

        # 记录时间则需要启动子进程
        if recording and p is None:
            le.info(u'启动子进程')
            p = multiprocessing.Process(target=runChildProcess)
            p.start()
            le.info(u'子进程启动成功')

        # 非记录时间则退出子进程
        if not recording and p is not None:
            le.info(u'关闭子进程')
            p.terminate()
            p.join()
            p = None
            le.info(u'子进程关闭成功')

        sleep(5)


if __name__ == '__main__':
    #runChildProcess()
    runParentProcess()
