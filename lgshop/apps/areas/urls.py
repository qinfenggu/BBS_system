# @ Time    : 2021/2/3 20:35
# @ Author  : JuRan
from django.urls import path, re_path
from . import views


urlpatterns = [
    # 省市区三级联动
    path('areas/', views.AreasView.as_view()),
]