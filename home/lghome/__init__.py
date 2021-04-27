"""因为不用app.py文件当做主文件"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from config import config_map
import redis
import logging
from logging.handlers import RotatingFileHandler
from lghome.utils.commons import ReConverter


# 这个db放在外面，不放在create_app里面。因为别的py文件需要调用这个db
db = SQLAlchemy()

# 创建Redis。同理这个定在外面原因，别的py需要调用它
redis_store = None


# 日志。这个函数网上一大堆。直接用它就行。里面的代码了解一下就ok
def setup_log():
    # 设置日志的的登记  DEBUG调试级别
    logging.basicConfig(level=logging.DEBUG)
    # 创建日志记录器，设置日志的保存路径和每个日志的大小和日志的总大小
    # maxBytes表示每个日志最大可传100M 1024*1024*100=100M 。如果一个日志100M满了就会创建一个新的日志文件，上限可创建100个日志文件
    file_log_handler = RotatingFileHandler("logs/log.log", maxBytes=1024*1024*100,backupCount=100)
    # 创建日志记录格式，日志等级，输出日志的文件名 行数 日志信息
    formatter = logging.Formatter("%(asctime)s-%(levelname)s %(filename)s: %(lineno)d %(message)s")
    # 为日志记录器设置记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flaks app使用的）加载日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 工厂模式。这个函数里面的代码都是原先需要在app.py里面写的代码。
def create_app(config_name):
    # 开始启动日志
    setup_log()
    app = Flask(__name__)

    # 这个是取 config_map字典里面的传过来config_name的key的值
    config_class = config_map.get(config_name)
    # 这个注册配置文件
    app.config.from_object(config_class)

    # 使用app初始化db。上面db = SQLAlchemy()而做的
    db.init_app(app)

    # redis配置
    global redis_store
    # 连接redis
    redis_store = redis.Redis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

    # session。配置文件里面写好配置代码确认把session保存到那个数据库里面。然后在app.py写到先这个代码
    Session(app)

    # 这个是那个flask-wtf的csrf保护
    CSRFProtect(app)

    # 为flask添加自定义的转换器。重写BaseConverter类，然后在app.py里面写这个代码。主要是可以在定义路由时可以自己自定义正则表达式
    app.url_map.converters['re'] = ReConverter

    # 弄view.py的蓝图，主要做页面逻辑功能。注册蓝图。这个导入必须写到这里。不可以把这个导入代码放到上面。不然会出现报错
    from lghome import api_1_0
    app.register_blueprint(api_1_0.api)

    # 显示前端代码。注册静态文件蓝图。本来HTML是放到Nginx，但是没有这个服务器。就定义到蓝图里面
    from lghome import web_html
    app.register_blueprint(web_html.html)

    return app






