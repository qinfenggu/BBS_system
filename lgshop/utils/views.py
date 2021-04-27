# @ Time    : 2021/2/5 20:42
# @ Author  : JuRan
from django.contrib.auth.mixins import LoginRequiredMixin
from django import http
from utils.response_code import RETCODE


# class LoginRequiredJSONMixin(LoginRequiredMixin):
#     """自定义判断用户是否登录的扩展类:返回JSON"""
#     def handle_no_permission(self):
#         """直接响应JSON数据"""
#         return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登陆'})

class LoginRequiredJsonMinin(LoginRequiredMixin):

    def handle_no_permission(self):
        """返回JSON数据"""
        return http.JsonResponse({"code": RETCODE.SESSIONERR, 'errmsg': "用户未登陆"})