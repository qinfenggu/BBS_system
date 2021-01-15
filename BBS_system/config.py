import os

HOSTNAME = "rm-bp16ao46vc2m2ks1y2o.mysql.rds.aliyuncs.com"
DATEBASE = "bbs_system"
PORT = 3306
USERNAME = 'qingfeng_gu'
PASSWORD = 'qingfeng_gu123'
con = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATEBASE)
SQLALCHEMY_DATABASE_URI = con  # 这是创建引擎语句
SQLALCHEMY_TRACK_MODIFICATIONS = False  # 这是消除警告

DEBUG = False
SECRET_KEY = os.urandom(10)


