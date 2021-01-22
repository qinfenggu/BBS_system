from flask import Blueprint, views, render_template, Response, request
from utils.image_captcha.image_captcha import Captcha
from utils import redis_save_capthcha, restful
from io import BytesIO
from .forms import SignUpForm
from .models import FrontUser
from excit import db

front_bp = Blueprint("front", __name__)


@front_bp.route('/fron_home_page/')
def index():
    return 'web'

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


front_bp.add_url_rule('/graph_captcha/', endpoint='graph_captcha', view_func=graph_captcha)
front_bp.add_url_rule("/signup/", view_func=SignupView.as_view('signup'))
