# @ Time    : 2020/5/22 21:22
# @ Author  : JuRan

from urllib.parse import urlparse, urljoin
from flask import request


# 如果访问注册页面是从其他URL跳转过来的，则判断这个URL是否在这个项目里面还是通过反爬访问的。为了防止注册成功，跳转的是你第三方的页面
def is_safe_url(target):

    ref_url = urlparse(request.host_url)

    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

