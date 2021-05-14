from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from excit import db
import enum
import shortuuid
from markdown import markdown
import bleach


class GenderEnum(enum.Enum):
    MALE = 1
    FEMALE = 2
    UNKNOW = 3


# 前台用户
class FrontUser(db.Model):
    __tablename__ = 'front_user'
    # 为了安全，id就不按数字了，而且 shortuuid.uuid生成16位唯一随机字符串
    id = db.Column(db.String(100), primary_key=True, default=shortuuid.uuid)
    telephone = db.Column(db.String(11), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False)
    _password = db.Column(db.String(100), nullable=False)
    # head_portrait头像，signature个性签名
    head_portrait = db.Column(db.String(100))
    # signature = db.Column(db.String(100), default="此人很懒什么也没有留下.....")

    create_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, *args, **kwargs):
        if "password" in kwargs:
            # 会调用@password.setter下方法，self.password原是个方法，后为属性，属性值self._password。@password.setter
            self.password = kwargs.get('password')
            kwargs.pop('password')


        # super(FrontUser, self).__init__(*args, **kwargs) 这是python2写法。
        # 在模型里面，可以把上面的静态属性按这样子定义，静态属性值都是Noen。而类名（类属性名=值），就是给它们赋值。
        # 类名（静态属性名=值）这种在Python语法里面是不成立的。但是这个用在模型里面成立
        super().__init__(*args, **kwargs)

    @property
    def password(self):
        return self._password

    # 添加前台用户时对传过来的密码即raw_password进行加密
    @password.setter
    def password(self, raw_password):
        self._password = generate_password_hash(raw_password)

    # 验证前端form表单传过来的密码是否和数据库里面的一致
    def check_password(self, passe_password):
        result = check_password_hash(self.password, passe_password)
        return result


# 帖子。发布帖子那个Editor编辑器的内容，
class PostsModel(db.Model):
    __tablename__ = 'front_posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # 保存HTNL
    content_html = db.Column(db.Text)
    # 访问量
    read_count = db.Column(db.Integer, default=0)
    like_count = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.now)
    # 属于哪个模块
    board_id = db.Column(db.Integer, db.ForeignKey("cms_board.id"))
    # 属于哪个前台用户
    author_id = db.Column(db.String(100), db.ForeignKey("front_user.id"))

    board = db.relationship("BoardModel", backref="posts")
    author = db.relationship("FrontUser", backref="posts")
    is_delete = db.Column(db.Integer, default=0)

    # 因为前端那边保存上来的是一个TTXT文本，不是HTML格式。下面这个方法是对保存上来的文本进行HTML格式处理,保存成markdown格式
    @staticmethod
    def on_changed_content(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p', 'img', 'video', 'div', 'iframe', 'p', 'br', 'span', 'hr', 'src', 'class'
                        'span', 'pre']
        allowed_attrs = {'*': ['class'],
                         'a': ['href', 'rel'],
                         'img': ['src', 'alt'],
                         'spna': ['class'],
                         'ol': ['class'],
                         'li': ['class'],
                         'pre': ['class'],
                         'div': ['class']
                         }
        target.content_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True, attributes=allowed_attrs))
        print('target.content_html:', target.content_html)


# 这个其实算是调用上面的on_changed_content
db.event.listen(PostsModel.content, 'set', PostsModel.on_changed_content)


# 评论
class CommentModel(db.Model):
    __tablename__ = 'front_comment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # content是评论语
    content = db.Column(db.Text, nullable=False)
    # 属于哪个前台用户
    author_id = db.Column(db.String(100), db.ForeignKey("front_user.id"))
    posts_id = db.Column(db.Integer, db.ForeignKey("front_posts.id"))
    create_time = db.Column(db.DateTime, default=datetime.now)
    is_delete = db.Column(db.Integer, default=0)

    author = db.relationship("FrontUser", backref="comment")
    posts = db.relationship("PostsModel", backref="comment")



