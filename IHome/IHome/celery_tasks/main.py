import os


# 配置环境
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "IHome.settings.dev")
# 导入 Celery 类
from celery import Celery


# 创建 celery 实例
celery_app = Celery('IHome')


# 指定配置
celery_app.config_from_object('celery_tasks.config')


# 自动捕获目标地址下的任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])
