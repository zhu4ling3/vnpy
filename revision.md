#修订记录

##2018-06-13～

* 修改runDataRecord，将开市闭市时间改为带时区的时间

* 支持将IB官方的Python API接口
    >vnpy项目中CPP API的版本比较旧，没有提供获取历史Tick的功能。
    直接升级CPP API涉及Makefile修改等内容，并且Windows环境下面还要安装VS
    作为编译器，比较繁琐。
    另外，不能对CPP API进行调整，不利于IB接口的初学者学习了解接口运行细节。
    综上，加入IB官方的Python API接口作为CPP API的替代方案。
    
    - 新增vnpy.api.ibpy Package
    - 新增vnpy.trader.gateway.ibGateway.ibGateway2
    - 修改vnpy.trader.gateway.ibGateway.\_\_init\_\_.py指向ibGateway2
    
* Python2->Python3环境
    - Python3.4 + Anaconda4.0.0 + requirement.txt + ta-lib0.4.9
    
* 新增采集IB历史数据的功能
    - 调用ibGateway.subscribe(req)的地方, dataRecorder模块drEngine
    - vtObject，新增VtHistoricalDataReq，用于从ibGateway.subscribe()的参数
    - 修改ibGateway.subscribe(req)方法，适应历史数据采集
    