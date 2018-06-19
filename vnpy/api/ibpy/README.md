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
- IB对于获取历史行情数据另有一些技术限制，见后说明。


#市场数据的种类
##实时数据
IB提供三种精度的实时数据：tick级，秒内级，秒间级。
- 快照数据snapshot。此数据并非tick-by-tick数据，而是根据tick-by-tick进行合成的数据，1秒钟内会有几个快照。
- tick-by-ticks数据。高精度数据，TWS v969 and API v973.04之后才支持。

##    
#快照数据snapshot的请求和接收
###用reqMktData()请求数据
- 返回的数据包含常规数据项，如果需要额外的可选项，用genericTickList参数指定获取
    > 可获得的数据项参考：http://interactivebrokers.github.io/tws-api/tick_types.html
- 如果订阅了NetworkA/B/C，可以请求市场快照数据一次（11秒内），而不必接收不停变动的数据。
- 法规快照Regulatory Snapshots。如果订阅了“US Securities Snapshot Bundle”，可以获得实时计算的NBBO
价格（美国国内最佳买卖价格）。第五个参数指定是否请求法规快照。
    > 每一次Regulatory Snapshot的生成需要支付0.01美元。

###用tickPrice()和tickSize()接收数据
reqMktData()请求的数据是异步返回的，并且根据返回数据的类型用不同的函数返回，例如


#tick-by-tick数据




   