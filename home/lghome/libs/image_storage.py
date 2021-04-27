# @ Time    : 2020/11/27 21:37
# @ Author  : JuRan

from qiniu import Auth, put_file, etag, put_data
import qiniu.config

# 需要填写你的 Access Key 和 Secret Key
access_key = 'Y7xiVS2YBV_XaDjrOoa4gjhqAT_c1X3f_wu6O-KW'
secret_key = '9lxlwgCcG8-b-_GmWogpVKNALvSoAsr1d_qfNF3M'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'lghome'
    # 上传后保存的文件名
    # key = 'my-python-logo.png'
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)

    # ret得到的数据是{'has':'上传图片名字hash加密字符', 'key':'如果没写key默认就是上传图片名字hash加密字符。有写key那就是key的值'}
    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        return ret.get('key')
    else:
        raise Exception('上传图片失败')


