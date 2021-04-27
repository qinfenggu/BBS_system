# @ Time    : 2020/7/30 21:49
# @ Author  : JuRan

from celery import Celery
import os

# celery的入口
if not os.getenv('DJANGO_SETTINGS_MODULE'):
    os.environ['DJANGO_SETTINGS_MODULE'] = 'lgshop.dev'

# 创建celery实例。lg意思：是给这个celery取名叫lg
celery_app = Celery('lg')

# 加载配置文件
celery_app.config_from_object('celery_tasks.config')

# 注册任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])

"""
Linux运行
celery -A celery_tasks.main worker -l info
• -A指对应的应用程序, 其参数是项目中 Celery实例的位置。
• worker指这里要启动的worker。
• -l指日志等级，比如info等级。

Windows运行
celery -A celery_tasks.main worker -l info --pool=solo
"""

