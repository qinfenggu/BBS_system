from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from bbs import app
from excit import db
from apps.cms.models import CMSUser, CMSRole, CMSPersmission
from apps.front.models import FrontUser, PostsModel, CommentModel


manager = Manager(app)
# manage和bbs和models进行关联
Migrate(app, db)
manager.add_command('db', MigrateCommand)


# 添加后台用户账号。python 映射数据库文件名.py  函数名 -n 参数数据
@manager.option('-u', '--username', dest='username')
@manager.option('-e', '--email', dest='email')
@manager.option('-p', '--password', dest='password')
def create_cms_user(username, email, password):
    # 调用CMSUser类，并给init方法里面属性赋值
    user = CMSUser(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()


# 添加角色。python 映射数据库文件名.py  函数名
@manager.command
def create_role():
    # 访问者
    # visitor = CMSRole(name='访问者', describe='只可访问，无法修改任何数据', permissions=CMSPersmission.VISITOR)
    # 运营人员
    operator = CMSRole(name='运营人员', describe='轮播图',
                      permissions=CMSPersmission.BANNER)
    # 管理员
    admin = CMSRole(name='管理员', describe='轮播图、帖子，板块',
                      permissions=CMSPersmission.BANNER | CMSPersmission.POSTER | CMSPersmission.BOARDER)
    # 超级管理员
    developer = CMSRole(name='超级管理员', describe='轮播图、帖子，板块、后台用户管理', permissions=CMSPersmission.ALL_PERMISSION)

    db.session.add_all([operator, admin, developer])
    db.session.commit()


# 用户绑定角色
@manager.option('-e', '--email', dest='email')
@manager.option('-r', '--role', dest='role')
def add_user_to_role(email, role):
    user = CMSUser.query.filter_by(email=email).first()
    if user:
        role = CMSRole.query.filter_by(name=role).first()
        if role:
            role.users.append(user)
            db.session.commit()
            print('{}用户与{}角色绑定成功'.format(email, role))
        else:
            print('{}角色不存在！'.format(role))
    else:
        print('{}用户不存在！'.format(email))


# 用户绑定角色
if __name__ == '__main__':
    manager.run()

