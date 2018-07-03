import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HISTORICAL_DATA = {
    'REQUESTS': {
        'working': True,
        'list': [
            {
                'workflag': False,
                'symbol': 'XAUUSD',
                'gateway': 'IB',
                'exchange': 'SMART',
                'currency': 'USD',
                'sectype': '现货',
                'start': '20160101 00:00:00',
                'end': '20180703 00:00:00',
                'datatype': [
                    'tick',
                    'bar',
                ],
            },
            {
                'workflag': False,
                'symbol': 'USD.JPY',
                'gateway': 'IB',
                'exchange': 'IDEALPRO',
                'currency': 'JPY',
                'sectype': '外汇',
                'start': '20160101 00:00:00',
                'end': '20180703 00:00:00',
                'datatype': [
                    'tick',
                    'bar',
                ],
            },
            {
                'workflag': True,
                'symbol': 'BABA',
                'gateway': 'IB',
                'exchange': 'SMART',
                'currency': 'USD',
                'sectype': '股票',
                'start': '20180702 00:00:00',
                'end': '20180702 09:33:00',
                'datatype': [
                    'tick',
                    'bar',
                ],
            },
        ],
    },

    'FOLDER': os.path.join(BASE_DIR, 'examples', 'HistoricalData', 'temp'),
    'TIME_ZONE': 'US/Eastern', # 这个时区是指登录TWS/IB Gateway时选择的时区，同时也是IB历史市场数据的时区。
}
