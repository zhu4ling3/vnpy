# encoding: UTF-8

'''
本文件中包含的数据格式和CTA模块通用，用户有必要可以自行添加格式。
'''


# 数据库名称
SETTING_DB_NAME = 'VnTrader_Setting_Db'
TICK_DB_NAME = 'VnTrader_Tick_Db'
DAILY_DB_NAME = 'VnTrader_Daily_Db'
MINUTE_DB_NAME = 'VnTrader_1Min_Db'
BAR_DB_NAME = {
    '1 sec': 'VnTrader_1Sec_Db',
    '5 secs': 'VnTrader_5Secs_Db',
    '10 secs': 'VnTrader_10Secs_Db',
    '30 secs': 'VnTrader_30ecs_Db',
    '1 min': 'VnTrader_1Min_Db',
    '10 mins': 'VnTrader_10Mins_Db',
    '1 hour': 'VnTrader_1Hour_Db',
    '4 hours': 'VnTrader_4Hours_Db',
    '1 day': 'VnTrader_1Day_Db',
    '1 week': 'VnTrader_1Week_Db',
    '1 month': 'VnTrader_1Month_Db',
}

# 行情记录模块事件
EVENT_HISTORICALDATA_LOG = 'HistoricalDataLog'     # 行情记录日志更新事件

# CTA引擎中涉及的数据类定义
from vnpy.trader.vtConstant import EMPTY_UNICODE, EMPTY_STRING, EMPTY_FLOAT, EMPTY_INT
