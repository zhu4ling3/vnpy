# TODO: 模仿dataRecorder，收集历史数据

# encoding: UTF-8


from .hdEngine import HdEngine
from .uiHdWidget import HdEngineManager

appName = 'HistoricalData'
appDisplayName = u'历史数据记录'
appEngine = HdEngine
appWidget = HdEngineManager
appIco = 'dr.ico'