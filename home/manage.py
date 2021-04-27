"""这个是开始文件，以前有一个app.py。现在不用它了。直接把这个迁移文件的manage.py当做主文件"""
from lghome import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from lghome import models

# 这个就是开启语句而且还可以得到app，这个语句我确实是想不到
app = create_app('dev')

# 数据库迁移
manage = Manager(app)
Migrate(app, db)
manage.add_command('db', MigrateCommand)


if __name__ == '__main__':
    # 因为这个是manage.py文件还记得?。所以这个就不是app.run()而是manage.run
    manage.run()