import json
import os
import random
import re
import time

import requests
import urllib3
import yaml
from bs4 import BeautifulSoup

import Api_Server.SparkApi as SparkApi
from OutPut import OutPut
from Util.meme import generate_random_meme_by_jpg, generate_meme
from Util.my_db import IdiomDB, EmojiDB
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
        # 初始化读取配置文件
        config = yaml.load(open(PRJ_PATH + '/Config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.system_copyright = config['System_Config']['System_Copyright']

        # 读取配置文件
        config = yaml.load(open(PRJ_PATH + '/Config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.Key = config['Api_Server']['Api_Config']['Key']
        self.ThreatBook_Key = config['Api_Server']['Api_Config']['ThreatBook_Key']
        self.Pic_Apis = config['Api_Server']['Pic_Api']
        self.Video_Apis = config['Api_Server']['Video_Api']
        self.Icp_Api = config['Api_Server']['Icp_Api']
        self.Attribution_Api = config['Api_Server']['Attribution_Api']
        self.Whois_Api = config['Api_Server']['Whois_Api']
        self.Fish_Api = config['Api_Server']['Fish_Api']
        self.Kfc_Api = config['Api_Server']['Kfc_Api']
        self.Weather_Api = config['Api_Server']['Weather_Api']
        self.Dog_Api = config['Api_Server']['Dog_Api']
        self.Morning_Api = config['Api_Server']['Morning_Api']
        self.Constellation_Api = config['Api_Server']['Constellation_Api']
        self.ThreatBook_Api = config['Api_Server']['ThreatBook_Api']
        self.Somd5_Md5_url = config['Api_Server']['Somd5_Md5_Api']
        self.Somd5_Key = config['Api_Server']['Api_Config']['Somd5_Key']
        self.Dream_Api = config['Api_Server']['Dream_Api']
        self.Port_Scan_Api = config['Api_Server']['Port_Scan_Api']
        self.Chicken_Soup_Api = config['Api_Server']['Chicken_Soup_Api']
        self.Joke_Api = config['Api_Server']['Joke_Api']
        self.s60_Api = config['Api_Server']['60s_Api']
        self.s60_Pic_Api = config['Api_Server']['60s_Pic_Api']
        self.Hupu_Api = config['Api_Server']['Hupu_Api']
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
        self.messages = [{"role": "system", "content": f"{self.OpenAi_Initiating_Message}"}]
        self.system_copyright = config['System_Config']['System_Copyright']
        # 千帆配置
        self.qf_ak = config['Api_Server']['Ai_Config']['QianFan']['Qf_Access_Key']
        self.qf_sk = config['Api_Server']['Ai_Config']['QianFan']['Qf_Secret_Key']
        # if self.qf_ak and self.qf_sk:
        #     self.chat_comp = qianfan.ChatCompletion(ak=self.qf_ak,
        #                                             sk=self.qf_sk)
        #     self.chat_mess = qianfan.Messages()
        #     pass
        # else:
        #     OutPut.outPut(f'[-]: 千帆模型未配置，请修改配置文件已启用模型！！！')
        # 秘塔搜索
        self.Metaso_Api = config['Api_Server']['Ai_Config']['Metaso']['Metaso_Api']
        self.Metaso_Key = config['Api_Server']['Ai_Config']['Metaso']['Metaso_Key']
        # spark_free_api
        self.Spark_Free_Api = config['Api_Server']['Ai_Config']['Spark_Free_Api']['Api']
        self.Spark_Free_Key = config['Api_Server']['Ai_Config']['Spark_Free_Api']['Key']
        # qwen_free_api
        self.Qwen_Free_Api = config['Api_Server']['Ai_Config']['Qwen_Free_Api']['Api']
        self.Qwen_Free_Key = config['Api_Server']['Ai_Config']['Qwen_Free_Api']['Key']

        # 成语数据库
        self.db_idiom = IdiomDB(PRJ_PATH + '/Config/idiom.db')
        # emoji数据库
        self.db_emoji = EmojiDB(PRJ_PATH + '/Config/emoji.db')

        # 是否为高级画画模式
        self.is_advanced_drawing = False
        # 搜图模式
        self.search_pic_mode = 'baidu'

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

        # 千帆大模型
        def get_qf(quest):
            try:
                OutPut.outPut(f'[*]: 正在调用千帆大模型... ...')
                self.chat_mess.append(quest)
                resp = self.chat_comp.do(messages=self.chat_mess)
                self.chat_mess.append(resp)
                accept_msg = resp['body']['result']
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return accept_msg
            except Exception as e:
                OutPut.outPut(f'[-]: 千帆大模型出现错误，错误信息: {e}')
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
                    return None
                if not Xh_Msg:
                    if not self.qf_ak:
                        OutPut.outPut(f'[-]: 千帆模型接口未配置，其它模型出现错误，请查看日志！')
                        return '千帆模型接口未配置，其它模型出现错误，请查看日志！'
                    return get_qf(quest=question)
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
            try:
                Xh_Msg = get_xh(question=question)
            except Exception as e:
                OutPut.outPut(f'[-]: 星火大模型出现错误，错误信息: {e}')
                return None
            if not Xh_Msg:
                return '星火大模型出现错误，请查看日志！'
            else:
                OutPut.outPut('[+]: Ai对话接口调用成功！！！')
                return Xh_Msg
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
            "model": "gpt-3.5-turbo",
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
            if len(self.messages) == 15:
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
        content = self.get_translate_by_api(content)
        if not content:
            return None
        url = ""

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
            "Authorization": "Bearer sk-"
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            json_data = response.json()
            image_url = json_data.get("images")[0].get("url")
            return image_url
        except Exception as e:
            print(e)
            return None

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
            save_path = self.get_girl_pic()
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
            save_path = self.get_girl_video()
        OutPut.outPut(f'[+]: 美女视频API接口调用成功！！！')
        return save_path

    # 天气查询接口
    def query_weather(self, content):
        OutPut.outPut(f'[*]: 正在调用天气查询接口... ...')
        city = content.split(' ')[-1]
        try:
            json_data = requests.get(url=self.Weather_Api.format(self.Key, city), verify=False).json()
            alarm_msg = ''
            if json_data['code'] == 200:
                data = json_data['result']
                if data['alarmlist']:
                    alarm_lists = data['alarmlist']
                    for alarm in alarm_lists:
                        alarm_msg += f'{alarm["content"]}\n'
                msg = f'\n今日{data["weather"]}天：{data["week"]}\n日期：{data["date"]}\n当前温度：{data["real"]}\n最低温度：{data["lowest"]}\n风向：{data["wind"] + data["windsc"]}\n风速：{data["windspeed"]}\n日出：{data["sunrise"]}\n日落：{data["sunset"]}\n降水量：{data["pcpn"]}\n空气质量：{data["quality"]}\n天气预警：{alarm_msg if alarm_msg else "无"}\n{"By: #" + self.system_copyright if self.system_copyright else ""}'
                return msg
            OutPut.outPut(f'[+]: 天气查询API接口调用成功！！！')
            if json_data['code'] != 200:
                return None
        except Exception as e:
            msg = f'[-]: 天气查询API接口出现错误，错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 舔狗日记
    def get_dog(self):
        OutPut.outPut('[*]: 正在调用舔狗日记API接口... ...')
        url = self.Dog_Api.format(self.Key)
        # url = "https://api.52vmy.cn/api/wl/yan/tiangou"
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=20, verify=False).json()
            print(json_data)
            if json_data['code'] == 200:
                msg = json_data['result']['content'].strip()
            else:
                OutPut.outPut(f'[~]: 舔狗日记接口出了点小问题... ...')
                return None
        except Exception as e:
            msg = f'[-]: 舔狗日记API接口出现错误，错误信息：{e}'
            OutPut.outPut(msg)
            return None
        OutPut.outPut(f'[+]: 舔狗日记API接口调用成功！！！')
        return msg

    # 早安寄语
    def get_morning(self):
        OutPut.outPut('[*]: 正在调用早安寄语API接口... ...')
        url = self.Morning_Api.format(self.Key)
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['code'] != 200 and json_data['msg'] != 'success':
                msg = f'[~]: 早安寄语接口出现错误, 错误信息请查看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            content = json_data['result']['content']
            OutPut.outPut(f'[+]: 早安寄语API接口调用成功！！！')
            return content
        except Exception as e:
            msg = f'[-]: 早安寄语接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 毒鸡汤
    def get_soup(self):
        OutPut.outPut('[*]: 正在调用毒鸡汤API接口... ...')
        url = self.Chicken_Soup_Api.format(self.Key)
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['code'] != 200 and json_data['msg'] != 'success':
                msg = f'[~]: 毒鸡汤接口出现错误, 错误信息请查看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            content = json_data['result']['content']
            OutPut.outPut(f'[+]: 毒鸡汤API接口调用成功！！！')
            return content
        except Exception as e:
            msg = f'[-]: 毒鸡汤接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 讲笑话
    def get_joke(self):
        OutPut.outPut('[*]: 正在调用讲笑话API接口... ...')
        url = self.Joke_Api.format(self.Key)
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['success'] is not True:
                msg = f'[~]: 讲笑话接口出现错误, 错误信息请查看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            content = json_data['data']['content']
            OutPut.outPut(f'[+]: 讲笑话API接口调用成功！！！')
            return content
        except Exception as e:
            msg = f'[-]: 讲笑话接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 60s读懂世界
    def get_60s(self):
        current_time = time.time()
        while current_time + 30 > time.time():
            res = self.get_60s_by_request()
            if res and '微语' in res:
                return res

            res_request = self.get_60s_by_api()
            if res_request and '微语' in res_request:
                return res_request
            time.sleep(3)
        return None

    def get_60s_by_api(self):
        OutPut.outPut('[*]: 正在调用60s接口... ...')
        url = self.s60_Api
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['status'] != 200:
                msg = f'[~]: 60s接口出现错误, 错误信息请查看日志 ~~~~~~'
                return msg
            news_and_quotes = json_data['data']
            content = '每天60秒读懂世界\n'
            for item in news_and_quotes:
                content += item + '\n'
            OutPut.outPut(f'[+]: 60s接口调用成功！！！')
            return content
        except Exception as e:
            msg = f'[-]: 60s接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)

    @staticmethod
    def get_60s_by_request():
        OutPut.outPut('[*]: 正在调用new 60s接口... ...')
        try:
            url = 'https://www.zhihu.com/api/v4/columns/c_1715391799055720448/items'
            headers = {
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "accept-language": "zh-CN,zh;q=0.9",
                "sec-ch-ua": "\"Chromium\";v=\"110\", \"Not A(Brand\";v=\"24\", \"Google Chrome\";v=\"110\"",
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": "\"Android\"",
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"
            }
            res = requests.get(url, headers=headers, timeout=10)
            res_json = json.loads(res.text)
            print(res_json)
            content = res_json.get('data')[0].get('content')

            # 使用BeautifulSoup提取出所有p标签的内容
            soup = BeautifulSoup(content, 'html.parser')
            info = soup.find_all('p')
            result = [i.get_text().strip() for i in info if i.get_text().strip()]
            result = ['【秒懂世界】'] + result
            OutPut.outPut(f'[+]: new 60s接口调用成功！！！')
            return "\n".join(result)
        except Exception as e:
            print(e)
            msg = f'[-]: new 60s接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)

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
        url = self.get_60s_pic_url()
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
            return None

    # 看图猜成语
    def get_idiom(self):
        OutPut.outPut('[*]: 正在调用看图猜成语API接口... ...')
        idiom_data = self.get_idiom_data()
        # save_path = self.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.jpg'
        pic_name = idiom_data.get('答案', '未知')
        save_path = self.Pic_path + '/guess_idiom_image/' + pic_name + '.jpg'
        # save_path = self.Pic_path + '/guess_idiom_image/' + str(int(time.time() * 1000)) + '.jpg'
        try:
            url = idiom_data['图片链接']
            pic_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).content
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
                return None
            msg = json_data['result']
            OutPut.outPut(f'[+]: 谷歌翻译API接口调用成功！！！')
            OutPut.outPut(f'[+]: 翻译结果：{msg}')
            return msg
        except Exception as e:
            msg = f'[-]: 谷歌翻译接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 虎扑热搜
    def get_hupu(self):
        OutPut.outPut('[*]: 正在调用虎扑热搜API接口... ...')
        url = self.Hupu_Api
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['success'] is False:
                msg = f'[~]: 虎扑热搜接口出现错误, 错误信息请查看日志 ~~~~~~'
                return msg
            hot_search = json_data['data']
            if not hot_search:
                return None

            content_lst = []
            queue1 = hot_search[:len(hot_search) // 2]
            queue2 = hot_search[len(hot_search) // 2:]
            # 分别处理两个队列
            for i, queue_data in enumerate([queue1, queue2]):
                start_index = i * (len(hot_search) // 2)
                end_index = start_index + len(queue_data)
                content = f'虎扑热搜 {start_index + 1}-{end_index}\n'
                for index, item in enumerate(queue_data):
                    content += f'{start_index + index + 1}、{item["title"]}\n{item["url"]}\n'
                content_lst.append(content)
            OutPut.outPut(f'[+]: 虎扑热搜API接口调用成功！！！')
            return content_lst
        except Exception as e:
            msg = f'[-]: 虎扑热搜接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)

    # 神回复
    def get_god_reply(self):
        OutPut.outPut('[*]: 正在调用神回复API接口... ...')
        url = "https://api.yujn.cn/api/shf.php?"
        try:
            content = requests.get(url=url, headers=self.headers, timeout=30, verify=False).text
            OutPut.outPut(f'[+]: 神回复API接口调用成功！！！')
            return content.replace('<br>', '\n')
        except Exception as e:
            url = "https://api.52hyjs.com/api/shenhuifu"
            try:
                json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
                content = json_data['0']['shenhuifu']
                OutPut.outPut(f'[+]: 神回复API接口调用成功！！！')
                return content.replace('<br>', '\n')
            except Exception as e:
                return None

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

            # 使用正则表达式进行解析
            pattern = r'±img=(?P<img>.*?)±\s*歌名：(?P<歌名>.*?)\s*歌手：(?P<歌手>.*?)\s*歌曲详情页：(?P<歌曲详情页>.*?)\s*播放链接：(?P<播放链接>.*)'

            match = re.match(pattern, content)
            if match:
                data_dict = match.groupdict()
                # 打印字典
                print(data_dict)
            else:
                print("无法解析字符串为字典格式")
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

    # 内涵段子
    def get_duanzi(self):
        OutPut.outPut(f'[*]: 正在调用内涵段子接口... ...')
        try:
            url = "https://dayu.qqsuu.cn/neihanduanzi/apis.php?type=json"
            res = requests.get(url=url, timeout=30, verify=False)
            json_data = res.json()
            url_pic = json_data['data']

            pic_data = requests.get(url=url_pic, headers=self.headers, timeout=30, verify=False).content
            save_path = self.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.png'
            with open(file=save_path, mode='wb') as pd:
                pd.write(pic_data)
        except Exception as e:
            msg = f'[-]: 内涵段子API接口出现错误，错误信息：{e}'
            OutPut.outPut(msg)
            return None
        OutPut.outPut(f'[+]: 内涵段子API接口调用成功！！！')
        return save_path

    # 搞笑段子
    @staticmethod
    def get_duanzi_text():
        OutPut.outPut('[*]: 正在调用搞笑段子API接口... ...')
        url = "https://api.pearktrue.cn/api/random/duanzi/?type=json"
        try:
            json_data = requests.get(url=url, timeout=30, verify=False).json()
            if json_data['code'] != 200:
                msg = '[~]: 搞笑段子接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            msg = json_data['duanzi'].replace('<br>', '\n')
            OutPut.outPut(f'[+]: 搞笑段子API接口调用成功！！！')
            return msg
        except Exception as e:
            msg = f'[-]: 搞笑段子接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

    # 喜加一
    def get_steam_plus_one(self):
        OutPut.outPut('[*]: 正在调用喜加一API接口... ...')
        url = "https://api.pearktrue.cn/api/steamplusone/?type=json"
        try:
            json_data = requests.get(url=url, headers=self.headers, timeout=30, verify=False).json()
            print(json_data)
            if json_data['code'] != 200:
                msg = '[~]: 喜加一接口出现错误，具体原因请看日志 ~~~~~~'
                OutPut.outPut(msg)
                return None
            msg_list = []
            game_list = json_data['data']
            for game in game_list:
                msg = f"游戏平台：{game['source']}\n" \
                      f"游戏名称：{game['name']}\n" \
                      f"领取时间：{game['starttime']}至{game['endtime']}\n" \
                      f"游戏链接：{game['url']}"
                msg_list.append(msg)
                detail = self.get_metaso(game['name'], 'detail')
                if detail is not None:
                    msg_list.append(detail.replace('\n\n', '\n'))
            OutPut.outPut(f'[+]: 喜加一API接口调用成功！！！')
            return msg_list
        except Exception as e:
            msg = f'[-]: 喜加一接口出现错误, 错误信息：{e}'
            OutPut.outPut(msg)
            return None

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

    # 生成表情
    @staticmethod
    def magic_emoji_by_head(head):
        emoji_path = generate_random_meme_by_jpg(head)
        return emoji_path

    # 生成表情
    @staticmethod
    def magic_emoji_by_head_and_emoji(head, emoji, texts=None, head2=None):
        meme_file = generate_meme(head, emoji, texts=texts, filename2=head2)
        return meme_file


if __name__ == '__main__':
    Ams = Api_Main_Server(1)
    # print(Ams.query_weather('天气查询 南昌'))
    print(Ams.get_dog())
    # # Ams.get_constellation('运势查询 白羊')
    # print(Ams.get_morning())
    print(Ams.get_soup())
    # print(Ams.search_image("taylor"))
    # # print(Ams.get_whois('whois查询 qq.com'))
    # # print(Ams.get_attribution('归属查询 121264'))
    # # print(Ams.get_icp('备案查询 qzzz2131231q.com'))
    # # print(Ams.get_metaso('The Falconeer: Standard Edition', "detail"))
    # # print(Ams.search_song('大象'))
    # info = Ams.parse_song_url('https://www.hhlqilongzhu.cn/api/dg_kugouSQ.php?msg=%E5%91%A8%E6%9D%B0%E4%BC%A6&n=1')
    # print(Ams.download_song(info))
