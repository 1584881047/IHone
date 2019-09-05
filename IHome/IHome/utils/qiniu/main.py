


# 七牛云
from urllib import parse

import qiniu
from qiniu.compat import BytesIO
from django.conf import settings




# filename: 文件名
def _upload_to_qiniu(upfile, filename):
    """
    上传文件到七牛
    """
    q = qiniu.Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)
    token = q.upload_token(settings.QINIU_BUCKET_NAME)
    buffer = BytesIO()
    for chunk in upfile.chunks():
        buffer.write(chunk)
    buffer.seek(0)
    ret, info = qiniu.put_data(token, filename, buffer.read())
    if info.ok:
        url = parse.urljoin(settings.QINIU_BUCKET_DOMAIN, ret['key'])
        return 'http://'+settings.QINIU_BUCKET_DOMAIN+'/'+url
    else:
        return False
