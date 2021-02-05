from wtforms import Form, IntegerField, StringField
from wtforms.validators import Email, InputRequired, Length, EqualTo, ValidationError, URL, Regexp
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


# 添加轮播图表单验证
class AddBannerForm(BaseForm):
    name = StringField(validators=[InputRequired(message='请输入轮播图名称')])
    image_url = StringField(validators=[InputRequired(message='请输入图片链接'), URL(message='图片链接有误')])
    link_url = StringField(validators=[InputRequired(message='请输入跳转链接'), URL(message='图片链接有误')])
    priority = IntegerField(validators=[InputRequired(message='请输入轮播图优先级')])


# 更新轮播图表单验证
class UpdateBannerForm(AddBannerForm):
    # 添加上去的轮播图信息都是按顺序排序的，每次添加都会自动有一个序号banner_id。它存在证明是'编辑',它不存在证明是'添加轮播图'。
    # 而表单验证这个字段是因为在ajax的post请求里面的'data'有banner_id这个字段
    banner_id = IntegerField(validators=[InputRequired(message='轮播图不存在')])


# 添加板块表单验证
class AddBoardForm(BaseForm):
    name = StringField(validators=[InputRequired(message='请输入板块名称')])


# 更新板块表单验证
class UpdateBoardForm(AddBoardForm):
    # 添加上去的板块信息都是按顺序排序的，每次添加都会自动有一个序号banner_id。
    # 而要表单验证这个字段是因为在ajax的post请求里面的'data'有banner_id这个字段
    board_id = StringField(validators=[InputRequired(message='请输入板块ID')])


# 添加管理员表单验证
class AddCmsUserForm(BaseForm):
    username = StringField(validators=[InputRequired(message='请输入用户名')])
    password = StringField(validators=[Length(min=6, max=20, message='请输入6-20位的密码')])
    password2 = StringField(validators=[EqualTo('password', message='两次密码输入不一致')])
    email = StringField(validators=[Email(message='请输入正确格式的邮箱地址'), InputRequired(message='请输入邮箱地址')])
    role = StringField(validators=[InputRequired(message='请选择角色')])


# 管理员添加角色表单验证
class UpdateCmsUserRole(BaseForm):
    # 正则只能是1234
    role_id = StringField(validators=[Regexp(r'[1234]', message='请输入正确的角色序号')])
