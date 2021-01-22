# @ Time    : 2020/5/8 21:27
# @ Author  : JuRan

from wtforms import Form, StringField
from wtforms.validators import InputRequired, Regexp
import hashlib


# 短信验证码，那只要有人知道这个发送短信验证码URL和传的参数，通过postman就可以无限的发送短信了。
# 为了解决这个问题，在发送短信验证码之前进行验证前端传过来sign和q3423805gdflvbdfvhsdoa`#$%加密后是否一致。这是验证js那边的
class SMSCaptchaForm(Form):
    telephone = StringField(validators=[Regexp(r'1[345789]\d{9}')])
    timestamp = StringField(validators=[Regexp(r'\d{13}')])
    sign = StringField(validators=[InputRequired()])

    # 验证前端发送过来的sign和后端加密之后的sign 是否一致

    def validate_sign(self, field):
        telephone = self.telephone.data
        timestamp = self.timestamp.data
        sign = self.sign.data

        # 服务端加密之后生成的
        sign2 = hashlib.md5((timestamp + telephone + 'q3423805gdflvbdfvhsdoa`#$%').encode('utf-8')).hexdigest()

        if sign == sign2:
            return True
        else:
            return False





