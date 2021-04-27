# @ Time    : 2021/1/22 22:08
# @ Author  : JuRan
from django.urls import path
from . import views

app_name = 'contents'

urlpatterns = [
    # 注册
    path('', views.IndexView.as_view(), name='index'),
]