# encoding: UTF-8

from __future__ import absolute_import
import json
import os
import traceback

# 默认设置
from .chinese import text

# 获取目录上级路径
path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SETTING_FILENAME = 'VT_setting.json'
SETTING_FILENAME = os.path.join(path, SETTING_FILENAME)

# 打开配置文件，读取语言配置
# python3环境下面不兼容。执行setting = json.load(f)时报错，UnicodeDecodeError: 'gbk' codec can't decode byte 0xae in position 21: illegal multibyte sequence。
# try:
#     with open(SETTING_FILENAME) as f:
#         setting = json.load(f)
#     if setting['language'] == 'english':
#         from .english import text
# except Exception:
#     traceback.print_exc()
try:
    with open(SETTING_FILENAME, 'r', encoding='UTF-8') as f:
        setting = json.load(f)
    if setting['language'] == 'english':
        from .english import text
except Exception:
    traceback.print_exc()