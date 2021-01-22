from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail


db = SQLAlchemy()  # 这是生成基类。相当于以前db = declarative_base(engine)
mail = Mail()
