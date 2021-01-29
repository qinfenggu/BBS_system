from flask import Flask
from excit import db, mail
from apps.cms.views import cms_bp
from apps.front.views import front_bp
from apps.common.views import common_bp
import config
from flask_wtf import CSRFProtect


app = Flask(__name__)
# CSRF页面保护：让请求更加安全
CSRFProtect(app)
# 加载配置文件
app.config.from_object(config)
# excit和bbs关联即注册db
db.init_app(app)
mail.init_app(app)
# 蓝图注册
app.register_blueprint(cms_bp)
app.register_blueprint(front_bp)
app.register_blueprint(common_bp)


if __name__ == '__main__':
    app.run(port=8000)