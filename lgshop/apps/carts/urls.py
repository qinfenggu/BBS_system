# @ Time    : 2021/1/20 21:57
# @ Author  : JuRan
from django.urls import path, re_path

from . import views

app_name = 'carts'

urlpatterns = [
    # 购物车
    path('carts/', views.CartsView.as_view(), name='info'),
    # 购物车的全选
    path('carts/selection/', views.CartsSelectAllView.as_view()),
]