"""

"""

import logging
from datetime import timedelta, datetime
import pytz
from copy import copy

from .decorator import logging_level
from vnpy.trader.vtEvent import EVENT_TIMER
from vnpy.trader.vtObject import VtHistoricalTickReq, VtHistoricalBarReq, VtTickData, VtBarData
from vnpy.api.ibpy.ibapi.contract import Contract
from .ibGateway2 import exchangeMap, productClassMap, currencyMap, optionTypeMap
from vnpy import settings

# 发出历史数据请求时，根据产品的资产类型决定请求的数据类型
REQ_DATA_TYPE_MAP = {
    'CMDTY': 'MIDPOINT',
    'CASH': 'MIDPOINT',
    'STK': 'TRADES',
}

# 发出历史数据请求时，根据数据粒度的大小，决定一次请求的期间长短
REQ_STEP_SIZE_MAP = {
    '1 sec': {'durationString': '1800 S', 'barSizeSetting': '1 sec', },
    '5 secs': {'durationString': '3600 S', 'barSizeSetting': '5 secs', },
    '10 secs': {'durationString': '14400 S', 'barSizeSetting': '10 secs', },
    '30 secs': {'durationString': '28800 S', 'barSizeSetting': '30 secs', },
#    '1 min': {'durationString': '1 D', 'barSizeSetting': '1 min', },
    '1 min': {'durationString': '28800 S', 'barSizeSetting': '1 min', },
    '10 mins': {'durationString': '1 W', 'barSizeSetting': '10 mins', },
    '1 hour': {'durationString': '1 M', 'barSizeSetting': '1 hour', },
    '4 hours': {'durationString': '1 M', 'barSizeSetting': '4 hours', },
    '1 day': {'durationString': '1 Y', 'barSizeSetting': '1 day', },
    '1 week': {'durationString': '1 Y', 'barSizeSetting': '1 week', },
    '1 month': {'durationString': '1 Y', 'barSizeSetting': '1 month', },
}


@logging_level(level=logging.INFO)
class HistoricalTicksRequest(object):
    def __init__(self, ibgw):
        super().__init__()

        self.__internal_counter = -1
        self.histTickDataList = []
        self.histTickReqDict = {}

        self.gateway = ibgw
        self.isRunning = False

    # ------------------------------------------------------------------------------
    def subscribe(self, req: VtHistoricalTickReq):
        # 将向IB请求历史数据所需的固定参数保存到列表，同时将onTick时需要的固定参数也保存到列表，供后续处理时使用。
        contract = Contract()
        contract.localSymbol = str(req.symbol)
        contract.exchange = exchangeMap.get(req.exchange, '')
        contract.secType = productClassMap.get(req.productClass, '')
        contract.currency = currencyMap.get(req.currency, '')
        contract.expiry = req.expiry
        contract.strike = req.strikePrice
        contract.right = optionTypeMap.get(req.optionType, '')

        st = datetime.strptime(req.start, '%Y%m%d %H:%M:%S').replace(
            tzinfo=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))
        et = datetime.strptime(req.end, '%Y%m%d %H:%M:%S').replace(
            tzinfo=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))

        # # 创建Tick对象并保存到字典中
        tick = VtTickData()
        tick.symbol = req.symbol
        tick.exchange = req.exchange
        tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
        tick.gatewayName = self.gateway.gatewayName
        dic = {
            'contractInfo': contract,
            'startDateTime': st,
            'endDateTime': et,
            'tickInfo': tick,
        }

        self.histTickDataList.append(
            dic,
        )

        self.gateway.eventEngine.register(EVENT_TIMER, self.__processTimerEvent)
        logging.info(dic)

    # ------------------------------------------------------------------------------
    def __processTimerEvent(self, event):
        """
        根据缓存的请求，向IB发起历史tick数据的请求

        :return:
        """

        if not self.isRunning:
            return

        # Timer事件是1秒一次，在本方法中可以控制向IB请求历史数据的频率为ONE_CALL_INTERNAL秒一次。
        ONE_CALL_INTERNAL = 1
        RETRY_COUNT = 180 // ONE_CALL_INTERNAL

        if self.__internal_counter == -1:
            self.__internal_counter = 0
        elif self.__internal_counter < ONE_CALL_INTERNAL:
            self.__internal_counter += 1
            return
        else:
            self.__internal_counter = 0

        # 遍历请求列表
        want_del = []
        for o in self.histTickDataList:
            contract = o['contractInfo']
            st = o['startDateTime']
            et = o['endDateTime']

            # 为第一次请求设置一些属性
            if not 'lastTime' in o:
                o['lastTime'] = et + timedelta(seconds=-1)
                o['totalTicks'] = 0
                o['retry_count'] = 0
                o['reqId'] = None

            lt = o['lastTime']

            # 所有历史数据已经获取完毕，可以删除其请求对象；
            if st > et:
                want_del.append(o)
                logging.info('-------------数据获取完毕。%s' % o)
                continue

            # 另外，有时IB对于请求会延迟响应，此时下一个定时器事件会到来。为了避免重复请求，将上一次请求的时间记录下来，
            # 然后本次请求和st和at比较，如果st<=at，则表示已经请求过了。
            if et == lt:
                o['retry_count'] += 1
                # 如果重试大于n次，则先取消这笔请求，然后再重新请求
                if o['retry_count'] <= RETRY_COUNT:
                    continue

                # TODO: 取消这笔请求
                self.gateway.api.cancelHistoricalData(o['reqId'])
                self.histTickReqDict.pop(o['reqId'])

            self.gateway.tickerId += 1

            # TODO: 测试通过后在加入去
            # 创建Tick对象并保存到字典中
            # tick = VtTickData()
            # tick.symbol = subscribeReq.symbol
            # tick.exchange = subscribeReq.exchange
            # tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            # tick.gatewayName = self.gatewayName
            # self.tickDict[self.tickerId] = tick
            # self.tickProductDict[self.tickerId] = subscribeReq.productClass

            self.histTickReqDict[self.gateway.tickerId] = o

            NUM_OF_TICKS = 1000
            self.gateway.api.reqHistoricalTicks(self.gateway.tickerId,
                                                contract,
                                                startDateTime='',
                                                endDateTime=et.astimezone(
                                                    tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE'])).strftime(
                                                    '%Y%m%d %H:%M:%S'),
                                                numberOfTicks=NUM_OF_TICKS,
                                                whatToShow=REQ_DATA_TYPE_MAP[contract.secType],
                                                useRth=0,
                                                ignoreSize=False, miscOptions=[])
            o['lastTime'] = et
            o['reqId'] = self.gateway.tickerId
            o['retry_count'] = 0
            logging.info('-----------reqId=%d %s %s' %
                         (o['reqId'], contract.localSymbol, et.strftime('%Y%m%d %H:%M:%S')))

        # 删除已经接收完毕的请求数据
        for o in want_del:
            self.histTickDataList.remove(o)

    # --------------------------------------------------------------------
    def historicalTicks(self, reqId, ticks, done):
        """
        :param reqId:
        :param ticks:
        :param done:
        :return:
        """

        val = self.histTickReqDict.pop(reqId) if done else self.histTickReqDict[reqId]  # 如果reqId对应的数据传输完毕，则清除字典中存储的对象。
        st = val['startDateTime']
        et = val['endDateTime']
        tick = val['tickInfo']

        t = None
        t1 = None  # 记录第一个有效数据的时间
        num = 0
        total = 0
        for o in ticks:
            # IB返回来的数据的时区和登录TWS/IB Gateway时选择的时区一致。此时区必须配置在settings中。
            dt = datetime.fromtimestamp(o.time, tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))

            # 清洗数据，仅当st<=数据日期<et数据才有效。回调函数传入的ticks是按照时间升序排列的
            if dt < st:
                continue
            if dt > et:
                break

            if t1 == None:
                t1 = dt

            if t != dt:

                if t:
                    total += num
                    logging.debug('-----------%s %s num=%d' % (tick.symbol, t.strftime('%Y%m%d %H:%M:%S'), num))
                t = dt
                num = 0

            num += 1

            # 在mongodb内部，时间戳以UTC时区保存
            tick.datetime = dt.astimezone(pytz.timezone('UTC'))
            tick.time = dt.strftime('%H:%M:%S.%f')
            tick.date = dt.strftime('%Y%m%d')
            tick.lastPrice = o.price
            tick.lastVolume = o.size
            newtick = copy(tick)
            self.gateway.onTick(newtick)

        if t:
            t0 = datetime.fromtimestamp(ticks[0].time, tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))
            val['endDateTime'] = t0 + timedelta(seconds=-1)

            total += num
            val['totalTicks'] += total
            logging.info('-----------reqId=%d %s %s %d total=%d' %
                         (reqId, tick.symbol, t.strftime('%Y%m%d %H:%M:%S'), num, val['totalTicks']))

            info = {}
            info['vtSymbol'] = tick.vtSymbol
            info['type'] = 'tick'
            info['size'] = 'n/a'
            info['stime'] = t1.strftime('%Y%m%d %H:%M:%S')
            info['etime'] = t.strftime('%Y%m%d %H:%M:%S')
            info['total'] = val['totalTicks']
            self.gateway.onProgress(info)

        # 如果endDateTime等于lastTime，就表示本次请求的响应数据里面没有包含有效数据。（可能包含了startDateTime～endDateTime之外的数据）
        # 如果done又同时为真，那么就可以推论出所有数据都已经获得。
        if val['endDateTime'] == val['lastTime'] and done:
            val['endDateTime'] = val['startDateTime'] + timedelta(seconds=-1)

    #--------------------------------------------------------------
    def setRunning(self, flag):
        self.isRunning = flag

    #--------------------------------------------------------------
    def getRunning(self):
        return self.isRunning



@logging_level(level=logging.INFO)
class HistoricalBarRequest(object):


    def __init__(self, ibgw):
        super().__init__()

        self.__internal_counter = -1
        self.histBarDataList = []
        self.histBarReqDict = {}
        self.__barBufferDict = {}

        self.gateway = ibgw

        self.isRunning= False

    # ------------------------------------------------------------------------------
    def subscribe(self, req: VtHistoricalBarReq):
        # 将向IB请求历史数据所需的固定参数保存到列表，同时将onTick时需要的固定参数也保存到列表，供后续处理时使用。
        contract = Contract()
        contract.localSymbol = str(req.symbol)
        contract.exchange = exchangeMap.get(req.exchange, '')
        contract.secType = productClassMap.get(req.productClass, '')
        contract.currency = currencyMap.get(req.currency, '')
        contract.expiry = req.expiry
        contract.strike = req.strikePrice
        contract.right = optionTypeMap.get(req.optionType, '')

        st = datetime.strptime(req.start, '%Y%m%d %H:%M:%S').replace(
            tzinfo=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))
        et = datetime.strptime(req.end, '%Y%m%d %H:%M:%S').replace(
            tzinfo=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))

        # # 创建Tick对象并保存到字典中
        bar = VtBarData()
        bar.symbol = req.symbol
        bar.exchange = req.exchange
        bar.vtSymbol = '.'.join([bar.symbol, bar.exchange])
        bar.gatewayName = self.gateway.gatewayName
        bar.size = req.size
        dic = {
            'contractInfo': contract,
            'startDateTime': st,
            'endDateTime': et,
            'barInfo': bar,
        }

        self.histBarDataList.append(
            dic,
        )

        self.gateway.eventEngine.register(EVENT_TIMER, self.__processTimerEvent)
        logging.info(dic)

    # ------------------------------------------------------------------------------
    def __processTimerEvent(self, event):
        """
        根据缓存的请求，向IB发起历史tick数据的请求

        :return:
        """

        if not self.isRunning:
            return

        # Timer事件是1秒一次，在本方法中可以控制向IB请求历史数据的频率为ONE_CALL_INTERNAL秒一次。
        ONE_CALL_INTERNAL = 1
        RETRY_COUNT = 180 // ONE_CALL_INTERNAL

        if self.__internal_counter == -1:
            self.__internal_counter = 0
        elif self.__internal_counter < ONE_CALL_INTERNAL:
            self.__internal_counter += 1
            return
        else:
            self.__internal_counter = 0

        # 遍历请求列表
        want_del = []
        for o in self.histBarDataList:
            contract = o['contractInfo']
            st = o['startDateTime']
            et = o['endDateTime']

            # 为第一次请求设置一些属性
            if not 'lastTime' in o:
                o['lastTime'] = et + timedelta(seconds=-1)
                o['totalTicks'] = 0
                o['retry_count'] = 0
                o['reqId'] = None

            lt = o['lastTime']

            # 所有历史数据已经获取完毕，可以删除其请求对象；
            if st > et:
                want_del.append(o)
                logging.info('-------------数据获取完毕。%s' % o)
                continue

            # 另外，有时IB对于请求会延迟响应，此时下一个定时器事件会到来。为了避免重复请求，将上一次请求的时间记录下来，
            # 然后本次请求和st和at比较，如果st<=at，则表示已经请求过了。
            if et == lt:
                o['retry_count'] += 1
                # 如果重试大于n次，则先取消这笔请求，然后再重新请求
                if o['retry_count'] <= RETRY_COUNT:
                    continue

                # TODO: 取消这笔请求
                self.gateway.api.cancelHistoricalData(o['reqId'])
                self.histBarReqDict.pop(o['reqId'])

            self.gateway.tickerId += 1

            # TODO: 测试通过后在加入去
            # 创建Tick对象并保存到字典中
            # tick = VtTickData()
            # tick.symbol = subscribeReq.symbol
            # tick.exchange = subscribeReq.exchange
            # tick.vtSymbol = '.'.join([tick.symbol, tick.exchange])
            # tick.gatewayName = self.gatewayName
            # self.tickDict[self.tickerId] = tick
            # self.tickProductDict[self.tickerId] = subscribeReq.productClass

            self.histBarReqDict[self.gateway.tickerId] = o

            NUM_OF_TICKS = 1000
            self.gateway.api.reqHistoricalData(self.gateway.tickerId,
                                               contract,
                                               endDateTime=et.astimezone(
                                                   tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE'])).strftime(
                                                   '%Y%m%d %H:%M:%S'),
                                               durationStr=REQ_STEP_SIZE_MAP[o['barInfo'].size]['durationString'],
                                               barSizeSetting=REQ_STEP_SIZE_MAP[o['barInfo'].size]['barSizeSetting'],
                                               whatToShow=REQ_DATA_TYPE_MAP[contract.secType],
                                               useRTH=0,
                                               formatDate=2,
                                               keepUpToDate=False,
                                               chartOptions=[])

            o['lastTime'] = et
            o['reqId'] = self.gateway.tickerId
            o['retry_count'] = 0
            logging.info('-----------reqId=%d %s %s' %
                         (o['reqId'], contract.localSymbol, et.strftime('%Y%m%d %H:%M:%S')))

        # 删除已经接收完毕的请求数据
        for o in want_del:
            self.histBarDataList.remove(o)

    # --------------------------------------------------------------------
    def historicalData(self, reqId, bar):
        """
        :param reqId:
        :param ticks:
        :param done:
        :return:
        """

        if not reqId in self.__barBufferDict:
            self.__barBufferDict[reqId] = []
        else:
            self.__barBufferDict[reqId].append(bar)

    # ---------------------------------------------------------
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        """ Marks the ending of the historical bars reception. """

        if not reqId in self.__barBufferDict:
            logging.warning('reqId不存在于self.__barBufferDict')
            return

        val = self.histBarReqDict.pop(reqId)
        st = val['startDateTime']
        et = val['endDateTime']
        bar = val['barInfo']

        bars = self.__barBufferDict.pop(reqId)

        t = None
        t1 = None # 记录第一个有效数据的时间
        num = 0
        total = 0
        for o in bars:

            # 如果请求的是日线数据，则数据日期格式为yyyyMMDD，否则由formatDate参数指定（本程序指定为unix时间戳。
            if bar.size == '1 day':
                o.date = datetime.strptime(o.date, '%Y%m%d').timestamp()

            # IB返回来的数据的时区和登录TWS/IB Gateway时选择的时区一致。此时区必须配置在settings中。
            dt = datetime.fromtimestamp(int(o.date), tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))


            # 清洗数据，仅当st<=数据日期<et数据才有效。回调函数传入的ticks是按照时间升序排列的
            if dt < st:
                continue
            if dt > et:
                break

            if t1 == None:
                t1 = dt

            if t != dt:

                if t:
                    total += num
                    logging.debug('-----------%s %s num=%d' % (bar.symbol, t.strftime('%Y%m%d %H:%M:%S'), num))
                t = dt
                num = 0

            num += 1

            # 在mongodb内部，时间戳以UTC时区保存
            bar.datetime = dt.astimezone(pytz.timezone('UTC'))
            bar.time = dt.strftime('%H:%M:%S.%f')
            bar.date = dt.strftime('%Y%m%d')
            bar.open = o.open
            bar.high = o.high
            bar.low = o.low
            bar.close = o.close
            bar.volume = o.volume

            newbar = copy(bar)
            self.gateway.onBar(newbar)

        if t:
            t0 = datetime.fromtimestamp(int(bars[0].date), tz=pytz.timezone(settings.HISTORICAL_DATA['TIME_ZONE']))
            val['endDateTime'] = t0 + timedelta(seconds=-1)

            total += num
            val['totalTicks'] += total
            logging.info('-----------reqId=%d %s %s %d total=%d' %
                         (reqId, bar.symbol, t.strftime('%Y%m%d %H:%M:%S'), num, val['totalTicks']))

            info = {}
            info['vtSymbol'] = bar.vtSymbol
            info['type'] = 'bar'
            info['size'] = bar.size
            info['stime'] = t1.strftime('%Y%m%d %H:%M:%S')
            info['etime'] = t.strftime('%Y%m%d %H:%M:%S')
            info['total'] = val['totalTicks']
            self.gateway.onProgress(info)

        # 如果endDateTime等于lastTime，就表示本次请求的响应数据里面没有包含有效数据。（可能包含了startDateTime～endDateTime之外的数据）
        # 如果done又同时为真，那么就可以推论出所有数据都已经获得。
        if val['endDateTime'] == val['lastTime']:
            val['endDateTime'] = val['startDateTime'] + timedelta(seconds=-1)

    #--------------------------------------------------------------
    def setRunning(self, flag):
        self.isRunning = flag

    #--------------------------------------------------------------
    def getRunning(self):
        return self.isRunning


