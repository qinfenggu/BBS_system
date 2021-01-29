from excit import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


# 用二进制来表示不同的权限，二进制里面1在哪个位置表示能这个位置是拥有哪种权限
class CMSPersmission(object):
    # 255二进制来表示所有的权限
    ALL_PERMISSION  = 0b11111111

    # 访问权限
    VISITOR         = 0b00000001

    # 帖子管理权限
    POSTER          = 0b00000010

    # 评论管理权限
    COMMENTER       = 0b00000100

    # 板块管理权限
    BOARDER         = 0b00001000

    # 前台用户管理权限
    FRONTUSER       = 0b00010000

    # 后台用户管理权限
    CMSUSER         = 0b00100000

    # 管理管理员用户权限
    ADMINER         = 0b01000000


cms_role_user = db.Table(
    'cms_role_user',
    db.Column('cms_role_id', db.Integer, db.ForeignKey('cms_role.id'), primary_key=True),
    db.Column('cms_user_id', db.Integer, db.ForeignKey('cms_user.id'), primary_key=True),
)


# CMS后台用户
class CMSUser(db.Model):
    __tablename__ = 'cms_user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    _password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    create_time = db.Column(db.DateTime, default=datetime.now())

    def __init__(self, username, password, email):
        self.username = username
        # 会调用@password.setter下方法，self.password原是个方法，后为属性，属性值self._password
        self.password = password
        self.email = email

    @property
    def password(self):
        return self._password

    # # 添加后台用户时对传过来的密码即raw_password进行加密
    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    # 验证前端form表单传过来的密码是否和数据库里面的一致
    def check_password(self, passe_password):
        result = check_password_hash(self.password, passe_password)
        return result

    # 取当前用户拥有的权限：把当前用户拥有的那些角色里面的权限全部都给|起来可得
    @property
    def permissions(self):
        if not self.roles:
            return 0
        has_all_permissions = 0
        # for循环原因：当前用户可能有多个角色
        for role in self.roles:
            permissions = role.permissions
            #  all_permissions = all_permissions | permissions
            has_all_permissions |= permissions
        return has_all_permissions

    # 判断当前用户是否拥有need_if_permissions这个权限
    def has_permissions(self, need_if_permissions):
        has_all_permissions = self.permissions
        # 如果has_all_permissions 含 permissions。则has_all_permissions & permissions得到permissions。
        result = has_all_permissions & need_if_permissions == need_if_permissions
        return result

    # 判断当前用户是否是开发者（即是否含有全部权限）
    @property
    def is_developer(self):
        return self.has_permissions(CMSPersmission.ALL_PERMISSION)


# 角色
class CMSRole(db.Model):
    __tablename__ = 'cms_role'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    describe = db.Column(db.String(200), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    permissions = db.Column(db.Integer, default=CMSPersmission.VISITOR)

    users = db.relationship('CMSUser', secondary=cms_role_user, backref='roles')


# 轮播图
class BannerModel(db.Model):
    __tablename__ = 'cms_banner'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    # 图片链接。就是这张图片的地址
    image_url = db.Column(db.String(255), nullable=False)
    # 跳转链接。就是点击这张图片会跳转到另一个URL
    link_url = db.Column(db.String(255), nullable=False)
    # 优先级字段。作用就是，前端每添加一条轮播图数据，我就依次增1，作用相当于id了，可以知道哪条先添加，它是第几次添加的
    priority = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.now())
    # 1表示为为删除，0表示已删除
    is_delete = db.Column(db.Integer, default=1)

    def __str__(self):
        return 'name:{}'.format(self.name)


# 板块管理
class BoardModel(db.Model):
    __tablename__ = 'cms_board'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now())
    # 1表示为为删除，0表示已删除
    is_delete = db.Column(db.Integer, default=1)


# 精华帖子。以帖子的id作为外键
class EssencePostsModel(db.Model):
    __tablename__ = 'essence_posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    posts_id = db.Column(db.Integer, db.ForeignKey('front_posts.id'))
    create_time = db.Column(db.DateTime, default=datetime.now())

    posts = db.relationship('PostsModel', backref='essence_posts')


