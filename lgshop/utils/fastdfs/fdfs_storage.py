# @ Time    : 2021/3/22 20:43
# @ Author  : JuRan
from django.core.files.storage import Storage
from django.conf import settings


class FastDFSStorage(Storage):
    """自定义文件存储类"""

    def __init__(self, fdfs_base_url=None):
        # if not fdfs_base_url:
        #     self.fdfs_base_url = settings.FDFS_BASE_URL
        # else:
        # self.fdfs_base_url = fdfs_base_url
        self.fdfs_base_url = fdfs_base_url or settings.FDFS_BASE_URL

    def _open(self, name, mode='rb'):
        pass

    def _save(self, name, content):
        pass

    def url(self, name):
        """
        返回文件的全路径
        :param name: 文件路径
        :return: ip+port+文件路径
        """
        return self.fdfs_base_url + name

