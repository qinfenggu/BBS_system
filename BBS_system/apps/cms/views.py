from flask import Blueprint, render_template, views, request, redirect, url_for, session, g, jsonify
from apps.cms.forms import LoginForm, ResetPwdForm
from apps.cms.models import CMSUser
from excit import db
from utils import restful

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


class ResetMailView(views.MethodView):
    def get(self):
        return render_template('cms/cms_resetemail.html')

    def post(self):
        pass


cms_bp.add_url_rule('/', endpoint='home_page', view_func=cms_home_page)
cms_bp.add_url_rule('/logout/', endpoint='logout', view_func=cms_logout_view)
cms_bp.add_url_rule('/profile/', endpoint='profile', view_func=cms_profile_view)
cms_bp.add_url_rule('/login/', view_func=CMSLoginView.as_view('login'))
cms_bp.add_url_rule('/resetpwd/', view_func=ResetPwdView.as_view('resetpwd'))
cms_bp.add_url_rule('/resetemail/', view_func=ResetMailView.as_view('resetemail'))
