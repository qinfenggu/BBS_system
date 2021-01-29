from flask import Blueprint, views, render_template, Response, request, session, g, redirect, url_for
from flask_paginate import Pagination, get_page_parameter
from utils.image_captcha.image_captcha import Captcha
from utils import redis_save_capthcha, restful, safe_url
from io import BytesIO
from .forms import SignUpForm, SignInForm, ReleasePostsForm, AddCommentForm, FontResetPwdForm, FrontResetTelephoneForm, \
                                FindPasswordForm
from .models import FrontUser, PostsModel, CommentModel
from apps.cms.models import BannerModel, BoardModel, EssencePostsModel
from .decorators import front_signin_required
import config
from excit import db
from sqlalchemy.sql import func

front_bp = Blueprint("front", __name__)


# 让访问下面的所有URL视图之前进行判断是否 session存在'front_user_id' 即有没有登录。如果登录，主页那边会多显示出用户名这一块。没登录不显示
@front_bp.before_request
def before_request():
    if 'front_user_id' in session:
        user_id = session.get('front_user_id')
        user = FrontUser.query.get(user_id)
        if user:
            g.front_user = user


# 主页
def front_home_page():
    # 往前台显示存储在mysql数据库里面的轮播图
    banners = BannerModel.query.filter(BannerModel.is_delete == 1).order_by(BannerModel.priority).all()
    boards = BoardModel.query.filter(BoardModel.is_delete == 1).order_by(BoardModel.id).all()
    # 前端<a href=" class="list-group-item active">Python</a>。带有active，Python会变蓝色填充。
    # 当点击Python时，会触发/front_home_page/? board_id=board.id这个url即重新映射这个HTML，
    # 而使current_board_id却有了值board.id，Python选择了带active属性的a标签。Python被蓝色填充
    # 不点posts,自然就是默认default=None。
    current_board_id = request.args.get('board_id', type=int, default=None)
    # 获取搜索框内容
    search = request.args.get('search', type=str, default='')
    # 如果点击'最新','精华帖子'，都会重定向/front_home_page/?current_choose=数字,有了数字则可判断'最新','精华帖子'
    # 这些哪个需要深灰色填充。default=1。进入主页，默认'最新'被深灰色填充
    current_choose = request.args.get('current_choose', type=int, default=1)

    # 当前的页码。就是在前台鼠标点击第几页，这边会获取到那个数字。default=1默认当前分页导航框页是1
    page = request.args.get(get_page_parameter(), type=int, default=1)
    # config.PER_PAGE是10。看配置文件
    start_page = (page - 1) * config.PER_PAGE
    end_page = start_page + config.PER_PAGE
    if current_choose == 1:
        # 最新。desc()从高到低排序。把所有is_delete=1的数据按create_time从高到低排序。
        old_posts = PostsModel.query.filter_by(is_delete=1).order_by(PostsModel.create_time.desc()).filter(PostsModel.title.like('%'+search+'%'))
    elif current_choose == 2:
        # 精华帖子。内连接
        old_posts = db.session.query(PostsModel).join(EssencePostsModel).order_by(EssencePostsModel.create_time.desc()).filter(PostsModel.title.like('%'+search+'%'))
    elif current_choose == 3:
        # 点赞最多
        old_posts = PostsModel.query.filter_by(is_delete=1).order_by(PostsModel.create_time.desc()).filter(PostsModel.title.like('%'+search+'%'))
    elif current_choose == 4:
        # 评论最多
        old_posts = db.session.query(PostsModel).join(CommentModel).group_by(PostsModel.id).order_by(func.count(CommentModel.id).desc()).filter(PostsModel.title.like('%'+search+'%'))
    else:
        old_posts = PostsModel.query.filter_by(is_delete=1).filter(PostsModel.title.like('%'+search+'%'))

    if current_board_id:
        # 有点击'具体某个board'就从第start_page+1条开始，显示这个所属这个board的end_page - start_page=config.PER_PAGE即10条帖子
        posts = old_posts.filter(PostsModel.board_id == current_board_id).slice(start_page, end_page)
        # total一共有多少条。如果不切片处理
        total = old_posts.filter(PostsModel.board_id == current_board_id).count()
    else:
        # 没有点击'具体某个board'就从第start_page+1条开始，按顺序开始显示10条帖子
        posts = old_posts.slice(start_page, end_page)
        total = old_posts.count()
    # bs_version=3指定bootstrap版本为3，原因：不指定分页导航框样式很丑。page=数字当前第几页；total=数字 总共多少条数据；
    # per_page=数字，每页显示多少条；inner_window=数字n。当前分页导航框页左右显示n个。 outer_window=0分页导航框页最左右显示一个
    pagination = Pagination(bs_version=3, page=page, total=total, per_page=config.PER_PAGE, inner_window=1, outer_window=0)

    context = {
        'banners': banners,
        'boards': boards,
        'current_board_id': current_board_id,
        'posts': posts,
        'pagination': pagination,
        'current_choose': current_choose
    }
    return render_template('front/front_home_page.html', **context)


# 帖子详情页面
def posts_detail(posts_id):
    posts = PostsModel.query.get(posts_id)
    if posts:
        # 每访问一次这个read_count字段数据就加1
        posts.read_count += 1
        db.session.commit()
        return render_template('front/front_posts_detail.html', posts=posts)
    else:
        return restful.params_errors(message='帖子不存在')


# 个人中心
def front_profile():
    return render_template('front/front_profile.html')


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


# 注销。跳转回主页
def front_logout_view():
    session.pop('front_user_id')
    return redirect(url_for('front.front_home_page'))


# 发表评论
@front_bp.route('/add_comment/', methods=['POST'])
def add_comment():
    add_comment_form = AddCommentForm(request.form)
    if add_comment_form.validate():
        posts_id = add_comment_form.posts_id.data
        content = add_comment_form.content.data
        posts = PostsModel.query.get(posts_id)
        if posts:
            comment = CommentModel(content=content)
            comment.posts = posts
            comment.author = g.front_user
            db.session.add(comment)
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='没有这篇帖子')
    else:
        return restful.params_errors(message=add_comment_form.get_form_error_message())


# 注册
class SignupView(views.MethodView):
    def get(self):
        return_to = request.referrer
        # 访问当前注册页面如果是通过点击类似a标签这种URL页面跳转过来访问的，并且这种URL页面是在这个项目里面而不是通过反爬访问
        # 或自己的那个注册URL访问自己，则注册成功跳转回那个URL页面。如果不是就跳转到fron_home_page。
        if return_to and return_to != request.url and safe_url.is_safe_url(return_to):
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
            # 这里注册成功为什么不写重定向：在js的ajax里面已经写了，注册成功会跳转到主页或者来到这个注册页面的上一个URL页面
            return restful.success()
        else:
            return restful.params_errors(message=signup_form.get_form_error_message())


# 登录
class SigninView(views.MethodView):
    def get(self):
        return_to = request.referrer
        # 访问当前登录页面如果是通过点击类似a标签这种URL页面跳转过来访问的，并且这种URL页面是在这个项目里面而不是通过反爬访问
        # 或自己的那个登录URL访问自己， 则登录成功跳转回那个URL页面。如果不是就跳转到fron_home_page。
        if return_to and return_to != request.url and safe_url.is_safe_url(return_to):
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
            # 判断前台传过来的用户名和密码是否与数据库一致
            if user and user.check_password(password):
                session['front_user_id'] = user.id
                if remember:
                    session.permanent = True
                # 这里登录成功为什么不写重定向：在js的ajax里面已经写了，登录成功会跳转到主页或者来到这个注册页面的上一个URL页面
                return restful.success()
            else:
                return restful.params_errors(message='手机号或者密码输入错误')

        else:
            return restful.params_errors(message=signin_form.get_form_error_message())


# 帖子
class PostsView(views.MethodView):
    # 判断目前这个session里面是否含有front_user_id即有没有登录
    decorators = [front_signin_required]

    def get(self):
        boards = BoardModel.query.filter(BoardModel.is_delete == 1).order_by(BoardModel.id).all()
        return render_template('front/front_posts.html', boards=boards)

    # 点击'发帖子'，就会通过触发js的ajax触发这个post请求。把发布的帖子内容保存到数据里面
    def post(self):
        release_posts_form = ReleasePostsForm(request.form)
        if release_posts_form.validate():
            tilte = release_posts_form.title.data
            board_id = release_posts_form.board_id.data
            content = release_posts_form.content.data
            board = BoardModel.query.get(board_id)
            if board:
                posts = PostsModel(title=tilte, content=content)
                posts.board = board
                posts.author = g.front_user
                db.session.add(posts)
                db.session.commit()
                # return redirect(url_for('front.front_home_page'))
                return restful.success()
            else:
                return restful.params_errors(message='没有这个板块')
        else:
            return restful.params_errors(message=release_posts_form.get_form_error_message())


# 修改密码
class FontResetPwdView(views.MethodView):
    def get(self):
        return render_template('front/front_resetpwd.html')

    def post(self):
        front_reset_form = FontResetPwdForm(request.form)
        if front_reset_form.validate():
            oldpwd = front_reset_form.oldpwd.data
            newpwd = front_reset_form.newpwd.data
            # g.user就是 FrontUser.query.get(user_id)
            user = g.front_user
            if user.check_password(oldpwd):
                # user.password = newpwd其实是调用了models.py里面CMSUser类下的@password.setter方法
                user.password = newpwd
                db.session.commit()
                return restful.success()
            else:
                return restful.params_errors(message='旧密码输入不正确，请重新输入')
        else:
            return restful.params_errors(message=front_reset_form.get_form_error_message())


# 更换手机号
class FrontResetTelephoneView(views.MethodView):
    def get(self):
        return render_template('front/front_reset_telephone.html')

    def post(self):
        front_reset_telephonr_form = FrontResetTelephoneForm(request.form)
        if front_reset_telephonr_form.validate():
            telephone = front_reset_telephonr_form.telephone.data
            # user就是 CMSUser.query.get(user_id)
            user = g.front_user
            user.telephone = telephone
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message=front_reset_telephonr_form.get_form_error_message())


# 找回密码
class FindPasswordView(views.MethodView):
    def get(self):
        return render_template('front/find_password.html')

    def post(self):
        find_password_form = FindPasswordForm(request.form)
        if find_password_form.validate():
            telephone = find_password_form.telephone.data
            newpwd = find_password_form.newpwd.data
            user = FrontUser.query.filter_by(telephone=telephone).first()
            # 判断前台传过来的用户名是否与数据库一致
            if user:
                user.password = newpwd
                db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message=find_password_form.get_form_error_message())


front_bp.add_url_rule('/graph_captcha/', endpoint='graph_captcha', view_func=graph_captcha)
front_bp.add_url_rule('/front_home_page/', endpoint='front_home_page', view_func=front_home_page)
front_bp.add_url_rule('/front_logout/', endpoint='front_logout', view_func=front_logout_view)
front_bp.add_url_rule('/posts_detail/<posts_id>/', endpoint='posts_detail', view_func=posts_detail)
front_bp.add_url_rule('/front_profile/', endpoint='front_profile', view_func=front_profile)

front_bp.add_url_rule("/signup/", view_func=SignupView.as_view('signup'))
front_bp.add_url_rule("/signin/", view_func=SigninView.as_view('signin'))
front_bp.add_url_rule("/posts/", view_func=PostsView.as_view('posts'))
front_bp.add_url_rule("/FontResetPwd/", view_func=FontResetPwdView.as_view('FontResetPwd'))
front_bp.add_url_rule("/FrontResetTelephone/", view_func=FrontResetTelephoneView.as_view('FrontResetTelephone'))
front_bp.add_url_rule("/FindPassword/", view_func=FindPasswordView.as_view('FindPassword'))
