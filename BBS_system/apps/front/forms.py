from wtforms import Form, StringField
from wtforms.validators import Length, EqualTo, ValidationError, Regexp
from utils import redis_save_capthcha


class BaseForm(Form):
    def get_form_error_message(self):
        form_error_message = self.errors.popitem()[1][0]
        return form_error_message


# 注册页面表单验证
class SignUpForm(BaseForm):
    telephone = StringField(validators=[Regexp(r'1[345789]\d{9}', message='请输入合法的手机号码')])
    sms_captcha = StringField(validators=[Length(min=6, max=6, message='请输入正确的短信验证码')])
    username = StringField(validators=[Length(min=4, max=20, message='请输入由数字和大小写组成的4-20位用户名')])
    password1 = StringField(validators=[Regexp(r'[0-9a-zA-Z]'), Length(min=6, max=20, message='请输入由数字和大小写组成的6-20位用户名')])
    password2 = StringField(validators=[EqualTo('password1', message='两次密码输入不一致')])
    graph_captcha = StringField(validators=[Length(min=4, max=4, message='请输入正确的验证码')])

    # 验证输入的短信验证码与redis里面是否一致
    def validate_sms_captcha(self, field):
        telephone = self.telephone.data
        sms_captcha = self.sms_captcha.data
        # 把短信验证码从redis里面取出来
        redis_sms_captcha = redis_save_capthcha.redis_get(telephone)
        if not redis_sms_captcha or redis_sms_captcha != sms_captcha:
            raise ValidationError(message='短信验证码输入错误')

    # 验证输入的图形验证码与redis里面是否一致
    def validate_graph_captcha(self, field):
        graph_captcha = self.graph_captcha.data
        # 把图形验证码从redis里面取出来。graph_captcha.lower()转小写原因：图形验证码保存到redis时，key就是验证码的小写
        redis_graph_captcha = redis_save_capthcha.redis_get(graph_captcha.lower())
        if not redis_graph_captcha:
            raise ValidationError(message='图形验证码输入错误')
