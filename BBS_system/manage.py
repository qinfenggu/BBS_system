from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from bbs import app
from excit import db
from apps.cms.models import CMSUser


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


if __name__ == '__main__':
    manager.run()


