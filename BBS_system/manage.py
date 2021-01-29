from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from bbs import app
from excit import db
from apps.cms.models import CMSUser, CMSRole, CMSPersmission, BannerModel, BoardModel, EssencePostsModel
from apps.front.models import FrontUser, PostsModel, CommentModel


manager = Manager(app)
# manage和bbs和models进行关联
Migrate(app, db)
manager.add_command('db', MigrateCommand)


# 添加后台管理员账号
@manager.option('-u', '--username', dest='username')
@manager.option('-p', '--password', dest='password')
@manager.option('-e', '--email', dest='email')
def create_cms_user(username, password, email):
    # 调用CMSUser类，并给init方法里面属性赋值
    user = CMSUser(username=username, password=password, email=email)
    db.session.add(user)
    db.session.commit()


# 添加角色
@manager.command
def create_role():
    # 访问者
    visitor = CMSRole(name='访问者', describe='只可访问，无法修改任何数据', permissions=CMSPersmission.VISITOR)
    # 运营人员
    operator = CMSRole(name='运营人员', describe='访问，帖子，评论，前台用户管理',
                      permissions=CMSPersmission.VISITOR | CMSPersmission.POSTER | CMSPersmission.COMMENTER
                                  | CMSPersmission.FRONTUSER)
    # 管理员
    admin = CMSRole(name='管理员', describe='访问，帖子，评论，板块，前台用户管理',
                      permissions=CMSPersmission.VISITOR | CMSPersmission.POSTER | CMSPersmission.COMMENTER
                                  | CMSPersmission.BOARDER | CMSPersmission.FRONTUSER)
    # 开发者
    developer = CMSRole(name='开发者', describe='所以权限', permissions=CMSPersmission.ALL_PERMISSION)

    db.session.add_all([visitor, operator, admin, developer])
    db.session.commit()


# 用户绑定角色
@manager.option('-e', '--email', dest='email')
@manager.option('-u', '--username', dest='username')
def add_user_to_role(email, username):
    user = CMSUser.query.filter_by(email=email).first()
    if user:
        role = CMSRole.query.filter_by(name=username).first()
        if role:
            role.users.append(user)
            db.session.commit()
            print('{}用户与{}角色绑定成功'.format(email, username))
        else:
            print('{}角色不存在！'.format(role))
    else:
        print('{}用户不存在！'.format(email))




if __name__ == '__main__':
    manager.run()


