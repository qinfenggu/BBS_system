"""这个是写视图逻辑的"""
from . import api
from lghome import db
import logging


@api.route('/index')
def index():
    logging.warning('数据库连接失败')
    return "index page"


@api.route('/profile')
def profile():
    return '个人中心'
