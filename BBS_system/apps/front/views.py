from flask import Blueprint, views, render_template, Response, request, session
from utils.image_captcha.image_captcha import Captcha
from utils import redis_save_capthcha, restful, safe_url
from io import BytesIO
from .forms import SignUpForm, SignInForm
from .models import FrontUser
from excit import db

front_bp = Blueprint("front", __name__)


def front_home_page():
    return render_template('front/front_home_page.html')


# 把图形验证码映射到前端页面。
# 一个图片充当返回值，要映射到前端页面，必须得把图片保存到字节流流中,然后Response(out.read(), mimetype='image/png')
def graph_captcha():
    try:
        # text生成的验证码 。image就是图形验证码图片
        text, image = Captcha.gene_graph_captcha()
        # BytesIO 字节流
        out = BytesIO()
        # 把图片保存在字节流中  并制定格式png
        image.save(out, 'png')
        # 文件流指针。从0位置开始读，必须要有
        out.seek(0)
        # 把图形验证码保存到redis里面。下面key和value都text.lower()这样转小写原因：利于后续前端输入验证码与这保存到redis里的验证码
        # 匹配时有忽略大小写功能
        redis_save_capthcha.redis_set(text.lower(), text.lower())
    except:
        # 如果异常再重新执行一遍
        return graph_captcha()
    return Response(out.read(), mimetype='image/png')


# 注册
class SignupView(views.MethodView):
    def get(self):
        return_to = request.referrer
        # 访问当前注册页面是否是通过点击类似a标签这种URL页面跳转过来访问的。如果是，并且这种URL页面是在这个项目里面而不是通过反爬访问
        # 则注册成功通过js来跳转回那个URL页面。如果不是就跳转到fron_home_page。
        if return_to and safe_url.is_safe_url(return_to):
            return render_template("front/front_signup.html", return_to=return_to)
        else:
            return render_template("front/front_signup.html")

    def post(self):
        # SignUpForm已进行表单验证和短信验证码，图形验证码是否与redis里面一致验证
        signup_form = SignUpForm(request.form)
        if signup_form.validate():
            telephone = signup_form.telephone.data
            username = signup_form.username.data
            password = signup_form.password1.data

            # 把手机号，用户名，密码保存到mysql数据库里面
            user = FrontUser(telephone=telephone, username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message=signup_form.get_form_error_message())


# 登录
class SigninView(views.MethodView):
    def get(self):
        return_to = request.referrer
        # 访问当前登录页面是否是通过点击类似a标签这种URL页面跳转过来访问的。如果是，并且这种URL页面是在这个项目里面而不是通过反爬访问
        # 则登录成功通过js来跳转回那个URL页面。如果不是就跳转到fron_home_page。
        if return_to and safe_url.is_safe_url(return_to):
            return render_template('front/front_signin.html', return_to=return_to)
        else:
            return render_template('front/front_signin.html')

    def post(self):
        signin_form = SignInForm(request.form)
        if signin_form.validate():
            telephone = signin_form.telephone.data
            password = signin_form.password.data
            remember = signin_form.remember.data
            user = FrontUser.query.filter_by(telephone=telephone).first()
            if user and user.check_password(password):
                session['user_id'] = user.id
                if remember:
                    session.permanent = True
                return restful.success()
            else:
                return restful.params_errors(message='手机号或者密码输入错误')

        else:
            return restful.params_errors(message=signin_form.get_form_error_message())


front_bp.add_url_rule('/graph_captcha/', endpoint='graph_captcha', view_func=graph_captcha)
front_bp.add_url_rule('/front_home_page/', endpoint='front_home_page', view_func=front_home_page)
front_bp.add_url_rule("/signup/", view_func=SignupView.as_view('signup'))
front_bp.add_url_rule("/signin/", view_func=SigninView.as_view('signin'))
