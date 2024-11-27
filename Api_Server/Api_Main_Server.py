import base64
import json
import os
import random
import re
import time

import requests
import urllib3
import yaml
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

import Api_Server.SparkApi as SparkApi
from OutPut import OutPut
from Util.meme import generate_random_meme_by_jpg, generate_meme
from Util.meme_info import api_emoji_dict
from Util.util_db import IdiomDB, EmojiDB, QuestionDB
from advanced_path import PRJ_PATH


class Api_Main_Server:
    def __init__(self, wcf):
        self.wcf = wcf
        # 全局header头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            # 'Connection':'keep-alive' ,#默认时链接一次，多次爬取之后不能产生新的链接就会产生报错Max retries exceeded with url
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Connection": "close",  # 解决Max retries exceeded with url报错
        }
        # 忽略HTTPS告警
        urllib3.disable_warnings()

        # 配置缓存文件夹路径
        self.Cache_path = PRJ_PATH + '/Cache'
        self.Pic_path = PRJ_PATH + '/Pic'
        os.makedirs(self.Pic_path, exist_ok=True)
        os.makedirs(self.Pic_path + '/guess_idiom_image', exist_ok=True)
        # 初始化读取配置文件
        config = yaml.load(open(PRJ_PATH + '/Config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.system_copyright = config['System_Config']['System_Copyright']

        # 读取配置文件
        config = yaml.load(open(PRJ_PATH + '/Config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.Pic_Apis = config['Api_Server']['Pic_Api']
        self.Video_Apis = config['Api_Server']['Video_Api']
        self.Fish_Api = config['Api_Server']['Fish_Api']
        self.Kfc_Api = config['Api_Server']['Kfc_Api']
        self.Morning_Api = config['Api_Server']['Morning_Api']
        self.s60_Pic_Api = config['Api_Server']['60s_Pic_Api']
        # 星火配置
        self.Spark_url = config['Api_Server']['Ai_Config']['SparkApi']['Spark_url']
        self.Spark_ApiSecret = config['Api_Server']['Ai_Config']['SparkApi']['ApiSecret']
        self.Spark_Domain = config['Api_Server']['Ai_Config']['SparkApi']['Domain']
        self.Spark_ApiKey = config['Api_Server']['Ai_Config']['SparkApi']['ApiKey']
        self.Spark_Appid = config['Api_Server']['Ai_Config']['SparkApi']['Appid']
        # OpenAi配置
        self.OpenAi_Api = config['Api_Server']['Ai_Config']['Open_Ai']['OpenAi_Api']
        self.OpenAi_Key = config['Api_Server']['Ai_Config']['Open_Ai']['OpenAi_Key']
        self.OpenAi_Initiating_Message = config['Api_Server']['Ai_Config']['Open_Ai']['OpenAi_Role']
        self.OpenAi_Model = config['Api_Server']['Ai_Config']['Open_Ai']['OpenAi_Model']
        self.messages = [{"role": "system", "content": f"{self.OpenAi_Initiating_Message}"}]
        self.system_copyright = config['System_Config']['System_Copyright']
        # 混元配置
        self.HunYuan_id = config['Api_Server']['Ai_Config']['HunYuan']['HunYuanSecretId']
        self.HunYuan_Key = config['Api_Server']['Ai_Config']['HunYuan']['HunYuanSecretKey']
        # 秘塔搜索
        self.Metaso_Api = config['Api_Server']['Ai_Config']['Metaso']['Metaso_Api']
        self.Metaso_Key = config['Api_Server']['Ai_Config']['Metaso']['Metaso_Key']
        # spark_free_api
        self.Spark_Free_Api = config['Api_Server']['Ai_Config']['Spark_Free_Api']['Api']
        self.Spark_Free_Key = config['Api_Server']['Ai_Config']['Spark_Free_Api']['Key']
        # qwen_free_api
        self.Qwen_Free_Api = config['Api_Server']['Ai_Config']['Qwen_Free_Api']['Api']
        self.Qwen_Free_Key = config['Api_Server']['Ai_Config']['Qwen_Free_Api']['Key']
        # silicon_api
        self.Silicon_Api = config['Api_Server']['Ai_Config']['Silicon']['Api']
        self.Silicon_Key = config['Api_Server']['Ai_Config']['Silicon']['Key']

        # 成语数据库
        self.db_idiom = IdiomDB(PRJ_PATH + '/Config/idiom.db')
        # emoji数据库
        self.db_emoji = EmojiDB(PRJ_PATH + '/Config/emoji.db')
        # 知识问答数据库
        self.db_question = QuestionDB(PRJ_PATH + '/Config/questions.db')

        # 是否为高级画画模式
        self.is_advanced_drawing = True
        # 搜图模式
        self.search_pic_mode = 'baidu'

    # 获取AI识别图片
    def get_ai_identify_images(self, image_path, question):
        with open(image_path, 'rb') as f:
            base64_data = base64.b64encode(f.read()).decode()
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{question}"},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_data}"
                        }
                    }
                ]
            }
        ]
        data = {
            "model": self.OpenAi_Model,
            "messages": messages
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.OpenAi_Key}",
        }
        try:
            resp = requests.post(url=self.OpenAi_Api, headers=headers, json=data, timeout=15)
            json_data = resp.json()
            assistant_content = json_data['choices'][0]['message']['content']
            return assistant_content
        except Exception as e:
            OutPut.outPut(f'[-]: AI对话接口出现错误，错误信息： {e}')
            return None

    # Ai功能
    def get_ai(self, question, model=None):
        OutPut.outPut("[*]: 正在调用Ai对话接口... ...")
        OutPut.outPut(f"[*]: 问题：{question}")
        send_msgs = []

        def getText(role, content):
            jsonData = dict()
            jsonData["role"] = role
            jsonData["content"] = content
            send_msgs.append(jsonData)
            return send_msgs

        def getLength(text):
            length = 0
            for content in text:
                temp = content["content"]
                line = len(temp)
                length += line
            return length

        def checkLen(text):
            while getLength(text) > 8000:
                del text[0]
            return text

        # 星火大模型
        def get_xh(question):
            try:
                OutPut.outPut(f'[+]: 正在调用星火大模型... ...')
                question = checkLen(getText("user", question))
                SparkApi.answer = ""
                SparkApi.main(self.Spark_Appid, self.Spark_ApiKey, self.Spark_ApiSecret, self.Spark_url,
                              self.Spark_Domain,
                              question)
                getText("assistant", SparkApi.answer)
                Xh_Msg = SparkApi.get_content()
                return Xh_Msg
            except Exception as e:
                OutPut.outPut(f'[-]: 星火大模型出现错误，错误信息: {e}')
                return None

        if model is None:
            gpt_msg = self.getGpt(content=question)
            if gpt_msg:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return gpt_msg
            else:
                try:
                    Xh_Msg = get_xh(question=question)
                except Exception as e:
                    OutPut.outPut(f'[-]: 星火大模型出现错误，错误信息: {e}')
                    return "Ai对话接口调用失败！！！"
                else:
                    OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                    return Xh_Msg
        elif model == 'gpt':
            gpt_msg = self.getGpt(content=question)
            if gpt_msg:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return gpt_msg
            else:
                return None
        elif model == 'xh':
            Xh_Msg = get_xh(question=question)
            if not Xh_Msg:
                return '星火大模型出现错误，请查看日志！'
            else:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return Xh_Msg
        elif model == 'tx':
            ret, msg_lst = self.getHunYuanAi(content=question)
            if not ret:
                return '腾讯混元接口出现错误，请查看日志！'
            else:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return ret
        elif model == 'metaso':
            metaso_msg = self.get_metaso(content=question)
            if metaso_msg:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return metaso_msg
            else:
                metaso_msg = self.get_metaso(content=question, model='detail')
                if metaso_msg:
                    OutPut.outPut('[+]: 秘塔搜索接口调用成功！！！')
                    return metaso_msg
                else:
                    return '秘塔搜索接口出现错误，请查看日志！'
        elif model == 'image':
            if not self.is_advanced_drawing:
                spark_free_msg = self.get_spark_free_image(content=question)
                if spark_free_msg:
                    OutPut.outPut('[+]: Spark文生图接口调用成功！！！')
                    return spark_free_msg
                else:
                    qwen_free_msg = self.get_qwen_free_image(content=question)
                    if qwen_free_msg:
                        OutPut.outPut('[+]: Qwen文生图接口调用成功！！！')
                        return qwen_free_msg
                    return None
            else:
                silicon_msg = self.get_silicon_flow_image(content=question)
                if silicon_msg:
                    OutPut.outPut('[+]: Silicon接口调用成功！！！')
                    return silicon_msg
                else:
                    return None

    # Gpt模型
    def getGpt(self, content):
        self.messages.append({"role": "user", "content": f'{content}'})
        data = {
            "model": self.OpenAi_Model,
            "messages": self.messages
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"{self.OpenAi_Key}",
        }
        try:
            resp = requests.post(url=self.OpenAi_Api, headers=headers, json=data, timeout=15)
            json_data = resp.json()
            assistant_content = json_data['choices'][0]['message']['content']
            self.messages.append({"role": "assistant", "content": f"{assistant_content}"})
            if len(self.messages) >= 10:
                self.messages = [{"role": "system", "content": f"{self.OpenAi_Initiating_Message}"}]
            return assistant_content
        except Exception as e:
            OutPut.outPut(f'[-]: AI对话接口出现错误，错误信息： {e}')
            self.messages = [{"role": "system", "content": f"{self.OpenAi_Initiating_Message}"}]
            return None

    # 秘塔搜索
    def get_metaso(self, content, model='concise'):
        messages = [{"role": "user", "content": f'{content}'}]
        data = {
            "model": model,
            "messages": messages
        }
        headers = {
            "Authorization": f"{self.Metaso_Key}",
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }
        try:
            resp = requests.post(url=self.Metaso_Api, headers=headers, json=data, timeout=15)
            json_data = resp.json()
            print(json_data)
            assistant_content = json_data['choices'][0]['message']['content']
            return assistant_content if assistant_content else None
        except Exception as e:
            OutPut.outPut(f'[-]: 秘塔搜索接口出现错误，错误信息： {e}')
            return None

    # spark_free_api
    def get_spark_free_image(self, content):
        data = {
            "prompt": content
        }
        headers = {
            "Authorization": f"{self.Spark_Free_Key}",
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }
        try:
            resp = requests.post(url=self.Spark_Free_Api, headers=headers, json=data, timeout=60)
            json_data = resp.json()
            OutPut.outPut(f"[*]: spark_free_api接口返回数据：{json_data}")
            assistant_content = json_data['data'][0]['url']
            return assistant_content if assistant_content else None
        except Exception as e:
            OutPut.outPut(f'[-]: spark_free_api接口出现错误，错误信息： {e}')
            return None

    # qwen_free_api
    def get_qwen_free_image(self, content):
        data = {
            "prompt": content
        }
        headers = {
            "Authorization": f"{self.Qwen_Free_Key}",
            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
            'Content-Type': 'application/json'
        }
        try:
            resp = requests.post(url=self.Qwen_Free_Api, headers=headers, json=data, timeout=60)
            json_data = resp.json()
            OutPut.outPut(f"[*]: qwen_free_api接口返回数据：{json_data}")
            assistant_content = json_data['data'][0]['url']
            return assistant_content if assistant_content else None
        except Exception as e:
            OutPut.outPut(f'[-]: qwen_free_api接口出现错误，错误信息： {e}')
            return None

    def get_silicon_flow_image(self, content):
        content = self.get_translate(content) or self.get_translate_by_api(content)
        if not content:
            return None
        url = self.Silicon_Api

        payload = {
            "prompt": content,
            "image_size": "1536x1024",
            "batch_size": 1,
            "num_inference_steps": 25,
            "guidance_scale": 5
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": self.Silicon_Key
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            json_data = response.json()
            image_url = json_data.get("images")[0].get("url")
            return image_url
        except Exception as e:
            print(e)
            return None

    def getHunYuanAi(self, content, messages=None):
        """
        腾讯混元模型 Ai对话接口
        :param content:
        :param messages:
        :return:
        """
        if messages is None:
            messages = []

        try:
            OutPut.outPut(f'[*]: 正在调用混元模型对话接口... ...')
            cred = credential.Credential(self.HunYuan_id, self.HunYuan_Key)
            httpProfile = HttpProfile()
            httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = hunyuan_client.HunyuanClient(cred, "ap-beijing", clientProfile)
            req = models.ChatCompletionsRequest()
            messages.append({'Role': 'user', 'Content': content})
            params = {
                "Model": "hunyuan-pro",
                "Messages": messages,
            }
            req.from_json_string(json.dumps(params))
            Choices = str(client.ChatCompletions(req).Choices[0])
            jsonData = json.loads(Choices)
            Message = jsonData['Message']
            messages.append({'Role': Message['Role'], 'Content': Message['Content']})
            content = Message['Content']
            if len(messages) == 21:
                del messages[1]
                del messages[2]
            if content:
                return content, messages
            return None, []
        except TencentCloudSDKException as e:
            OutPut.outPut(f'[-]: 腾讯混元Ai对话接口出现错误, 错误信息: {e}')
            return None, messages

    # 美女图片
    def get_girl_pic(self):
        OutPut.outPut(f'[*]: 正在调用美女图片接口... ...')
        url = random.choice(self.Pic_Apis)
        save_path = self.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.jpg'
        try:
            pic_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).content
            with open(file=save_path, mode='wb') as pd:
                pd.write(pic_data)
        except Exception as e:
            msg = f'[-]: 美女图片API接口出现错误，错误信息：{e}\n正在回调中... ...'
            OutPut.outPut(msg)
            return self.get_girl_pic()
        OutPut.outPut(f'[+]: 美女图片API接口调用成功！！！')
        return save_path

    # 美女视频
    def get_girl_video(self):
        OutPut.outPut('[*]: 正在调用美女视频API接口... ...')
        url = random.choice(self.Video_Apis)
        save_path = self.Cache_path + '/Video_Cache/' + str(int(time.time() * 1000)) + '.mp4'
        try:
            video_data = requests.get(url=url, headers=self.headers, timeout=90, verify=False).content
            with open(file=save_path, mode='wb') as vd:
                vd.write(video_data)
        except Exception as e:
            msg = f'[-]: 美女视频API接口出现错误，错误信息：{e}\n正在回调中... ...'
            OutPut.outPut(msg)
            return self.get_girl_video()
        OutPut.outPut(f'[+]: 美女视频API接口调用成功！！！')
        return save_path

    # 早安寄语
    def get_morning(self):
        OutPut.outPut('[*]: 正在调用早安寄语API接口... ...')
        url = self.Morning_Api
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            content = json_data['content']
            OutPut.outPut(f'[+]: 早安寄语API接口调用成功！！！')
            print(content)
            return content
        except Exception as e:
            msg = f'[-]: 早安寄语接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 秒懂世界图片
    def get_60s_pic_url(self):
        url = self.s60_Pic_Api
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
            if json_data['code'] != "200":
                return None
            pic_url = json_data['imageBaidu']
            return pic_url
        except Exception as e:
            return None

    def get_60s_pic(self):
        OutPut.outPut('[*]: 正在调用60s图片接口... ...')
        url = "https://api.lbbb.cc/api/60s"
        save_path = self.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.jpg'
        if not url:
            msg = f'[-]: 60s图片API接口出现错误, 错误信息请查看日志 ~~~~~~'
            OutPut.outPut(msg)
            return None
        try:
            pic_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).content
            with open(file=save_path, mode='wb') as pd:
                pd.write(pic_data)
        except Exception as e:
            msg = f'[-]: 60s图片API接口出现错误，错误信息：{e}'
            OutPut.outPut(msg)
            return None
        OutPut.outPut(f'[+]: 60s图片API接口调用成功！！！')
        return save_path

    # 摸鱼日记
    def get_fish(self):
        OutPut.outPut(f'[*]: 正在调用摸鱼日记接口... ...')
        save_path = self.Cache_path + '/Fish_Cache/' + str(int(time.time() * 1000)) + '.jpg'
        try:
            url = random.choice(self.Fish_Api)
            res = requests.get(url=url, timeout=30, verify=True)
            if res.status_code != 200:
                msg = f'[-]: 摸鱼日记API接口出现错误，错误信息：{res.status_code}\n正在回调中... ...'
                OutPut.outPut(msg)
                return self.get_fish()
            pic_data = res.content
            with open(file=save_path, mode='wb') as pd:
                pd.write(pic_data)
        except Exception as e:
            msg = f'[-]: 摸鱼日记API接口出现错误，错误信息：{e}\n正在回调中... ...'
            OutPut.outPut(msg)
            save_path = self.get_fish()
        OutPut.outPut(f'[+]: 摸鱼日记API接口调用成功！！！')
        return save_path

    # 疯狂星期四文案
    def get_kfc(self):
        OutPut.outPut('[*]: 正在调用疯狂星期四文案API接口... ...')
        try:
            json_data = requests.get(url=self.Kfc_Api, timeout=30, verify=False).json()
            if json_data['code'] != 200:
                msg = '[~]: 疯狂星期四文案接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            msg = json_data['text']
            OutPut.outPut(f'[+]: 疯狂星期四文案API接口调用成功！！！')
            return msg
        except Exception as e:
            msg = f'[-]: 疯狂星期四文案接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 看图猜成语
    def get_idiom_data(self):
        url = "https://api.andeer.top/API/guess_idiom_img.php"
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
            if json_data['code'] != 200:
                return None
            data = json_data['data']
            return data
        except Exception as e:
            print(e)
            return None

    # 看图猜成语
    def get_idiom_data_new(self):
        # random_num = random.randint(1, 2)
        # if random_num == 1:
        #     return self.get_idiom_data()
        api_lst = ["https://api.lolimi.cn/API/ktcc/api.php", "https://free.wqwlkj.cn/wqwlapi/ccy.php"]
        url = random.choice(api_lst)
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
            if json_data['code'] != 1:
                return None
            idiom_dict = {'答案': json_data['answer'], '图片链接': json_data['img']}
            return idiom_dict
        except Exception as e:
            print(e)
            return None

    # 看图猜成语
    def get_idiom(self):
        OutPut.outPut('[*]: 正在调用看图猜成语API接口... ...')
        idiom_data = self.get_idiom_data_new()
        try:
            pic_name = idiom_data.get('答案', '未知')
            idiom_dict = self.get_idiom_dict(pic_name)
            if not idiom_dict:
                raise Exception('未查询到该成语')
            idiom_data.update(idiom_dict)

            save_path = self.Pic_path + '/guess_idiom_image/' + pic_name + '.jpg'
            # save_path = self.Pic_path + '/guess_idiom_image/' + str(int(time.time() * 1000)) + '.jpg'

            url = idiom_data['图片链接']
            if url and not os.path.exists(save_path):
                res = requests.get(url=url, headers=self.headers, timeout=30, verify=False)
                if res.status_code != 200:
                    raise Exception('图片请求失败')
                pic_data = res.content
                with open(file=save_path, mode='wb') as pd:
                    pd.write(pic_data)
        except Exception as e:
            msg = f'[-]: 看图猜成语接口出现错误，错误信息：{e}，回调中... ...'
            OutPut.outPut(msg)
            time.sleep(0.2)
            return self.get_idiom()
        OutPut.outPut(f'[+]: 看图猜成语接口调用成功！！！')
        OutPut.outPut(f'[+]: 成语图片保存路径：{save_path}')
        return save_path, idiom_data

    # 成语解析
    def get_idiom_explain(self, idiom):
        info = self.db_idiom.get_info_by_word(idiom)
        if info:
            res = f"【{info.get('word')}】\n" \
                  f"拼音：[{info.get('pinyin')}]\n" \
                  f"解释：{info.get('explanation')}\n" \
                  f"出处：{info.get('derivation')}\n" \
                  f"例句：{info.get('example')}"
            return res
        else:
            return f"未查询到该成语【{idiom}】"

    def get_idiom_dict(self, idiom):
        info = self.db_idiom.get_info_by_word(idiom)
        idiom_dict = {}
        if info:
            idiom_dict['答案'] = info.get('word')
            idiom_dict['拼音'] = info.get('pinyin')
            idiom_dict['解释'] = info.get('explanation')
            idiom_dict['出处'] = info.get('derivation')
            idiom_dict['例句'] = info.get('example')
        return idiom_dict

    # 谷歌翻译
    @staticmethod
    def get_translate(content):
        OutPut.outPut('[*]: 正在调用谷歌翻译API接口... ...')
        url = "http://192.168.222.108:9200/translate/{}".format(content)
        try:
            json_data = requests.get(url=url, timeout=30).json()
            print(json_data)
            if not json_data['success']:
                msg = f'[~]: 谷歌翻译接口出现错误, 错误信息请查看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            msg = json_data['result']
            OutPut.outPut(f'[+]: 谷歌翻译API接口调用成功！！！')
            return msg
        except Exception as e:
            msg = f'[-]: 谷歌翻译接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 谷歌翻译外置API
    @staticmethod
    def get_translate_by_api(content):
        OutPut.outPut('[*]: 正在调用谷歌翻译API接口... ...')
        url = "https://api.pearktrue.cn/api/googletranslate/?text={}&type=auto".format(content)
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            # print(json_data)
            if json_data['code'] != 200:
                msg = '[~]: 谷歌翻译接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                try:
                    url = f"https://api.qqguaji.cn/api/fanyi.php?msg={content}"
                    res = requests.get(url=url, timeout=30, verify=False)
                    if res.status_code != 200:
                        return None
                    res_txt = res.text
                    return res_txt.split('翻译后：')[1].strip()
                except Exception as e:
                    msg = f'[-]: 谷歌翻译接口出现错误, 错误信息：{e}'
                    OutPut.outPut(msg)
                    return None
            msg = json_data['result']
            OutPut.outPut(f'[+]: 谷歌翻译API接口调用成功！！！')
            OutPut.outPut(f'[+]: 翻译结果：{msg}')
            return msg
        except Exception as e:
            msg = f'[-]: 谷歌翻译接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            try:
                url = f"https://api.qqguaji.cn/api/fanyi.php?msg={content}"
                res = requests.get(url=url, timeout=30, verify=False)
                if res.status_code != 200:
                    return None
                res_txt = res.text
                return res_txt.split('翻译后：')[1].strip()
            except Exception as e:
                msg = f'[-]: 谷歌翻译接口出现错误, 错误信息：{e}'
                OutPut.outPut(msg)
                return None

    # 天气查询接口
    def query_weather(self, content):
        OutPut.outPut(f'[*]: 正在调用天气查询接口... ...')
        city = content.split(' ')[-1]
        try:
            question = f'查询{city}今天明天后天的天气，除了每天的时间、天气、温度外，还有出行建议'
            return self.getHunYuanAi(question)[0]
        except Exception as e:
            msg = f'[-]: 天气查询API接口出现错误，错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 虎扑热搜
    def get_hupu(self):
        OutPut.outPut('[*]: 正在调用虎扑热搜API接口... ...')
        url = "https://api.vvhan.com/api/hotlist/huPu"
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['success'] is False:
                msg = f'[~]: 虎扑热搜接口出现错误, 错误信息请查看日志 ~~~~~~'
                return msg
            hot_search = json_data['data']
            if not hot_search:
                return None

            # content_lst = []
            # queue1 = hot_search[:len(hot_search) // 2]
            # queue2 = hot_search[len(hot_search) // 2:]
            # # 分别处理两个队列
            # for i, queue_data in enumerate([queue1, queue2]):
            #     start_index = i * (len(hot_search) // 2)
            #     end_index = start_index + len(queue_data)
            #     content = f'虎扑热搜 {start_index + 1}-{end_index}\n'
            #     for index, item in enumerate(queue_data):
            #         content += f'{start_index + index + 1}、{item["title"]}\n{item["url"]}\n'
            #     content_lst.append(content)

            content_lst = []
            content = '虎扑热搜\n'
            for i, queue_data in enumerate(hot_search):
                content += f'{i + 1}、{queue_data["title"]}\n{queue_data["url"]}\n'
            content_lst.append(content)
            OutPut.outPut(f'[+]: 虎扑热搜API接口调用成功！！！')
            return content_lst
        except Exception as e:
            msg = f'[-]: 虎扑热搜接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)

    # 每日英语
    @staticmethod
    def get_daily_english():
        OutPut.outPut('[*]: 正在调用每日英语API接口... ...')
        url = "https://api.oioweb.cn/api/common/OneDayEnglish"
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            # print(json_data)
            if json_data['code'] != 200:
                msg = '[~]: 每日英语接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            json_data = json_data['result']
            msg = json_data['content'] + '\n' + json_data['note']
            OutPut.outPut(f'[+]: 每日英语API接口调用成功！！！')
            return msg
        except Exception as e:
            msg = f'[-]: 每日英语接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 百度百科
    @staticmethod
    def get_baidu_baike(question):
        OutPut.outPut('[*]: 正在调用百度百科API接口... ...')
        url = f"https://oiapi.net/API/BaiduEncyclopedia?msg={question}"
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['code'] != 1:
                return False, json_data.get('message', '未知错误')
            OutPut.outPut(f'[+]: 百度百科API接口调用成功！！！')
            return True, json_data['data']
        except Exception as e:
            msg = f'[-]: 百度百科接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return False, '未知错误'

    @staticmethod
    def get_random_music():
        url = "https://www.hhlqilongzhu.cn/api/musicList_wyy.php?id=2573305699"
        # url = "https://www.hhlqilongzhu.cn/api/dg_QQphb.php?id=1&type=1"
        # qq https://www.hhlqilongzhu.cn/api/dg_qqmusic.php?gm=red&n=1
        try:
            json_data = requests.get(url=url, timeout=30).json()
            json_data = json_data['data']
            music_data = {"歌名": json_data['name'], "歌手": json_data['artistsname'], "播放链接": json_data['url'],
                          "歌曲详情页": json_data['link'], "img": json_data['picurl']}
            # music_data = {"歌名": json_data['title'], "歌手": json_data['singer'], "播放链接": json_data['song_url'],
            #               "歌曲详情页": json_data['link'], "img": json_data['song_cover']}
            return music_data
        except Exception as e:
            return None

    def search_image(self, msg):
        OutPut.outPut(f'[*] 正在调用搜图API接口...')
        try:
            if self.search_pic_mode == "baidu":
                # url = f"https://api.52vmy.cn/api/img/baidu?msg={msg}"
                url = f"https://api.suyanw.cn/api/baidu_image_search.php?msg={msg}"
                # save_path = os.path.join(self.Cache_path, 'Pic_Cache', f"{msg}-{int(time.time() * 1000)}.jpg")
                save_path = os.path.join(self.Cache_path, 'Pic_Cache', f"{int(time.time() * 1000)}.jpg")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保保存路径存在
                pic_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).content
                if not pic_data:
                    OutPut.outPut('[~] 搜图API接口调用失败！！！')
                    return None
                with open(file=save_path, mode='wb') as pd:
                    pd.write(pic_data)
                OutPut.outPut('[+] 搜图API接口调用成功！！！')
                return save_path

            elif self.search_pic_mode == "360":
                url = f"https://api.52vmy.cn/api/img/360?msg={msg}"
            else:
                url = f"https://api.52vmy.cn/api/img/sogo?msg={msg}"
            res = requests.get(url, timeout=30)
            json_data = res.json()
            print(json_data)

            if json_data['code'] == 200:
                image_url = json_data['data']['url']
                image_data = requests.get(image_url, headers=self.headers, timeout=30).content
                # save_path = os.path.join(self.Cache_path, 'Pic_Cache', f"{msg}-{int(time.time() * 1000)}.jpg")
                save_path = os.path.join(self.Cache_path, 'Pic_Cache', f"{int(time.time() * 1000)}.jpg")
                os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保保存路径存在
                with open(save_path, 'wb') as img_file:
                    img_file.write(image_data)

                OutPut.outPut('[+] 搜图API接口调用成功！！！')
                return save_path
            else:
                OutPut.outPut(f'[-] 搜图API接口返回错误：{json_data["msg"]}')
                return None

        except Exception as e:
            OutPut.outPut(f'[-] 搜图API接口调用失败，错误信息：{e}')
            return None

    @staticmethod
    def search_novel(msg):
        OutPut.outPut(f'[*] 正在调用搜书API接口...')
        try:
            url = f"https://www.hhlqilongzhu.cn/api/novel_1.php?name={msg}&n="
            res = requests.get(url, timeout=30)
            content = res.text
            print(content)

            if content:
                OutPut.outPut('[+] 搜书API接口调用成功！！！')
                return content, url
            else:
                OutPut.outPut(f'[-] 搜书API接口返回错误')
                return None, None

        except Exception as e:
            OutPut.outPut(f'[-] 搜书API接口调用失败，错误信息：{e}')
            return None, None

    @staticmethod
    def search_song(msg):
        OutPut.outPut(f'[*] 正在调用搜歌API接口...')
        try:
            # url = f"http://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg={msg}&n="
            url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={msg}&n="
            res = requests.get(url, timeout=30)
            content = res.text
            print(content)

            if content:
                OutPut.outPut('[+] 搜歌API接口调用成功！！！')
                return content, url
            else:
                OutPut.outPut(f'[-] 搜歌API接口返回错误')
                return None, None

        except Exception as e:
            OutPut.outPut(f'[-] 搜歌API接口调用失败，错误信息：{e}')
            return None, None

    @staticmethod
    def parse_song_url(url):
        OutPut.outPut(f'[*] 正在调用解析歌曲链接API接口...')
        try:
            res = requests.get(url, timeout=30)
            content = res.text
            print(content)

            # 正则表达式用于提取歌名、歌手
            pattern = r'±img=(?P<img>.*?)±\s*歌名：(?P<歌名>.*?)\s*歌手：(?P<歌手>.*?)\s*歌曲详情页：(?P<歌曲详情页>.*?)\s'

            match = re.match(pattern, content)
            if match:
                data_dict = match.groupdict()
                # 打印字典
                print(data_dict)
            else:
                print("无法解析字符串为字典格式")
                data_dict = None

            if data_dict:
                # 正则表达式用于提取MP3链接
                pattern_mp3 = r'http[^\s]+\.(?:mp3|flac|wav|m4a)'

                mp3_urls = re.findall(pattern_mp3, content)
                if mp3_urls:
                    data_dict['播放链接'] = mp3_urls[0]
                else:
                    OutPut.outPut(f'[-] 无法提取MP3链接')
                    data_dict = None

            if data_dict:
                OutPut.outPut('[+] 解析歌曲链接API接口调用成功！！！')
                return data_dict
            else:
                OutPut.outPut(f'[-] 解析歌曲链接API接口返回错误')
                return None

        except Exception as e:
            OutPut.outPut(f'[-] 解析歌曲链接API接口调用失败，错误信息：{e}')
            return None

    def download_song(self, song_info):
        OutPut.outPut(f'[*] 正在调用下载歌曲API接口...')
        try:
            song_url = song_info['播放链接']
            res = requests.get(song_url, timeout=30)
            content = res.content

            # save_path = os.path.join(self.Cache_path, 'Music_Cache', f"{song_info['歌手']}-{song_info['歌名']}.flac")
            save_path = os.path.join(self.Cache_path, 'Music_Cache', f"{song_info['歌手']}-{song_info['歌名']}.mp3")
            # save_path = os.path.join(self.Cache_path, 'Music_Cache', f"{str(int(time.time() * 1000))}.mp3")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保保存路径存在
            with open(save_path, 'wb') as song_file:
                song_file.write(content)

            OutPut.outPut('[+] 下载歌曲API接口调用成功！！！')
            return save_path

        except Exception as e:
            OutPut.outPut(f'[-] 下载歌曲API接口调用失败，错误信息：{e}')
            return None

    def down_song_by_url(self, url):
        song_info = self.parse_song_url(url)
        if song_info:
            song_path = self.download_song(song_info)
            return song_path
        else:
            return None

    def down_novel_by_url(self, url):
        res = requests.get(url, timeout=30)
        if res.status_code == 200:
            json_content = res.json()
            file_name = json_content['title'] + '-' + json_content['author'] + '.txt'
            save_path = os.path.join(self.Cache_path, 'Novel_Cache', file_name)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)  # 确保保存路径存在

            res = requests.get(json_content['download'], timeout=30)
            if res.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(res.content)
                return save_path

    # 喜加一
    def get_steam_plus_one(self):
        OutPut.outPut('[*]: 正在调用喜加一API接口... ...')
        url = "https://api.tangdouz.com/a/steam.php?return=json"
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
            print(json_data)
            if not json_data['name']:
                msg = '[~]: 喜加一接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            msg_list = []
            game_list = [json_data]
            for game in game_list:
                msg = f"游戏平台：{game['store'].strip()}\n" \
                      f"游戏名称：{game['name'].strip()}\n" \
                      f"领取时间：{game['start'].strip()}至{game['end'].strip()}\n" \
                      f"游戏链接：{game['url'].strip()}"
                msg_list.append(msg)
                detail = self.get_metaso(game['name'].strip(), 'detail')
                if detail is not None:
                    msg_list.append(detail.replace('\n\n', '\n'))
            OutPut.outPut(f'[+]: 喜加一API接口调用成功！！！')
            return msg_list
        except Exception as e:
            msg = f'[-]: 喜加一接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    @staticmethod
    def parse_vx_video(payload):
        try:
            url = ""
            # 发起 POST 请求
            response = requests.post(url, json=payload)
            # 检查响应状态码
            if response.status_code == 200:
                # print("请求成功!")
                # print("响应数据:", response.json())  # 如果响应是 JSON 格式
                return response.json()
            else:
                # print(f"请求失败, 状态码: {response.status_code}")
                # print("响应内容:", response.text)
                return None
        except requests.exceptions.RequestException as e:
            print(f"请求发生错误: {e}")

    # 生成表情
    @staticmethod
    def magic_emoji_by_head(head):
        emoji_path, key_word = generate_random_meme_by_jpg(head)

        return emoji_path, key_word

    # 生成表情
    @staticmethod
    def magic_emoji_by_head_and_emoji(head, emoji, texts=None, head2=None):
        meme_file = generate_meme(head, emoji, texts=texts, filename2=head2)

        return meme_file

    @staticmethod
    def magic_emoji_by_api(emoji, head_url):
        if not (emoji and head_url):
            print(f"参数不足，生成表情失败：{emoji}")
            return
        file_name_prefix = f"{emoji}-{str(int(time.time() * 1000))}"
        url = api_emoji_dict.get(emoji) + head_url
        print(url)
        try:
            resp = requests.get(url, timeout=15)
        except Exception as e:
            print(f"生成表情失败，重试一次")
            try:
                resp = requests.get(url, timeout=15)
            except Exception as e:
                print(f"生成表情失败：{emoji}")
                return
        if resp.status_code != 200:
            print(f"生成表情失败：{emoji}")
            return
        # 根据 Content-Type 确定文件扩展名
        content_type = resp.headers.get('Content-Type', '')
        print(content_type)
        if 'image/gif' in content_type.lower():
            result_filename = f"{file_name_prefix}.gif"
        else:
            result_filename = f"{file_name_prefix}.jpg"

        img_dir = PRJ_PATH + '/Cache/Meme_Cache'
        os.makedirs(img_dir, exist_ok=True)
        result_filename = os.path.join(img_dir, result_filename)

        with open(result_filename, "wb") as f:
            f.write(resp.content)

        print(f"生成表情成功：{result_filename}")
        return result_filename


if __name__ == '__main__':
    Ams = Api_Main_Server(1)
    # print(Ams.parse_song_url("http://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg=周杰伦&n=1"))
    # print(Ams.get_random_music())
    # Ams.magic_emoji_by_api("扭屁股", "https://gw.alicdn.com/tfscom/tuitui/O1CN01xazVaP1ZRyiyUGdAI_!!0-rate.jpg")
    print(Ams.get_ai_identify_images("/home/frz/图片/help.jpg", "图片是什么内容"))
