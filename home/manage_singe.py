from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect

app = Flask(__name__)


class Config(object):
    """配置信息"""

    SECRET_KEY = 'ASDAXCWE5ERTFG%%DAS34'
    USERNAME = 'qingfeng_gu'
    PASSWORD = 'qingfeng_gu123'
    HOSTNAME = 'rm-bp16ao46vc2m2ks1y2o.mysql.rds.aliyuncs.com'
    PORT     = 3306
    DATEBASE = 'home'

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask-session。保存到什么数据库
    SESSION_TYPE = 'redis'
    # 与那个数据库建立连接关系
    SESSION_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    # 是否想加密。如果不想加密就写False，想加密就写True并且。SECRET_KEY = 'xxxxx随便写'
    SESSION_USE_SIGNER = True
    # 保存到redis有效期
    PERMANENT_SESSION_LIFETIME = 8640   # 单位是秒

    # 数据库。这是创建引擎语句
    DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATEBASE)

# 加载配置文件
app.config.from_object(Config)

# 这是分离数据库那个第三方那个db。
db = SQLAlchemy(app)

# 创建Redis即；连接redis
redis_store = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# session
Session(app)

# post请求  wtf  csrf
CSRFProtect(app)


@app.route('/')
def index():
    return "index page"


if __name__ == '__main__':
    app.run()