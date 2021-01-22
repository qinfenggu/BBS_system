from flask import Blueprint, render_template, views, request, redirect, url_for, session, g, jsonify
from apps.cms.forms import LoginForm, ResetPwdForm, ResetEmailForm
from apps.cms.models import CMSUser, CMSPersmission
from apps.cms.decorators import permission_required
from excit import db, mail
from utils import restful, random_captcha, redis_save_capthcha
from flask_mail import Message


cms_bp = Blueprint('cms', __name__, url_prefix='/cms')


# 访问这个view.py里所有的视图都会先执行这个cms_before_request方法进行验证是否得登录
@cms_bp.before_request
def cms_before_request():
    # 如果不是后台登录页面。
    if not request.path.endswith(url_for('cms.login')):
        user_id = session.get('user_id')
        if user_id:
            user = CMSUser.query.get(user_id)
            if user:
                g.user = user
        else:
            return redirect(url_for('cms.login'))


# 上下文处理器。用于HTML能够使用判断CMSPersmission类。
# 目的：用于判断当前用户是否含有帖子，评论，板块这些权限，有就显示出对应的帖子，评论，板块这些按钮
@cms_bp.context_processor
def cms_context_processor():
    return {'CMSPersmission': CMSPersmission}


# 进去CMS第一时间主页
def cms_home_page():
    return render_template('cms/cms_home_page.html')


# 退出CMS,重定向回登录页面
def cms_logout_view():
    session.clear()
    return redirect(url_for('cms.login'))


# CMS个人信息页面
def cms_profile_view():
    return render_template('cms/cms_profile.html')


# 登录CMS后台
class CMSLoginView(views.MethodView):
    def get(self, error_message=None):
        context = {
            'error_message': error_message
        }
        return render_template('/cms/cms_login.html', **context)

    def post(self):
        login_form = LoginForm(request.form)
        if login_form.validate():
            # 验证post请求过来的邮箱和密码是否和数据库一致
            email = login_form.email.data
            password = login_form.password.data
            remember = login_form.remember.data
            # 这是实例化CMSUser类，所以下面才user.check_password
            user = CMSUser.query.filter_by(email=email).first()
            # user这个就是邮箱在数据库里面存不存在。user.check_password这个就是验证密码
            if user and user.check_password(password):
                # 用于后面验证访问页面之前是否已登录的
                session['user_id'] = user.id
                if remember:
                    session.permanent = True
                return redirect(url_for('cms.home_page'))
            else:
                return self.get(error_message='邮箱地址或密码不正确')
        else:
            return self.get(login_form.get_form_error_message())


# 修改密码
class ResetPwdView(views.MethodView):
    def get(self):
        return render_template('cms/cms_resetpwd.html')

    def post(self):
        reset_form = ResetPwdForm(request.form)
        if reset_form.validate():
            oldpwd = reset_form.oldpwd.data
            newpwd = reset_form.newpwd.data
            # g.user就是 CMSUser.query.get(user_id)
            user = g.user
            if user.check_password(oldpwd):
                # user.password = newpwd其实是调用了models.py里面CMSUser类下的@password.setter方法
                user.password = newpwd
                db.session.commit()
                return restful.success()
            else:
                return restful.params_errors(message='旧密码输入不正确，请重新输入')
        else:
            return restful.params_errors(message=reset_form.get_form_error_message())


# 修改邮箱
class ResetMailView(views.MethodView):
    def get(self):
        return render_template('cms/cms_resetemail.html')

    def post(self):
        reset_form = ResetEmailForm(request.form)
        if reset_form.validate():
            email = reset_form.email.data
            # user就是 CMSUser.query.get(user_id)
            user = g.user
            user.email = email
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message=reset_form.get_form_error_message())


# 发送邮箱。利用ajax，当点HTML的获取验证码按钮后就会触发这个/email_captcha/，从而触发这个get请求
class EmailCaptchaView(views.MethodView):
    def get(self):
        # 获取前端输入的邮箱地址
        email = request.args.get('email')
        if not email:
            return restful.params_errors('请输入邮箱地址！')
        # 随机生成验证码并向邮件发送这个验证码
        capthcha = random_captcha.get_random_captcha(6)
        message = Message('【轻风言论坛】修改邮箱', recipients=[email], body='你的邮箱验证码：%s' %capthcha)
        try:
            mail.send(message)
        except:
            return restful.server_errors()
        # 把验证码保持到redis数据库里面
        redis_save_capthcha.redis_set(key=email, value=capthcha)
        return restful.success()


# 帖子管理。@permission_required装饰器是在执行cms_posts_view之前进行判断当前用户是否拥有帖子权限
@permission_required(CMSPersmission.POSTER)
def cms_posts_view():
    return '帖子'


# 评论管理
@permission_required(CMSPersmission.COMMENTER)
def cms_comments_view():
    return '评论'


# 板块管理
@permission_required(CMSPersmission.BOARDER)
def cms_boards_view():
    return '板块'


# 前台用户管理
@permission_required(CMSPersmission.FRONTUSER)
def cms_frontuser_manage_view():
    return '板块'


# 后台用户管理
@permission_required(CMSPersmission.CMSUSER)
def cms_cmsuser_manage_view():
    return '板块'


# 角色管理
def cms_roles_view():
    return '角色'


cms_bp.add_url_rule('/home_page/', endpoint='home_page', view_func=cms_home_page)
cms_bp.add_url_rule('/logout/', endpoint='logout', view_func=cms_logout_view)
cms_bp.add_url_rule('/profile/', endpoint='profile', view_func=cms_profile_view)
cms_bp.add_url_rule('/posts/', endpoint='posts', view_func=cms_posts_view)
cms_bp.add_url_rule('/comments/', endpoint='comments', view_func=cms_comments_view)
cms_bp.add_url_rule('/boards/', endpoint='boards', view_func=cms_boards_view)
cms_bp.add_url_rule('/frontuser_manage/', endpoint='frontuser_manage', view_func=cms_frontuser_manage_view)
cms_bp.add_url_rule('/cmsuser_manage/', endpoint='cmsuser_manage', view_func=cms_cmsuser_manage_view)
cms_bp.add_url_rule('/roles/', endpoint='roles', view_func=cms_roles_view)


cms_bp.add_url_rule('/login/', view_func=CMSLoginView.as_view('login'))
cms_bp.add_url_rule('/resetpwd/', view_func=ResetPwdView.as_view('resetpwd'))
cms_bp.add_url_rule('/resetemail/', view_func=ResetMailView.as_view('resetemail'))
cms_bp.add_url_rule('/email_captcha/', view_func=EmailCaptchaView.as_view('email_captcha'))
