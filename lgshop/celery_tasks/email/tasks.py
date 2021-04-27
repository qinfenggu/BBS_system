# 发送邮箱任务
from celery_tasks.main import celery_app
from django.core.mail import send_mail
from django.conf import settings


@celery_app.task(name="send_verify_email")
def send_verify_email(email, verify_url):
    """
    发送邮件的异步任务
    :param email: 发送邮箱
    :param verify_url: 激活链接
    """
    # 发送邮件
    subject = "商城邮箱验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用商城。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接激活您的邮箱：</p>' \
                   '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)

    send_mail(subject, '', from_email=settings.EMAIL_FROM, recipient_list=[email], html_message=html_message)


