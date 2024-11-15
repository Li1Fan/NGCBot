# -*- coding: utf-8 -*-
# Author ：梦情
# Time ：2024-09-30 7:44
# File : upload.py
import base64
from datetime import datetime
from io import BytesIO

import requests

# API 端点 URL
api_endpoint = 'http://tc.mqmrx.cn/upload.php'


def upload_img(base64_data):
    # 生成文件名，使用当前时间戳
    file_extension = 'png'  # 请根据实际情况修改文件扩展名
    file_name = datetime.now().strftime('%Y%m%d%H%M%S') + '.' + file_extension

    # 解码base64数据
    image_data = base64.b64decode(base64_data)
    # 使用BytesIO将二进制数据封装为文件对象
    files = {'img': (file_name, BytesIO(image_data), 'image/png')}

    # 发送 POST 请求
    response = requests.post(api_endpoint, files=files)
    # print(response.text)
    if response.status_code == 200:
        print('文件上传成功。')
        return response.json()
    else:
        print('文件上传失败。')
        return None


def upload_img_from_file(file_path):
    with open(file_path, 'rb') as f:
        base64_data = base64.b64encode(f.read()).decode()

        res = upload_img(base64_data)
        if res:
            return res.get('download_url', '')
        else:
            return ''
