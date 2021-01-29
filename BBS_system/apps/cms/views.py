from flask import Blueprint, render_template, views, request, redirect, url_for, session, g, jsonify
from apps.cms.forms import LoginForm, ResetPwdForm, ResetEmailForm, AddBannerForm, UpdateBannerForm, AddBoardForm, \
                           UpdateBoardForm
from apps.cms.models import CMSUser, CMSPersmission, BannerModel, BoardModel, EssencePostsModel
from apps.cms.decorators import permission_required
from excit import db, mail
from utils import restful, random_captcha, redis_save_capthcha
from flask_mail import Message
from apps.front.models import PostsModel, CommentModel
from tasks import send_mail

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
    session.pop('user_id')
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
            # send_mail('【轻风言论坛】修改邮箱', recipients=[email], body='您的验证码是 %s' % capthcha)
            mail.send(message)
        except:
            return restful.server_errors()
        # 把验证码保持到redis数据库里面
        redis_save_capthcha.redis_set(key=email, value=capthcha)
        return restful.success()


# 帖子管理。@permission_required装饰器是在执行cms_posts_view之前进行判断当前用户是否拥有帖子权限
@permission_required(CMSPersmission.POSTER)
def cms_posts_view():
    posts = PostsModel.query.filter(PostsModel.is_delete == 1).order_by(PostsModel.id).all()
    return render_template('cms/cms_posts.html', posts=posts)


# 加精。点击一个帖子'加精'，根据<tr data-id="{{ post.id }}" data-highlight="{{ 1 if post.essence_posts else 0 }}">得data-highlight为0
# js的ajax会根据data-highlight为0选择post请求/become_essence_posts/并在鼠标选中这帖子时标签里data-id="{{ post.id }}属性便得选中帖子的id
@cms_bp.route('/become_essence_posts/', methods=['POST'])
def become_essence_posts_view():
    posts_id = request.form.get('post_id')
    if posts_id:
        posts = PostsModel.query.get(posts_id)
        if posts:
            #  essence_posts = EssencePostsModel(字段=值)原因，没有字段需要设置值呀，id和create_time都会自己添加
            essence_posts = EssencePostsModel()
            essence_posts.posts = posts
            db.session.add(essence_posts)
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='没有这篇帖子')
    else:
        return restful.params_errors(message='请传入帖子ID')


# 取消加精。点击一个帖子'取消加精'，根据data-highlight="{{ 1 if post.essence_posts else 0 }}得data-highlight为1
# js的ajax会data-highlight为0选择根据post请求这个/unbecome_essence_posts/并根据你鼠标选中这个帖子时标签里面自动添加属性post_id==posts.id
# 得到post的id来进行删除essence_posts表对应数据
@cms_bp.route("/unbecome_essence_posts/", methods=["POST"])
def unbecome_essence_posts_view():
    posts_id = request.form.get("post_id")
    if posts_id:
        posts = PostsModel.query.get(posts_id)
        if posts:
            essence_posts = EssencePostsModel.query.filter_by(posts_id=posts_id).first()
            db.session.delete(essence_posts)
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='没有这篇帖子')
    else:
        return restful.params_errors(message="请传入帖子id")


# 你鼠标选中这个帖子时标签里面自动添加属性post_id==posts.id
@cms_bp.route('/delete_essence_posts/', methods=['POST'])
def delete_essence_posts():
    posts_id = request.form.get("post_id")
    if posts_id:
        posts = PostsModel.query.get(posts_id)
        if posts:
            posts.is_delete = 0
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='没有这篇帖子')
    else:
        return restful.params_errors(message='请输入帖子ID')


# 评论管理
@permission_required(CMSPersmission.COMMENTER)
def cms_comments_view():
    comment = CommentModel.query.filter(CommentModel.is_delete == 1).order_by(CommentModel.id).all()
    return render_template('cms/cms_comment.html', comment=comment)


# 删除评论
@cms_bp.route("/delete_comment/", methods=['POST'])
def delete_comment():
    comment_id = request.form.get('comment_id')

    if not comment_id:
        return restful.params_errors(message='评论ID不存在')

    comment = CommentModel.query.get(comment_id)

    if not comment:
        return restful.params_errors(message='评论不存在')

    comment.is_delete = 0
    db.session.commit()
    return restful.success()


# 板块管理
@permission_required(CMSPersmission.BOARDER)
def cms_boards_view():
    boards = BoardModel.query.filter(BoardModel.is_delete == 1).order_by(BoardModel.id).all()
    return render_template('cms/cms_boards.html', boards=boards)


# 添加新板块。点击'添加新板块'，填写完点'确定'，会通过js的ajax的post请求就会访问这个/add_board/。
@cms_bp.route("/add_board/", methods=['POST'])
def add_board():
    add_board_form = AddBoardForm(request.form)
    if add_board_form.validate():
        name = add_board_form.name.data
        board = BoardModel(name=name)
        db.session.add(board)
        db.session.commit()
        return restful.success()
    else:
        return restful.params_errors(message=add_board_form.get_form_error_message())


# 编辑板块。点击'编辑'，里面会多一个placeholer属性。判断得知是'编辑'。填写完点'确定',会通过js的ajax的post请求就会访问这个/add_board/。
@cms_bp.route("/update_board/", methods=['POST'])
def update_board():
    update_board_form = UpdateBoardForm(request.form)
    if update_board_form.validate():
        board_id = update_board_form.board_id.data
        name = update_board_form.name.data

        board = BoardModel.query.get(board_id)
        if board:
            board.name = name
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='没有这个板块名称')
    else:
        return restful.params_errors(message=update_board_form.get_form_error_message())


# 删除板块。点击'删除'，会通过js的ajax的post请求就会访问这个/delete_board/。
@cms_bp.route("/delete_board/", methods=['POST'])
def delete_board():
    board_id = request.form.get('board_id')

    if not board_id:
        return restful.params_errors(message='板块名称不存在')

    board = BoardModel.query.get(board_id)

    if not board:
        return restful.params_errors(message='板块名称不存在')

    board.is_delete = 0
    db.session.commit()
    return restful.success()


# 前台用户管理
@permission_required(CMSPersmission.FRONTUSER)
def cms_frontuser_manage_view():
    return '前台用户'


# 后台用户管理
@permission_required(CMSPersmission.CMSUSER)
def cms_cmsuser_manage_view():
    return '后台用户'


# 角色管理
def cms_roles_view():
    return '角色'


# 轮播图管理
def cms_banners_view():
    # 按把数据库轮播图表里面所有的数据给取出来，按优先级priority这个字段排序
    banners = BannerModel.query.order_by(BannerModel.priority).all()
    return render_template('cms/cms_banners.html', banners=banners)


# 添加轮播图。在前端点击'保存'，会进行判断有无data-type == 'update'属性，如果没有通过js的ajax的post请求就会访问这个/add_banner/。
@cms_bp.route('/add_banner/', methods=['POST'])
def add_banner():
    add_banner_form = AddBannerForm(request.form)
    if add_banner_form.validate():
        name = add_banner_form.name.data
        image_url = add_banner_form.image_url.data
        link_url = add_banner_form.link_url.data
        priority = add_banner_form.priority.data

        banner = BannerModel(name=name, image_url=image_url, link_url=link_url, priority=priority)
        db.session.add(banner)
        db.session.commit()
        return restful.success()
    else:
        return restful.params_errors(message=add_banner_form.get_form_error_message())


# 修改轮播图。点击'编辑'，再点击'保存'，会进行判断有无data-type == 'update'属性，如果有证明是'编辑'不是'添加轮播图'，
# 然后会通过js的ajax的post请求就会访问这个/update_banner/。可通过data-id=数字从数据库查找轮播图信息。
@cms_bp.route("/update_banner/", methods=['POST'])
def update_banner():
    # 修改  banner_id
    updata_banner_form = UpdateBannerForm(request.form)
    if updata_banner_form.validate():
        banner_id = updata_banner_form .banner_id.data
        name = updata_banner_form .name.data
        image_url = updata_banner_form .image_url.data
        link_url = updata_banner_form .link_url.data
        priority = updata_banner_form .priority.data
        banner = BannerModel.query.get(banner_id)
        if banner:
            banner.name = name
            banner.image_url = image_url
            banner.link_url = link_url
            banner.priority = priority
            db.session.commit()
            return restful.success()
        else:
            return restful.params_errors(message='轮播图不存在')
    else:
        return restful.params_errors(message=updata_banner_form.get_form_error_message())


# 删除轮播图。点击'删除'，通过js的ajax的post请求就会访问这个/delete_banner/
@cms_bp.route('/delete_banner/', methods=['POST'])
def delete_banner():
    # post方式
    banner_id = request.form.get('banner_id')
    if not banner_id:
        return restful.params_errors(message='轮播图不存在')

    banner = BannerModel.query.get(banner_id)
    if banner:
        banner.is_delete = 0
        db.session.commit()
        return restful.success()
    else:
        return restful.params_errors('轮播图不存在')


cms_bp.add_url_rule('/home_page/', endpoint='home_page', view_func=cms_home_page)
cms_bp.add_url_rule('/logout/', endpoint='logout', view_func=cms_logout_view)
cms_bp.add_url_rule('/profile/', endpoint='profile', view_func=cms_profile_view)
cms_bp.add_url_rule('/posts/', endpoint='posts', view_func=cms_posts_view)
cms_bp.add_url_rule('/comments/', endpoint='comments', view_func=cms_comments_view)
cms_bp.add_url_rule('/boards/', endpoint='boards', view_func=cms_boards_view)
cms_bp.add_url_rule('/frontuser_manage/', endpoint='frontuser_manage', view_func=cms_frontuser_manage_view)
cms_bp.add_url_rule('/cmsuser_manage/', endpoint='cmsuser_manage', view_func=cms_cmsuser_manage_view)
cms_bp.add_url_rule('/roles/', endpoint='roles', view_func=cms_roles_view)
cms_bp.add_url_rule('/banners/', endpoint='banners', view_func=cms_banners_view)


cms_bp.add_url_rule('/login/', view_func=CMSLoginView.as_view('login'))
cms_bp.add_url_rule('/resetpwd/', view_func=ResetPwdView.as_view('resetpwd'))
cms_bp.add_url_rule('/resetemail/', view_func=ResetMailView.as_view('resetemail'))
cms_bp.add_url_rule('/email_captcha/', view_func=EmailCaptchaView.as_view('email_captcha'))
