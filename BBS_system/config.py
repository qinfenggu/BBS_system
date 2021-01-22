import os

HOSTNAME = "rm-bp16ao46vc2m2ks1y2o.mysql.rds.aliyuncs.com"
DATEBASE = "bbs_system"
PORT = 3306
USERNAME = 'qingfeng_gu'
PASSWORD = 'qingfeng_gu123'
con = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATEBASE)
SQLALCHEMY_DATABASE_URI = con  # 这是创建引擎语句
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 这是消除警告

# 发送邮箱的服务地址  QQ邮箱
MAIL_SERVER = 'smtp.qq.com'
# 端口465或587
MAIL_PORT = '587'
MAIL_USE_TLS = True
# MAIL_USE_SSL : default False  465

MAIL_USERNAME = '3136413608@qq.com'
# 不是QQ密码
MAIL_PASSWORD = 'jvnjpvyegeqldgfa'
MAIL_DEFAULT_SENDER = '3136413608@qq.com'

DEBUG = True
SECRET_KEY = os.urandom(10)
TEMPLATES_AUTO_RELOAD = True   # 这是让模板自动更新到最新语句


