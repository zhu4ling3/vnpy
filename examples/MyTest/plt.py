import datetime
import csv
import matplotlib.pyplot as plt
import mpl_finance as mpf
import matplotlib.dates as mpd
import pymongo
import pytz
import talib
import numpy as np

str2date =lambda x: mpd.date2num(datetime.datetime.strptime(x, '%m/%d/%Y').date())

data_text = """
date\topen\thigh\tlow\tclose\tVolume
1/4/2000\t1368.692993\t1407.517944\t1361.213989\t1406.370972\t0
1/5/2000\t1407.828979\t1433.780029\t1398.322998\t1409.682007\t0
1/6/2000\t1406.036011\t1463.954956\t1400.253052\t1463.942017\t0
1/7/2000\t1477.154053\t1522.824951\t1477.154053\t1516.604004\t0
1/8/2000\t1477.154053\t1522.824951\t1477.154053\t1516.604004\t0
1/9/2000\t1531.712036\t1546.723022\t1506.404053\t1545.112061\t0
1/10/2000\t1531.712036\t1546.723022\t1506.404053\t1545.112061\t0
1/11/2000\t1547.677979\t1547.708008\t1468.756958\t1479.781006\t0
1/12/2000\t1473.760986\t1489.280029\t1434.995972\t1438.02002\t0"""
# data_list = list(csv.reader(data_text.strip().splitlines(), delimiter='\t'))
# columns = data_list[0]
# quotes = [[str2date(d[0])] + [float(v) for v in d[1:-1]] for d in data_list[1:]]


dbClient = pymongo.MongoClient('localhost', 27017)
collection = dbClient['VnTrader_1Day_Db']['BABA.SMART']
stime = datetime.datetime.strptime('2010-07-20 09:18:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone('US/Eastern'))
etime = datetime.datetime.strptime('2018-07-21 23:00:00', '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone('US/Eastern'))
flt = {'datetime': {'$gte': stime,
                    '$lte': etime}
       }
dbCursor = collection.find(flt).sort('datetime')
quotes = [ [mpd.date2num(r['datetime']), r['open'], r['high'], r['low'], r['close'], r['volume']] for r in dbCursor]

print(quotes)

DAYS200 = 200
DAYS60 = 60
sma200 = talib.SMA(np.array([o[4] for o in quotes]),DAYS200)
sma60 = talib.SMA(np.array([o[4] for o in quotes]),DAYS60)
dat = np.array([o[0] for o in quotes])


fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(6,4), facecolor=(0.5, 0.5, 0.5))
fig.subplots_adjust(bottom=0.2)


# mpf.candlestick_ohlc(ax,quotes,width=0.4/(24*60),colorup='g',colordown='r')
mpf.candlestick_ohlc(ax1,quotes,width=0.4,colorup='g',colordown='r')
ax1.xaxis_date()
ax1.autoscale_view()
ax1.plot(dat[DAYS200:-1], sma200[DAYS200:-1],  'r-')
ax1.plot(dat[DAYS60:-1], sma60[DAYS60:-1],  'b-')

# pCandle = plt.subplot(2,1,1)
# pCandle.grid(False)
# pCandle.plot(dat[DAYS200:-1], sma[DAYS200:-1],  'r-')

# pTr = plt.subplot(2, 1, 2)
# t = pTr.table(cellText=[[11, 12, 13], [21, 22, 23], [28, 29, 30]], rowLabels=['a', 'b', 'c'],
#               colLabels=['x', 'y', 'z'], )

plt.title("BABA")
plt.xlabel("Date")
plt.ylabel("Price")

plt.setp(plt.gca().get_xticklabels(), rotation=30)
plt.show()
