"""这个是蓝图。蓝图的书写格式代码写到这个包的__init__文件里面我确实是没有想到，而且还得把视图的文件给导入进来"""
from flask import Blueprint

api = Blueprint('api_1_0', __name__, url_prefix='/api/v1.0')

# 必须把写视图的文件给导入，不然你不在这里导入，你写视图谁知道你这个视图的文件和谁关联。
from . import dmeo, verify_code, passport, profile, houses, orders, pay