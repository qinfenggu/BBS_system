from wtforms import Form, IntegerField, StringField
from wtforms.validators import Email, InputRequired, Length, EqualTo


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
