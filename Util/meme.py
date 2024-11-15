import json
import os
import random
import time

import requests

from Util.meme_info import emoji_value4jpg4txt, emoji_value4jpg, emoji_key4jpg4txt, emoji_value_custom, \
    emoji_value_double_jpg, \
    emoji_key4jpg, emoji_key_custom, emoji_mapping_dict
from advanced_path import PRJ_PATH

emoji_value_reply = [emoji + '*' if emoji in emoji_value4jpg4txt else emoji
                     for emoji in emoji_value4jpg]
value_custom_reply = [emoji + '*' for emoji in emoji_value_custom]
value_double_jpg_reply = [emoji + '°' for emoji in emoji_value_double_jpg]

emoji_value_reply_msg = ','.join(emoji_value_reply)
emoji_value_reply_msg += '\n' + ','.join(value_custom_reply)
emoji_value_reply_msg += '\n' + ','.join(value_double_jpg_reply)
emoji_value_reply_msg += '\n\n' + '其中，*表示可自定义文字，°表示需要艾特别人使用'


def generate_meme_file(filename, emoji, texts=None, filename2=None):
    try:
        if texts is None:
            texts = []
        # 这里对于同时传入了jpg和txt，但是不能使用txt的表情，将texts置空
        if (filename and texts) and (emoji not in emoji_key4jpg4txt + emoji_key_custom):
            texts = []
        print(f"filename: {filename}, emoji: {emoji}, texts: {texts}, filename2: {filename2}")

        files = [("images", open(filename, "rb"))]
        if filename2:
            files.append(("images", open(filename2, "rb")))
        # 对于可达鸭表情，将文字拆分成两部分，特殊处理
        if emoji == 'psyduck' and texts:
            if len(texts[0]) == 4:
                texts = [texts[0][:2], texts[0][2:]]
        args = {"circle": True}
        data = {"texts": texts, "args": json.dumps(args)}

        wxid = os.path.basename(filename).split(".")[0]
        if filename2:
            wxid2 = os.path.basename(filename2).split(".")[0]
            wxid = f"{wxid}_{wxid2}"

        img_dir = PRJ_PATH + '/Cache/Meme_Cache'
        os.makedirs(img_dir, exist_ok=True)

        if texts:
            file_name_prefix = f"{img_dir}/{wxid}_{emoji}_{str(int(time.time() * 1000))}"
        else:
            file_name_prefix = f"{img_dir}/{wxid}_{emoji}"

        if os.path.exists(f"{file_name_prefix}.gif"):
            return f"{file_name_prefix}.gif"
        if os.path.exists(f"{file_name_prefix}.jpg"):
            return f"{file_name_prefix}.jpg"

        # 如果是只可文字自定义表情，不传入图片
        if emoji in emoji_key_custom:
            files = []
        url = f"http://192.168.222.108:2233/memes/{emoji}/"
        resp = requests.post(url, files=files, data=data)
        if resp.status_code != 200:
            print(f"生成表情失败：{resp.text}")
            return

        # 根据 Content-Type 确定文件扩展名
        content_type = resp.headers.get('Content-Type', '')
        if 'image/gif' in content_type:
            result_filename = f"{file_name_prefix}.gif"
        else:
            result_filename = f"{file_name_prefix}.jpg"

        with open(result_filename, "wb") as f:
            f.write(resp.content)

        print(f"生成表情成功：{result_filename}")
        return result_filename

    except Exception as e:
        print(e)


def generate_meme(filename, emoji, texts=None, filename2=None):
    meme_file = generate_meme_file(filename, emoji, texts, filename2)
    if not meme_file:
        return
    if meme_file.endswith(".gif"):
        return meme_file
    else:
        filename = filename.replace(".jpg", "_pro.jpg")
        if os.path.exists(filename):
            meme_file = generate_meme_file(filename, emoji, texts, filename2)
        return meme_file


def generate_random_meme_by_jpg(filename):
    emoji = random.choice(emoji_key4jpg)
    emoji_value = emoji_mapping_dict.get(emoji, emoji)
    meme_file = generate_meme(filename, emoji)
    # if not meme_file:
    #     return generate_random_meme_by_jpg(filename)
    return meme_file, emoji_value

# print(len(emoji_value_reply + value_custom_reply + value_double_jpg_reply))
