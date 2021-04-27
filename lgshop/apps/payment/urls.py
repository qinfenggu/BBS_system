# @ Time    : 2020/9/8 21:47
# @ Author  : JuRan

from django.urls import path, re_path
from . import views


urlpatterns = [
    re_path(r'payment/(?P<order_id>\d+)/', views.PaymentView.as_view()),
]