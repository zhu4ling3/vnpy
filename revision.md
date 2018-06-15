#修订记录

##2018-06-13～

* 修改runDataRecord，将开市闭市时间改为带时区的时间
* 新增采集IB历史数据的功能
    - 调用ibGateway.subscribe(req)的地方, dataRecorder模块drEngine
    - vtObject，新增VtHistoricalDataReq，用于从ibGateway.subscribe()的参数
    - 修改ibGateway.subscribe(req)方法，适应历史数据采集
    