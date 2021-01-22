from wtforms import Form, IntegerField, StringField
from wtforms.validators import Email, InputRequired, Length, EqualTo, ValidationError
from utils import redis_save_capthcha


class BaseForm(Form):
    def get_form_error_message(self):
        form_error_message = self.errors.popitem()[1][0]
        return form_error_message


# 登录表单验证
class LoginForm(BaseForm):
    email = StringField(validators=[Email(message='请输入正确格式的邮箱地址'), InputRequired(message='请输入邮箱地址')])
    password = StringField(validators=[Length(min=6, max=20, message='请输入6-20位的密码')])
    remember = IntegerField()


# 修改密码表单验证
class ResetPwdForm(BaseForm):
    oldpwd = StringField(validators=[Length(min=6, max=20, message='请输入6-20位密码')])
    newpwd = StringField(validators=[Length(min=6, max=20, message='请输入6-20位密码')])
    newpwd2 = StringField(validators=[EqualTo('newpwd', message='两次密码输入不一致')])


# 表单验证前端输入email和验证码并且验证这个验证码是否与保持在redis里面的一致
class ResetEmailForm(BaseForm):
    email = StringField(validators=[Email(message='请输入正确的邮箱格式')])
    captcha = StringField(validators=[Length(min=6, max=6, message='请正确长度的验证码')])

    def validate_captcha(self, field):
        # email = request.form.get('email')
        email = self.email.data
        # image_captcha = request.form.get('image_captcha')
        captcha = self.captcha.data
        # 从redis里面取验证码出来
        redis_captcha = redis_save_capthcha.redis_get(email)

        if not redis_captcha or captcha.lower() != redis_captcha.lower():
            raise ValidationError('验证码输入错误')
