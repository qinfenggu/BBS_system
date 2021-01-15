from excit import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class CMSUser(db.Model):
    __tablename__ = 'cms_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    _password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    create_time = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, username, password, email):
        self.username = username
        # 会调用@password.setter下方法，self.password原是个方法，后为属性，属性值self._password
        self.password = password
        self.email = email

    @property
    def password(self):
        return self._password

    # 对传过来的密码进行加密
    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    # 验证传过来的密码是否和数据库里面的一致
    def check_password(self, passe_password):
        result = check_password_hash(self.password, passe_password)
        return result







