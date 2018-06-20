#关于IB市场行情数据接口的注意事项
- 应用程序并不是直接连接到IB的服务器，而是通过TWS（默认端口4793）或者IB Gateway（默认端口4002）和IB
服务器交互。
- 要想从IB获得市场行情数据，必须满足以下dirdoe前提：
    - 有对应资产的交易权限
    - 账号已经入金（获取外汇和债券的数据除外）
    - 付费订阅了相关产品的行情数据
    - 没有超过最大Market Data Line的限制
        > Market Data Line的概念是对一种产品(Instrument)的实时数据请求占用一个Market Data Line。
        系统默认每个用户的最大Market Data Line数量为100，它包括TWS中和API应用程序中所有产品的合计。
- IB对于获取行情数据另有一些技术限制，见后说明。


#市场数据的种类
###实时数据
IB提供三种精度的实时数据：原始tick级，合成tick级(1秒内多次)，Bar级。
- 原始tick数据。Tick-by-Tick Data。高精度数据，TWS v969+ and API v973.04+之后才支持。形如“TWS Time & Sales Window”界面的数据。
    >限制：最多5个产品可以接收原始tick
- 合成tick数据。Streaming market data。此数据是根据原始tick进行合成的tick数据，1秒钟内会有几个快照。
- Bar数据。5 Second Real Time Bars 。每5秒产生一个Bar，包含OHLC值。


###历史数据
IB提供两种精度的历史数据：原始tick级，Bar级。
- 原始tick数据。Tick-by-Tick Data。TWS v968+ and API v973.04+之后才支持。形如“TWS Time & Sales Window”界面的数据。
- Bar级数据。Historical Bar Data。1分钟，5分钟......小时，日，周，月的Bar数据。

    
#实时数据-合成tick数据的请求和接收
###用reqMktData()请求数据
- 返回的数据包含常规数据项，如果需要额外的可选项，用genericTickList参数指定获取
    > 可获得的数据项参考：http://interactivebrokers.github.io/tws-api/tick_types.html
- 如果订阅了NetworkA/B/C，可以请求市场快照数据一次（11秒内），而不必接收不停变动的数据。
- 法规快照Regulatory Snapshots。如果订阅了“US Securities Snapshot Bundle”，可以获得实时计算的NBBO
价格（美国国内最佳买卖价格）。第五个参数指定是否请求法规快照。
    > 每一次Regulatory Snapshot的生成需要支付0.01美元。

###用tickPrice(),tickSize(),tickString()接收数据
reqMktData()请求的数据是异步返回的，并且根据返回数据的类型用不同的函数返回。
- tickPrice()。接收Decimal数据。例如BidPrice, AskPrice等
- tickSize()。接收int数据。例如Volume等。
- tickString()。接收字符串或者日期等类型。例如成交时间等。




#tick-by-tick数据




   