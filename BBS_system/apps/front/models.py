from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from excit import db
import enum
import shortuuid


class GenderEnum(enum.Enum):
    MALE = 1
    FEMALE = 2
    UNKNOW = 3


# 前台用户
class FrontUser(db.Model):
    __tablename__ = 'front_user'
    # 为了安全，id就不按数字了，而且 shortuuid.uuid生成16位唯一随机字符串
    id = db.Column(db.String(100), primary_key=True, default=shortuuid.uuid)
    telephone = db.Column(db.String(11), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False)
    _password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    # realname真实姓名，head_portrait头像，signature个性签名
    realname = db.Column(db.String(50))
    head_portrait = db.Column(db.String(100))
    signature = db.Column(db.String(100))
    gender = db.Column(db.Enum(GenderEnum), default=GenderEnum.UNKNOW)

    create_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, *args, **kwargs):
        if "password" in kwargs:
            # 会调用@password.setter下方法，self.password原是个方法，后为属性，属性值self._password
            self.password = kwargs.get('password')
            kwargs.pop('password')

        # super(FrontUser, self).__init__(*args, **kwargs) 这是python2写法。
        # 在模型里面，可以把上面的类属性按这样子定义，类属性值都是Noen。而类名（类属性名=值），就是给它们赋值。
        # 类名（类属性名=值）这种在Python语法里面是不成立的。但是这个用在模型里面成立
        super().__init__(*args, **kwargs)

    @property
    def password(self):
        return self._password

    # 添加前台用户时对传过来的密码即raw_password进行加密
    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    # 验证前端form表单传过来的密码是否和数据库里面的一致
    def check_password(self, passe_password):
        result = check_password_hash(self.password, passe_password)
        return result
