# encoding:utf-8
from app import app
from qiniu import Auth, put_data

access_key = app.config['QINIU_ACCESS_KEY']
secret_key = app.config['QINIU_SECRET_KEY']
q = Auth(access_key, secret_key)
domain_prefix =app.config['QINIU_DOMAIN']

bucket_name = 'images'
# 上传到七牛后保存的文件名
# key = 'flask_demo.jpg';
# 生成上传 Token，可以指定过期时间等
# token = q.upload_token(bucket_name, key, 3600)

# 要上传文件的本地路径
# localfile = 'D://upload/2c8df230072311e88dd9f079591b5a8e.jpg'
# ret, info = put_file(token, key, localfile)
# print(info)
# assert ret['key'] == key
# assert ret['hash'] == etag(localfile)


def qiniu_upload_file(source_file, save_file_name):
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, save_file_name)

    ret, info = put_data(token, save_file_name, source_file.stream)
    print type(info.status_code), info
    if info.status_code == 200:
        return domain_prefix + save_file_name
    return None



