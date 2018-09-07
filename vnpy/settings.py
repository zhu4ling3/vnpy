import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

"""
bar size：
1 secs, 5 secs, 10 secs, 15 secs, 30 secs;
1 min, 2 mins, 3 mins, 5 mins, 10 mins, 15 mins, 20 mins, 30 mins;
1 hour, 2 hours, 3 hours, 4 housr, 8 hours;
1 day
1 week
1 month
"""
HISTORICAL_DATA = {
    'REQUESTS': {
        'working': True,
        'list': [
            {
                'workflag': True,
                'symbol': 'GOOG',
                'gateway': 'IB',
                'exchange': 'SMART',
                'currency': 'USD',
                'sectype': '股票',
                'start': '20010101 00:00:00',
                'end': '20180908 00:00:00',
                'objects': [
                    #{'type':'tick'},
                    # {'type': 'bar', 'size': '1 min'},
#                    {'type': 'bar', 'size': '1 hour'},
                   {'type': 'bar', 'size': '1 day'},
                ],
            },
            {
                'workflag': False,
                'symbol': 'XAUUSD',
                'gateway': 'IB',
                'exchange': 'SMART',
                'currency': 'USD',
                'sectype': '现货',
                'start': '20100101 00:00:00',
                'end': '20180707 00:00:00',
                'objects': [
                    #{'type':'tick', 'gen':'1 min'},
                    {'type':'tick'},
                    {'type': 'bar', 'size': '1 min'},
                    {'type': 'bar', 'size': '1 hour'},
                    {'type': 'bar', 'size': '1 day'},
                ],
            },
            {
                'workflag': False,
                'symbol': 'USD.JPY',
                'gateway': 'IB',
                'exchange': 'IDEALPRO',
                'currency': 'JPY',
                'sectype': '外汇',
                'start': '20100101 00:00:00',
                'end': '20180707 00:00:00',
                'objects': [
                    {'type':'tick'},
                    {'type': 'bar', 'size': '1 min'},
                    {'type': 'bar', 'size': '1 hour'},
                    {'type': 'bar', 'size': '1 day'},
                ],
            },
            {
                'workflag': False,
                'symbol': 'BABA',
                'gateway': 'IB',
                'exchange': 'SMART',
                'currency': 'USD',
                'sectype': '股票',
                'start': '20150101 00:00:00',
                'end': '20180721 00:00:00',
                'objects': [
                    #{'type':'tick'},
                    {'type': 'bar', 'size': '1 min'},
#                    {'type': 'bar', 'size': '1 hour'},
#                    {'type': 'bar', 'size': '1 day'},
                ],
            },
        ],
    },

    'FOLDER': os.path.join(BASE_DIR, 'examples', 'HistoricalData', 'temp'),
    'TIME_ZONE': 'US/Eastern',  # 这个时区是指登录TWS/IB Gateway时选择的时区，同时也是IB历史市场数据的时区。
}
