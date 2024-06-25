import os
import random
import re
import threading
import time
import xml.etree.ElementTree as ET
from threading import Thread

import requests
import yaml

from Api_Server.Api_Main_Server import Api_Main_Server
from Db_Server.Db_Main_Server import Db_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from OutPut import OutPut


class Room_Msg_Dispose:
    def __init__(self, wcf):
        self.wcf = wcf
        # 实例化数据操作类
        self.Dms = Db_Main_Server(wcf=self.wcf)
        # 实例化积分数据类
        self.Dps = Db_Point_Server()

        # 实例化API类
        self.Ams = Api_Main_Server(wcf=self.wcf)

        # 读取配置文件
        self.current_path = os.path.dirname(__file__)
        config = yaml.load(open(self.current_path + '/../config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.system_copyright = config['System_Config']['System_Copyright']

        self.administrators = config['Administrators']
        self.Add_Admin_KeyWords = config['Admin_Function_Word']['Add_Admin_Word']
        self.Del_Admin_KeyWords = config['Admin_Function_Word']['Del_Admin_Word']
        self.Add_Push_KeyWords = config['Admin_Function_Word']['Add_White_Word']
        self.Del_Push_KeyWords = config['Admin_Function_Word']['Del_White_Word']
        self.Add_WhiteRoom_Words = config['Admin_Function_Word']['Add_WhiteRoom_Word']
        self.Del_WhiteRoom_Words = config['Admin_Function_Word']['Del_WhiteRoom_Word']
        self.Add_BlackRoom_Words = config['Admin_Function_Word']['Add_BlackRoom_Word']
        self.Del_Black_Room_Words = config['Admin_Function_Word']['Del_BlackRoom_Word']
        self.Del_User_Words = config['Admin_Function_Word']['Del_User_Word']
        self.Del_WhiteGh_Words = config['Admin_Function_Word']['Del_WhiteGh_Word']

        self.Pic_Words = config['Function_Key_Word']['Pic_Word']
        self.Video_Words = config['Function_Key_Word']['Video_Word']
        self.Icp_Words = config['Function_Key_Word']['Icp_Word']
        self.Attribution_Words = config['Function_Key_Word']['Attribution_Word']
        self.Kfc_Words = config['Function_Key_Word']['Kfc_Word']
        self.Whois_Words = config['Function_Key_Word']['Whois_Word']
        self.Fish_Words = config['Function_Key_Word']['Fish_Word']
        self.Weather_Words = config['Function_Key_Word']['Weather_Word']
        self.Dog_Words = config['Function_Key_Word']['Dog_Word']
        self.Constellation_Words = config['Function_Key_Word']['Constellation_Word']
        self.Dream_Words = config['Function_Key_Word']['Dream_Word']
        self.ThreatBook_Words = config['Function_Key_Word']['ThreatBook_Word']
        self.Morning_Words = config['Function_Key_Word']['Morning_Word']
        self.Morning_Page_Words = config['Function_Key_Word']['Morning_Page_Word']
        self.Evening_Page_Words = config['Function_Key_Word']['Evening_Page_Word']
        self.Custom_Key_Words = config['Custom_KeyWord']
        self.Md5_Words = config['Function_Key_Word']['Md5_Words']
        self.Port_Scan_Words = config['Function_Key_Word']['Port_Scan_Word']
        self.HelpMenu_Words = config['Function_Key_Word']['Help_Menu']
        self.Poison_Chicken_Soup_Words = config['Function_Key_Word']['Poison_Chicken_Soup_Word']
        self.Joke_Words = config['Function_Key_Word']['Joke_Word']
        self.s60_Words = config['Function_Key_Word']['60s_Word']
        self.Hupu_Words = config['Function_Key_Word']['Hupu_Word']
        self.GPT_Words = config['Function_Key_Word']['GPT_Word']
        self.Spark_Words = config['Function_Key_Word']['Spark_Word']
        self.Metaso_Words = config['Function_Key_Word']['Metaso_Word']

        self.Sign_Words = config['Point_Config']['Sign']['Word']
        self.Query_Point_Words = config['Point_Config']['Query_Point_Word']
        self.Add_Point_Words = config['Point_Config']['Add_Point_Word']
        self.Del_Point_Words = config['Point_Config']['Del_Point_Word']
        self.Send_Point_Words = config['Point_Config']['Send_Point_Word']
        self.Md5_Point = config['Point_Config']['Function_Point']['Md5']
        self.Ip_Point = config['Point_Config']['Function_Point']['IP']
        self.Ai_Point = config['Point_Config']['Function_Point']['Ai_point']
        self.Port_Scan_Point = config['Point_Config']['Function_Point']['Port_Scan']

        # 管理员模式
        self.manager_mode_rooms = {}
        # 游戏模式
        self.game_mode_rooms = {}
        self.game_point = {}
        self.game_answer = {}
        self.game_success = {}
        self.idiom_pic = {}
        self.idiom_usr_answer = {}
        # 创建一个线程锁
        self.counter_lock = threading.Lock()

    # 主消息处理
    def Msg_Dispose(self, msg):
        at_user_lists = []
        # 获取所在群所有管理员
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        # 获取所有白名单群聊
        whiteRooms_dicts = self.Dms.show_white_rooms()
        # 获取所有黑名单群聊
        blackRooms_dicts = self.Dms.show_black_rooms()
        # 处理@消息
        if '@' in msg.content and msg.type == 1:
            at_user_lists = self.get_at_wx_id(msg.xml)
        # 超级管理员功能
        if msg.sender in self.administrators:
            Thread(target=self.Administrator_Function, name="超级管理员处理流程", args=(msg, at_user_lists,)).start()
            return
        # 管理员功能
        elif msg.sender in admin_dicts.keys():
            Thread(target=self.Admin_Function, name="管理员处理流程", args=(msg, at_user_lists)).start()
            return
        # 管理员模式下，屏蔽所有非管理员消息
        elif self.manager_mode_rooms.get(msg.roomid, False):
            return
        # 白名单群聊功能
        elif msg.roomid in whiteRooms_dicts.keys():
            Thread(target=self.WhiteRoom_Function, name="白名单群聊处理流程", args=(msg, at_user_lists)).start()
            return
        # 黑名单群聊功能
        elif msg.roomid in blackRooms_dicts.keys():
            Thread(target=self.BlackRoom_Function, name="黑名单群聊处理流程", args=(msg, at_user_lists)).start()
            return
        # 普通群聊功能
        else:
            Thread(target=self.OrdinaryRoom_Function, name="普通群聊处理流程", args=(msg, at_user_lists)).start()
            return

    def Administrator_Function(self, msg, at_user_lists):
        # 新增管理员流程
        if self.judge_keyword(keyword=self.Add_Admin_KeyWords, msg=msg.content, list_bool=True, in_bool=True):
            Thread(target=self.add_admin, name="新增管理员", args=(msg.sender, at_user_lists, msg.roomid,)).start()
        # 删除管理员流程
        elif self.judge_keyword(keyword=self.Del_Admin_KeyWords, msg=msg.content, list_bool=True, in_bool=True):
            Thread(target=self.del_admin, name="删除管理员", args=(msg.sender, at_user_lists, msg.roomid,)).start()
        self.Admin_Function(msg, at_user_lists)

    # 管理员功能
    def Admin_Function(self, msg, at_user_lists):
        # 开启推送服务
        if self.judge_keyword(keyword=self.Add_Push_KeyWords, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.add_push_room, name="添加推送群聊", args=(msg.sender, msg.roomid,)).start()
        # 关闭推送服务
        elif self.judge_keyword(keyword=self.Del_Push_KeyWords, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_push_room, name="移除推送群聊", args=(msg.sender, msg.roomid,)).start()
        # 添加白名单群聊
        elif self.judge_keyword(keyword=self.Add_WhiteRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.add_white_room, name="添加白名单群聊", args=(msg.sender, msg.roomid,)).start()
        # 移除白名单群聊
        elif self.judge_keyword(keyword=self.Del_WhiteRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_white_room, name="移除白名单群聊", args=(msg.sender, msg.roomid,)).start()
        # 添加黑名单群聊
        elif self.judge_keyword(keyword=self.Add_BlackRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.add_black_room, name="添加黑名单群聊", args=(msg.sender, msg.roomid,)).start()
        # 移除黑名单群聊
        elif self.judge_keyword(keyword=self.Del_Black_Room_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_black_room, name="移除黑名单群聊", args=(msg.sender, msg.roomid,)).start()
        # 把人移出群聊
        elif self.judge_keyword(keyword=self.Del_User_Words, msg=self.handle_atMsg(msg, at_user_lists), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_user, name="把人移出群聊", args=(msg.sender, msg.roomid, at_user_lists,)).start()
        # 移除白名单公众号
        elif self.judge_keyword(keyword=self.Del_WhiteGh_Words, msg=self.handle_xml_msg(msg), list_bool=True,
                                equal_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.del_white_gh, name="移除白名单公众号", args=(msg,)).start()
        # 增加用户积分
        elif self.judge_keyword(keyword=self.Add_Point_Words, msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True,
                                split_bool=True):
            Thread(target=self.Add_Point, name="增加积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
        # 减少用户积分
        elif self.judge_keyword(keyword=self.Del_Point_Words, msg=self.handle_atMsg(msg, at_user_lists), list_bool=True,
                                split_bool=True):
            Thread(target=self.Del_Point, name="减少积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
        # 早报
        elif self.judge_keyword(keyword=self.Morning_Page_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            send_msg = self.Ams.get_freebuf_news()
            self.wcf.send_text(msg=send_msg, receiver=msg.roomid)
        # 晚报
        elif self.judge_keyword(keyword=self.Evening_Page_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            send_msg = self.Ams.get_safety_news()
            self.wcf.send_text(msg=send_msg, receiver=msg.roomid)
        # 添加白名单公众号
        elif msg.type == 49:
            Thread(target=self.add_white_gh, name="添加白名单公众号", args=(msg,)).start()
        # 积分限制功能
        elif msg.content.strip() in ['取消积分限制', '取消积分', '取消限制', '关闭积分限制', '关闭积分', '关闭限制']:
            self.Ai_Point = 0
            self.wcf.send_text(msg='关闭积分限制成功', receiver=msg.roomid, aters=msg.sender)
        elif msg.content.strip() in ['开启积分限制', '开启积分', '开启限制']:
            self.Ai_Point = 10
            self.wcf.send_text(msg='开启积分限制成功', receiver=msg.roomid, aters=msg.sender)
        elif msg.content.strip() in ['开启管理员模式', '管理员模式']:
            self.manager_mode_rooms[msg.roomid] = True
            self.wcf.send_text(msg=f'管理员模式开启成功，仅响应管理员消息', receiver=msg.roomid, aters=msg.sender)
        elif msg.content.strip() in ['关闭管理员模式', '取消管理员模式', '退出管理员模式', '普通模式']:
            self.manager_mode_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'管理员模式关闭成功，恢复正常消息响应', receiver=msg.roomid, aters=msg.sender)
        Thread(target=self.OrdinaryRoom_Function, name="普通群聊功能", args=(msg, at_user_lists)).start()

    # 白名单群聊功能
    def WhiteRoom_Function(self, msg, at_user_lists):
        # 检测广告自动踢出
        white_ids = ['57']
        if msg.type == 49 and (self.handle_xml_type(msg) not in white_ids):
            Thread(target=self.detecting_advertisements, name="检测广告自动踢出", args=(msg,)).start()
        Thread(target=self.OrdinaryRoom_Function, name="普通群聊功能", args=(msg, at_user_lists)).start()

    # 黑名单群聊功能
    def BlackRoom_Function(self, msg, at_user_lists):
        Thread(target=self.Point_Function, name="积分功能", args=(msg, at_user_lists)).start()

    # 普通群聊功能
    def OrdinaryRoom_Function(self, msg, at_user_lists):
        Thread(target=self.Happy_Function, name="娱乐功能", args=(msg,)).start()
        Thread(target=self.Point_Function, name="积分功能", args=(msg, at_user_lists,)).start()

    # 娱乐功能
    def Happy_Function(self, msg):
        if self.game_mode_rooms.get(msg.roomid, False):
            self.gaming_function(msg)
            return
        if self.game_function(msg):
            return
        # 美女图片
        if self.judge_keyword(keyword=self.Pic_Words, msg=msg.content, list_bool=True, equal_bool=True):
            save_path = self.Ams.get_girl_pic()
            if 'Pic_Cache' in save_path:
                self.wcf.send_image(path=save_path, receiver=msg.roomid)
            else:
                self.wcf.send_text(msg='美女图片接口出错, 错误信息请查看日志 ~~~~~~', receiver=msg.roomid)
        # 美女视频
        elif self.judge_keyword(keyword=self.Video_Words, msg=msg.content, list_bool=True, equal_bool=True):
            save_path = self.Ams.get_girl_video()
            if 'Video_Cache' in save_path:
                self.wcf.send_file(path=save_path, receiver=msg.roomid)
            else:
                self.wcf.send_text(msg='美女视频接口出错, 错误信息请查看日志 ~~~~~~', receiver=msg.roomid)
        # 天气查询
        elif self.judge_keyword(keyword=self.Weather_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            weather_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.query_weather(
                msg.content.strip())
            self.wcf.send_text(msg=weather_msg, receiver=msg.roomid, aters=msg.sender)
        # 舔狗日记
        elif self.judge_keyword(keyword=self.Dog_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            dog_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_dog()
            self.wcf.send_text(msg=dog_msg, receiver=msg.roomid, aters=msg.sender)
        # # 星座查询
        # elif self.judge_keyword(keyword=self.Constellation_Words, msg=msg.content.strip(), list_bool=True,
        #                         split_bool=True):
        #     constellation_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}' + self.Ams.get_constellation(
        #         msg.content)
        #     self.wcf.send_text(msg=constellation_msg, receiver=msg.roomid, aters=msg.sender)
        # 早安寄语
        elif self.judge_keyword(keyword=self.Morning_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            morning_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_morning()
            self.wcf.send_text(msg=morning_msg, receiver=msg.roomid, aters=msg.sender)
            # try:
            #     self.wcf.send_image(path=self.Ams.Pic_path+'/daily.gif', receiver=msg.roomid)
            # except Exception as e:
            #     print(f'早安寄语图片发送失败, 错误信息: {e}')
        # 毒鸡汤
        elif self.judge_keyword(keyword=self.Poison_Chicken_Soup_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            poison_chicken_soup_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_soup()
            self.wcf.send_text(msg=poison_chicken_soup_msg, receiver=msg.roomid, aters=msg.sender)
        # 讲笑话
        elif self.judge_keyword(keyword=self.Joke_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            joke_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_joke()
            self.wcf.send_text(msg=joke_msg, receiver=msg.roomid, aters=msg.sender)
        # 60s
        elif self.judge_keyword(keyword=self.s60_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            s60_msg = self.Ams.get_60s()
            if s60_msg:
                self.wcf.send_text(msg=s60_msg, receiver=msg.roomid, aters=msg.sender)
        elif self.judge_keyword(keyword=["60s图片", "60pic", "60spic"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            save_path = self.Ams.get_60s_pic()
            if save_path:
                self.wcf.send_image(path=save_path, receiver=msg.roomid)
            else:
                self.wcf.send_text(msg='60s图片接口出错, 错误信息请查看日志 ~~~~~~', receiver=msg.roomid)
        # 虎扑热搜
        elif self.judge_keyword(keyword=self.Hupu_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            hupu_msg = self.Ams.get_hupu()
            if hupu_msg is None:
                self.wcf.send_text(msg='未获取到虎扑热搜数据', receiver=msg.roomid)
                return
            self.wcf.send_text(msg=hupu_msg[0], receiver=msg.roomid, aters=msg.sender)
            self.wcf.send_text(msg=hupu_msg[1], receiver=msg.roomid, aters=msg.sender)
        # 摸鱼日记
        elif self.judge_keyword(keyword=self.Fish_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            save_path = self.Ams.get_fish()
            ret = f'[*]: 摸鱼日记API接口返回值：{save_path}'
            OutPut.outPut(ret)
            if 'Fish_Cache' in save_path:
                # TODO: send_image() 图片有概率会发送不成功，怀疑是微信客户端安装在虚拟机中导致
                self.wcf.send_image(path=save_path, receiver=msg.roomid)
            else:
                self.wcf.send_text(msg='摸鱼日记接口出错, 错误信息请查看日志 ~~~~~~', receiver=msg.roomid)
        # 点歌功能
        elif self.judge_keyword(keyword=["点歌", "听歌"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            music_name = msg.content.strip().split(' ', 1)[1].strip()
            digest = '搜索歌曲：{}'.format(music_name)
            url = 'https://tool.liumingye.cn/music/#/search/M/song/{}'.format(music_name)
            self.send_music_message(digest, url, msg.roomid)
        elif msg.content.strip() in ["点歌", "听歌"]:
            digest = '点击进入点歌页面'
            url = 'https://tool.liumingye.cn/music/'
            self.send_music_message(digest, url, msg.roomid)
        # 成语解析功能
        elif self.judge_keyword(keyword=["成语解析", "成语解释", "成语查询"], msg=msg.content.strip(), list_bool=True,
                                split_bool=True):
            idiom_name = msg.content.strip().split(' ', 1)[1].strip()
            idiom_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' \
                        + self.Ams.get_idiom_explain(idiom_name)
            self.wcf.send_text(msg=idiom_msg, receiver=msg.roomid, aters=msg.sender)
        # 接口不稳定，暂时关闭
        # elif msg.content.strip().upper() in ["COS", "COSPLAY"]:
        #     save_path = self.Ams.get_cosplay_video()
        #     if save_path:
        #         self.wcf.send_file(path=save_path, receiver=msg.roomid)
        #     else:
        #         self.wcf.send_text(msg='COSPLAY接口出错, 错误信息请查看日志 ~~~~~~', receiver=msg.roomid)

        # # Whois查询
        # elif self.judge_keyword(keyword=self.Whois_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     whois_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_whois(
        #         msg.content.strip())
        #     self.wcf.send_text(msg=whois_msg, receiver=msg.roomid, aters=msg.sender)
        # # 归属地查询
        # elif self.judge_keyword(keyword=self.Attribution_Words, msg=msg.content.strip(), list_bool=True,
        #                         split_bool=True):
        #     attribution_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_attribution(
        #         msg.content.strip())
        #     self.wcf.send_text(msg=attribution_msg, receiver=msg.roomid, aters=msg.sender)
        # # 备案查询
        # elif self.judge_keyword(keyword=self.Icp_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     attribution_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_icp(
        #         msg.content.strip())
        #     self.wcf.send_text(msg=attribution_msg, receiver=msg.roomid, aters=msg.sender)
        # 疯狂星期四文案
        elif self.judge_keyword(keyword=self.Kfc_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            kfc_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_kfc().replace(
                '\\n', '\n')
            self.wcf.send_text(msg=kfc_msg, receiver=msg.roomid, aters=msg.sender)
        # # 周公解梦
        # elif self.judge_keyword(keyword=self.Dream_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     dream_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' + self.Ams.get_dream(
        #         msg.content.strip())
        #     self.wcf.send_text(msg=dream_msg, receiver=msg.roomid, aters=msg.sender)
        # help帮助菜单
        elif self.judge_keyword(keyword=self.HelpMenu_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.get_help, name="Help帮助菜单", args=(msg,)).start()
        # # 自定义回复
        # Thread(target=self.custom_get, name="自定义回复", args=(msg,)).start()

    # 积分功能
    def Point_Function(self, msg, at_user_lists):
        # 签到功能
        if msg.content.strip() == '签到':
            sign_word = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}' + f'签到口令已改为：{self.Sign_Words}'
            self.wcf.send_text(msg=sign_word, receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() == self.Sign_Words:
            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
            room_name = self.Dms.query_room_name(room_id=msg.roomid)
            sign_msg = f'@{wx_name}\n'
            sign_msg += self.Dps.sign(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name)
            self.wcf.send_text(msg=sign_msg, receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['重新发送图片', '重新发送', '重发图片']:
            self.wcf.send_image(path=self.save_path, receiver=msg.roomid)
        # 赠送积分功能
        elif self.judge_keyword(keyword=self.Send_Point_Words, msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True, split_bool=True):
            Thread(target=self.send_point, name="赠送积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            return
        # # Md5查询
        # elif self.judge_keyword(keyword=self.Md5_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     Thread(target=self.get_md5, name="Md5查询", args=(msg,)).start()
        # # 微步IP查询
        # elif self.judge_keyword(keyword=self.ThreatBook_Words, msg=msg.content.strip(), list_bool=True,
        #                         split_bool=True):
        #     Thread(target=self.get_ip, name="IP查询", args=(msg,)).start()
        # # 端口查询
        # elif self.judge_keyword(keyword=self.Port_Scan_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     Thread(target=self.get_port, name="端口查询", args=(msg,)).start()
        # 拒绝者
        elif self.judge_keyword(keyword=['拒绝者'], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.get_xiuren_pic, name="积分查询", args=(msg,)).start()
            return
        # 积分查询
        elif self.judge_keyword(keyword=self.Query_Point_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.query_point, name="积分查询", args=(msg,)).start()
            return
        # GPT对话
        elif self.judge_keyword(keyword=self.GPT_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            Thread(target=self.get_ai, name="GPT对话", args=(msg, at_user_lists, 'gpt')).start()
            return
        # 星火对话
        elif self.judge_keyword(keyword=self.Spark_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            Thread(target=self.get_ai, name="星火对话", args=(msg, at_user_lists, 'xh')).start()
            return
        # 秘塔搜索
        elif self.judge_keyword(keyword=self.Metaso_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            Thread(target=self.get_ai, name="秘塔搜索", args=(msg, at_user_lists, 'metaso')).start()
            return
        elif ' ' in msg.content.strip() and msg.content.strip().split(' ')[0] in ['秘塔搜索', '秘塔AI搜索']:
            question = msg.content.strip().split(' ', 1)[1]
            self.wcf.send_rich_text(name='搜索',
                                    account='',
                                    title='秘塔AI搜索',
                                    digest=question,
                                    url='https://metaso.cn/?q=%s' % question,
                                    thumburl='https://metaso.cn/apple-touch-icon.png',
                                    receiver=msg.roomid)
            return
        # 文生图
        elif self.judge_keyword(
                keyword=['画', '画画', '画图', '绘画', 'ai画画', 'Ai画画', 'AI画画', 'ai绘画', 'Ai绘画', 'AI绘画',
                         '文生图'],
                msg=msg.content.strip(), list_bool=True, split_bool=True):
            Thread(target=self.get_ai, name="Spark文生图", args=(msg, at_user_lists, 'image')).start()
            return
        # Ai对话
        elif self.wcf.self_wxid in at_user_lists and '所有人' not in msg.content:
            Thread(target=self.get_ai, name="Ai对话", args=(msg, at_user_lists)).start()
            return

    def game_function(self, msg):
        if self.judge_keyword(keyword=["看图猜成语"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.start_guess_idiom_image, name="看图猜成语", args=(msg,)).start()
            return True
        elif self.judge_keyword(keyword=["成语接龙"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.start_idiom_chain, name="猜成语", args=(msg,)).start()
            return True

    def gaming_function(self, msg):
        if self.judge_keyword(keyword=["退出游戏"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            self.game_mode_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'游戏已中止！', receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["重发"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            self.wcf.send_image(path=self.idiom_pic[msg.roomid], receiver=msg.roomid)
            return
        else:
            if self.game_mode_rooms.get(msg.roomid, False) == "guess_idiom_image":
                try:
                    with self.counter_lock:
                        if self.game_success.get(msg.roomid, False):
                            return
                        if self.judge_keyword(keyword=[self.game_answer[msg.roomid].get('答案', '')],
                                              msg=msg.content.strip(), list_bool=True, equal_bool=True):
                            self.game_success[msg.roomid] = True
                            self.game_answer[msg.roomid] = None
                            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
                            # 如果获取不到群昵称，则获取微信昵称
                            if not wx_name:
                                wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
                            self.wcf.send_text(msg=f'恭喜{wx_name}答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_name in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_name] += 1
                                else:
                                    self.game_point[msg.roomid][wx_name] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_name: 1}
                except Exception as e:
                    print(e)
            elif self.game_mode_rooms.get(msg.roomid, False) == "idiom_chain":
                try:
                    with self.counter_lock:
                        if self.game_success.get(msg.roomid, False):
                            return
                        if self.judge_keyword(keyword=self.game_answer[msg.roomid],
                                              msg=msg.content.strip(), list_bool=True, equal_bool=True):
                            self.game_success[msg.roomid] = True
                            self.game_answer[msg.roomid] = None
                            self.idiom_usr_answer[msg.roomid] = msg.content.strip()
                            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
                            # 如果获取不到群昵称，则获取微信昵称
                            if not wx_name:
                                wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
                            self.wcf.send_text(msg=f'恭喜{wx_name}接龙成功！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_name in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_name] += 1
                                else:
                                    self.game_point[msg.roomid][wx_name] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_name: 1}
                except Exception as e:
                    print(e)

    def start_guess_idiom_image(self, msg):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n看图猜成语游戏开始，总共五轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。'
                               f'\n如果未成功收到图片，'
                               f'\n请回复“重发”。',
                           receiver=msg.roomid, aters=msg.sender)
        self.game_mode_rooms[msg.roomid] = "guess_idiom_image"
        try:
            for i in range(5):
                if not self.game_mode_rooms.get(msg.roomid, False):
                    # 清空游戏数据
                    self.game_mode_rooms[msg.roomid] = False
                    self.game_point[msg.roomid] = {}
                    self.game_answer[msg.roomid] = None
                    self.game_success[msg.roomid] = False
                    self.idiom_pic[msg.roomid] = None
                    return
                save_path, idiom_data = self.Ams.get_idiom()
                self.idiom_pic[msg.roomid] = save_path
                self.game_answer[msg.roomid] = idiom_data
                self.wcf.send_image(path=save_path, receiver=msg.roomid)
                self.wcf.send_text(msg=f'第{i + 1}轮题目：', receiver=msg.roomid)
                self.wcf.send_text(msg='请在六十秒内回答，否则将跳过此题', receiver=msg.roomid)
                cur_time = time.time()
                while time.time() - cur_time < 61:
                    if not self.game_mode_rooms.get(msg.roomid, False):
                        # 清空游戏数据
                        self.game_mode_rooms[msg.roomid] = False
                        self.game_point[msg.roomid] = {}
                        self.game_answer[msg.roomid] = None
                        self.game_success[msg.roomid] = False
                        self.idiom_pic[msg.roomid] = None
                        return
                    if self.game_success.get(msg.roomid, False):
                        break
                    time.sleep(0.5)
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                    self.wcf.send_text(msg='回答正确！', receiver=msg.roomid)
                else:
                    self.wcf.send_text(msg='没有人回答正确！', receiver=msg.roomid)
                answer = f"答案：{idiom_data.get('答案', '')}\n" \
                         f"拼音：{idiom_data.get('拼音', '')}\n" \
                         f"解释：{idiom_data.get('解释', '')}\n" \
                         f"出处：{idiom_data.get('出处', '')}\n" \
                         f"例句：{idiom_data.get('例句', '')}"
                self.wcf.send_text(msg=answer, receiver=msg.roomid)
                time.sleep(0.7)
            msg_over = ["游戏结束！"]
            if msg.roomid in self.game_point.keys():
                for wx_name, point in self.game_point[msg.roomid].items():
                    msg_over.append(f"{wx_name}：{point} 分")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[~]: 猜词游戏出问题了 :{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False
            self.idiom_pic[msg.roomid] = None

    # 成语接龙
    def start_idiom_chain(self, msg):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n成语接龙游戏开始，总共十轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。',
                           receiver=msg.roomid, aters=msg.sender)
        self.game_mode_rooms[msg.roomid] = "idiom_chain"
        try:
            pinyin_lst = ['a', 'an', 'ang', 'ao', 'ba', 'bai', 'ban', 'bang', 'bao', 'bei', 'ben', 'beng', 'bi', 'bian',
                          'biao', 'bie', 'bin', 'bing', 'bo', 'bu', 'ca', 'cai', 'can', 'cang', 'cao', 'ce', 'cen',
                          'ceng',
                          'cha', 'chai', 'chan', 'chang', 'chao', 'che', 'chen', 'cheng', 'chi', 'chong', 'chou', 'chu',
                          'chuai', 'chuan', 'chuang', 'chui', 'chun', 'chuo', 'ci', 'cong', 'cu', 'cuan', 'cui', 'cun',
                          'cuo', 'da', 'dai', 'dan', 'dang', 'dao', 'de', 'deng', 'di', 'dian', 'diao', 'die', 'ding',
                          'diu', 'dong', 'dou', 'du', 'duan', 'dui', 'dun', 'duo', 'e', 'en', 'er', 'fa', 'fan', 'fang',
                          'fei', 'fen', 'feng', 'fo', 'fu', 'ga', 'gai', 'gan', 'gang', 'gao', 'ge', 'gen', 'geng',
                          'gong',
                          'gou', 'gu', 'gua', 'guai', 'guan', 'guang', 'gui', 'gun', 'guo', 'hai', 'han', 'hang', 'hao',
                          'he', 'hei', 'hen', 'heng', 'hong', 'hou', 'hu', 'hua', 'huai', 'huan', 'huang', 'hui', 'hun',
                          'huo', 'ji', 'jia', 'jian', 'jiang', 'jiao', 'jie', 'jin', 'jing', 'jiong', 'jiu', 'ju',
                          'juan',
                          'jue', 'jun', 'kai', 'kan', 'kang', 'kao', 'ke', 'ken', 'keng', 'kong', 'kou', 'ku', 'kua',
                          'kuai', 'kuan', 'kuang', 'kui', 'kun', 'kuo', 'la', 'lai', 'lan', 'lang', 'lao', 'le', 'lei',
                          'leng', 'li', 'lian', 'liang', 'liao', 'lie', 'lin', 'ling', 'liu', 'long', 'lou', 'lu',
                          'luan',
                          'lun', 'luo', 'lv', 'lve', 'ma', 'mai']
            pinyin = random.choice(pinyin_lst)
            idiom_lst = self.Ams.db_idiom.get_words_by_first(pinyin)
            idiom = random.choice(idiom_lst)

            for i in range(10):
                if not self.game_mode_rooms.get(msg.roomid, False):
                    # 清空游戏数据
                    self.game_mode_rooms[msg.roomid] = False
                    self.game_point[msg.roomid] = {}
                    self.game_answer[msg.roomid] = None
                    self.game_success[msg.roomid] = False
                    self.idiom_usr_answer[msg.roomid] = None
                    return
                answers = self.Ams.db_idiom.get_words_by_word(idiom)
                if not answers:
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                self.game_answer[msg.roomid] = answers
                self.wcf.send_text(msg=f'第{i + 1}轮题目：【{idiom}】', receiver=msg.roomid)
                self.wcf.send_text(msg='请在六十秒内回答，否则结束游戏', receiver=msg.roomid)
                cur_time = time.time()
                while time.time() - cur_time < 61:
                    if not self.game_mode_rooms.get(msg.roomid, False):
                        # 清空游戏数据
                        self.game_mode_rooms[msg.roomid] = False
                        self.game_point[msg.roomid] = {}
                        self.game_answer[msg.roomid] = None
                        self.game_success[msg.roomid] = False
                        self.idiom_usr_answer[msg.roomid] = None
                        return
                    if self.game_success.get(msg.roomid, False):
                        break
                    time.sleep(0.5)
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    self.wcf.send_text(msg='没有人接龙成功！', receiver=msg.roomid)
                    break
                usr_answer = self.idiom_usr_answer[msg.roomid]
                idiom_lst = self.Ams.db_idiom.get_words_by_word(usr_answer)
                idiom = random.choice(idiom_lst)
                time.sleep(0.3)
            msg_over = ["游戏结束！"]
            if msg.roomid in self.game_point.keys():
                for wx_name, point in self.game_point[msg.roomid].items():
                    msg_over.append(f"{wx_name}：{point} 分")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[~]: 成语接龙游戏出问题了：{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False
            self.idiom_usr_answer[msg.roomid] = None

    # 积分查询
    def query_point(self, msg):
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name)
        send_msg = f'@{wx_name} 您当前剩余积分: {point}\n还望好好努力，平时舔舔管理员 让管理给你施舍点'
        self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 自定义回复
    def custom_get(self, msg):
        for key, values in self.Custom_Key_Words.items():
            for value in values:
                if value == msg.content.strip():
                    OutPut.outPut(f'[+]: 调用自定义回复成功！！！')
                    send_msg = key.replace('\\n', '\n')
                    self.wcf.send_text(
                        msg=f'@{self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)} {send_msg}',
                        receiver=msg.roomid, aters=msg.sender)
                    return

    # 帮助菜单
    def get_help(self, msg):
        OutPut.outPut(f'[*]: 正在调用Help功能菜单... ...')
        send_msg = f"【一、积分功能】\n" \
                   f"【1.1】、@机器人开启Ai对话\n" \
                   f"【1.2】、GPT3.5\n" \
                   f"【1.3】、星火大模型（联网）\n" \
                   f"【1.4】、秘塔搜索\n" \
                   f"【1.5】、Ai画画\n" \
                   f"【二、娱乐功能】\n" \
                   f"【2.1】、舔狗日记\n" \
                   f"【2.2】、毒鸡汤\n" \
                   f"【2.3】、讲笑话\n" \
                   f"【2.4】、秒懂世界\n" \
                   f"【2.5】、天气查询\n" \
                   f"【2.6】、点歌\n" \
                   f"【2.7】、看图猜成语\n" \
                   f"【2.8】、成语接龙\n" \
                   f"{'By #' + self.system_copyright if self.system_copyright else ''}"
        self.wcf.send_text(msg=send_msg, receiver=msg.roomid)

        # f"[烟花]【2.1】、舔狗日记\n" \
        # f"[烟花]【2.2】、摸鱼日历\n" \
        # f"[烟花]【2.3】、疯狂星期四\n" \
        # f"[烟花]【2.4】、早安寄语\n" \
        # f"[烟花]【2.5】、毒鸡汤\n" \
        # f"[烟花]【2.6】、讲笑话\n" \
        # f"[烟花]【2.7】、虎扑热搜\n" \
        # f"[烟花]【2.8】、每天60秒读懂世界\n" \
        # f"[烟花]【2.9】、天气查询\n" \
        # f"[烟花]【2.10】、点歌\n" \

        # num = ''
        # content = msg.content.strip()
        # if ' ' in content:
        #     num = content.split(' ')[-1]
        # if not num:
        #     send_msg = f"[爱心] ———— NGCBot功能菜单 ———— [爱心]\n[庆祝]【一、积分功能】\n[庆祝]【1.1】、微步威胁IP查询\n[庆祝]【1.2】、端口查询\n[庆祝]【1.3】、MD5查询[烟花]\n[庆祝]【1.4】、Ai对话(Gpt&星火模型&千帆模型)\n\n可在群内发送信息【WHOIS查询 qq.com】不需要@本Bot哦\n\n[烟花]【二、娱乐功能】\n" \
        #                f"[烟花]【2.1】、美女图片\n[烟花]【2.2】、美女视频\n[烟花]【2.3】、舔狗日记\n[烟花]【2.4】、摸鱼日历\n[烟花]【2.5】、星座查询\n[庆祝]【2.6】、KFC伤感文案\n[庆祝]【2.7】、手机号归属地查询\n[庆祝]【2.8】、WHOIS信息查询\n" \
        #                f"[烟花]【2.9】、备案查询\n\n您可以在群内发送消息【查询运势 白羊座】进行查询【其它功能类似】，或@本Bot进行AI对话哦\n\n需要调出帮助菜单，回复【帮助菜单】即可\n" \
        #                f"回复【help 2.1】可获取相应功能帮助[跳跳]，其它功能帮助以此类推[爱心]\n" \
        #                f"{'By #' + self.system_copyright if self.system_copyright else ''}"
        # elif num == '1.1':
        #     send_msg = '[庆祝]【1.1】、微步威胁IP查询功能帮助\n\n[爱心]命令：【ip查询 x.x.x.x】'
        # elif num == '1.2':
        #     send_msg = '[庆祝]【1.2】、端口查询功能帮助\n\n[爱心]命令：【端口查询 x.x.x.x】'
        # elif num == '1.3':
        #     send_msg = '[庆祝]【1.3】、MD5查询功能帮助\n\n[爱心]命令：【MD5查询 MD5密文】'
        # elif num == '1.4':
        #     send_msg = '[庆祝]【1.4】、Ai对话功能帮助\n\n[爱心]命令：【@机器人进行Ai对话】'
        # elif num == '2.1':
        #     send_msg = '[烟花]【2.1】、美女图片功能帮助\n\n[爱心]命令：【图片】【美女图片】'
        # elif num == '2.2':
        #     send_msg = '[烟花]【2.2】、美女视频功能帮助\n\n[爱心]命令：【视频】【美女视频】'
        # elif num == '2.3':
        #     send_msg = '[烟花]【2.3】、舔狗日记功能帮助\n\n[爱心]命令：【舔狗日记】'
        # elif num == '2.4':
        #     send_msg = '[烟花]【2.4】、摸鱼日历功能帮助\n\n[爱心]命令：【摸鱼日历】\n\n[爱心]联系主人可开启定时发送哦[跳跳]'
        # elif num == '2.5':
        #     send_msg = '[烟花]【2.5】、星座查询功能帮助\n\n[爱心]命令：【星座查询 白羊】'
        # elif num == '2.6':
        #     send_msg = '[烟花]【2.6】、KFC伤感文案功能帮助\n\n[爱心]命令：【Kfc】'
        # elif num == '2.7':
        #     send_msg = '[烟花]【2.7】、手机号归属地查询功能帮助\n\n[爱心]命令：【归属查询 110】'
        # elif num == '2.8':
        #     send_msg = '[烟花]【2.8】、WHOIS信息查询功能帮助\n\n[爱心]命令：【whois查询 qq.com】'
        # elif num == '2.9':
        #     send_msg = '[烟花]【2.9】、备案查询功能帮助\n\n[爱心]命令：【icp查询 qq.com】'
        # else:
        #     send_msg = f'@{self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)}\n' \
        #                f'帮助菜单编号错误，请重新输入编号！！！'
        # self.wcf.send_text(msg=send_msg, receiver=msg.roomid)

    # Ai对话
    def get_ai(self, msg, at_user_lists, model=None):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name}\n您是尊贵的管理员/超级管理员，本次对话不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            if not model:
                question = self.handle_atMsg(msg, at_user_lists=at_user_lists)
            else:
                question = msg.content.strip().split(' ', 1)[1]
            if model != 'image':
                use_msg = f'@{wx_name}\n' + self.Ams.get_ai(
                    question=question, model=model)
                self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
            else:
                OutPut.outPut(f'[*]: 正在调用文生图接口... ...')
                save_path = self.Ams.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.jpg'
                url = self.Ams.get_ai(question=question, model=model)
                if url:
                    headers = {
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json'
                    }
                    try:
                        pic_data = requests.get(url=url, headers=headers, timeout=90, verify=False).content
                        with open(file=save_path, mode='wb') as pd:
                            pd.write(pic_data)
                        OutPut.outPut(f'[+]: 文生图接口调用成功，图片保存路径：{save_path}\n')
                    except Exception as e:
                        msg = f'[-]: 文生图接口出现错误，错误信息：{e}\n'
                        OutPut.outPut(msg)
                    if os.path.exists(save_path):
                        self.wcf.send_image(path=save_path, receiver=msg.roomid)
                        self.save_path = save_path
                    # usr_msg = f'@{wx_name}\n [{question}]：\n{url}'
                    usr_msg = f'@{wx_name}\n [{question}]：\n图片已发送，请查收！'
                    self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
                else:
                    usr_msg = f'@{wx_name}\n [{question}]：\n图片生成失败！'
                    self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
        # 不是管理员
        else:
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    self.Ai_Point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=int(self.Ai_Point))
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                point_msg = f'@{wx_name} 您使用了Ai对话功能，扣除您 {self.Ai_Point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=point_msg, receiver=msg.roomid, aters=msg.sender)
                if not model:
                    question = self.handle_atMsg(msg, at_user_lists=at_user_lists)
                else:
                    question = msg.content.strip().split(' ', 1)[1]
                if model != 'image':
                    use_msg = f'@{wx_name}\n' + self.Ams.get_ai(
                        question=question, model=model)
                    self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
                else:
                    OutPut.outPut(f'[*]: 正在调用Spark文生图接口... ...')
                    save_path = self.Ams.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + '.jpg'
                    url = self.Ams.get_ai(question=question, model=model)
                    if url:
                        headers = {
                            'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                            'Content-Type': 'application/json'
                        }
                        try:
                            pic_data = requests.get(url=url, headers=headers, timeout=90, verify=False).content
                            with open(file=save_path, mode='wb') as pd:
                                pd.write(pic_data)
                            OutPut.outPut(f'[+]: Spark文生图接口调用成功，图片保存路径：{save_path}\n')
                        except Exception as e:
                            msg = f'[-]: Spark文生图接口出现错误，错误信息：{e}\n'
                            OutPut.outPut(msg)
                        if os.path.exists(save_path):
                            self.wcf.send_image(path=save_path, receiver=msg.roomid)
                            self.save_path = save_path
                        # usr_msg = f'@{wx_name}\n [{question}]：\n{url}'
                        usr_msg = f'@{wx_name}\n [{question}]：\n图片已发送，请查收！'
                        self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
                    else:
                        usr_msg = f'@{wx_name}\n [{question}]：\n图片生成失败！'
                        self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # Md5查询
    def get_md5(self, msg):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次查询不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            use_msg = self.Ams.get_md5(content=msg.content.strip())
            self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
        # 不是管理员
        else:
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    self.Md5_Point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=int(self.Md5_Point))
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                md5_msg = f'@{wx_name} 您使用了MD5解密功能，扣除您 {self.Md5_Point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=md5_msg, receiver=msg.roomid, aters=msg.sender)
                use_msg = self.Ams.get_md5(content=msg.content.strip())
                self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # IP查询
    def get_ip(self, msg):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次查询不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            use_msg = f'@{wx_name} ' + self.Ams.get_threatbook_ip(content=msg.content.strip())
            self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
        # 不是管理员
        else:
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    self.Ip_Point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=int(self.Ip_Point))
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                md5_msg = f'@{wx_name} 您使用了威胁IP查询功能，扣除您 {self.Ip_Point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=md5_msg, receiver=msg.roomid, aters=msg.sender)
                use_msg = self.Ams.get_threatbook_ip(content=msg.content.strip())
                self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 端口查询
    def get_port(self, msg):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次查询不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            use_msg = f'@{wx_name} ' + self.Ams.get_portScan(content=msg.content.strip())
            self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
        # 不是管理员
        else:
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    self.Port_Scan_Point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=int(self.Port_Scan_Point))
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                scan_msg = f'@{wx_name} 您使用了端口查询功能，扣除您 {self.Port_Scan_Point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=scan_msg, receiver=msg.roomid, aters=msg.sender)
                use_msg = self.Ams.get_portScan(content=msg.content.strip())
                self.wcf.send_text(msg=use_msg, receiver=msg.roomid, aters=msg.sender)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)  # 端口查询

    def get_xiuren_pic(self, msg):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次操作不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            try:
                num = random.randint(1, 10305)
                emoji = self.Ams.db_emoji.get_emoji_by_id(num)
                self.wcf.send_text(msg=emoji, receiver=msg.roomid)
            except Exception as e:
                self.wcf.send_text(msg=str(e), receiver=msg.roomid)
            pic_path = self.get_xiuren_pic_path()
            self.wcf.send_image(path=pic_path, receiver=msg.roomid)
        # 不是管理员
        else:
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    self.Port_Scan_Point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=int(self.Port_Scan_Point))
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                scan_msg = f'@{wx_name} 您使用了隐藏功能-拒绝者，扣除您 {self.Port_Scan_Point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=scan_msg, receiver=msg.roomid, aters=msg.sender)
                pic_path = self.get_xiuren_pic_path()
                self.wcf.send_image(path=pic_path, receiver=msg.roomid)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 赠送积分
    def send_point(self, msg, content, at_user_lists):
        try:
            point = content.split(' ')[-1]
            wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
            room_name = self.Dms.query_room_name(room_id=msg.roomid)
            for give_sender in at_user_lists:
                give_name = self.wcf.get_alias_in_chatroom(wxid=give_sender, roomid=msg.roomid)
                send_msg = f'@{wx_name}'
                send_msg += self.Dps.send_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                room_name=room_name,
                                                give_sender=give_sender, give_name=give_name, point=point)
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)
        except Exception as e:
            OutPut.outPut(f'[~]: 赠送积分出了点小问题 :{e}')

    # 新增管理员
    def add_admin(self, sender, wx_ids, room_id):
        if wx_ids:
            for wx_id in wx_ids:
                wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                at_msg = f'@{wx_name}\n'
                wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = self.Dms.add_admin(room_id=room_id, wx_id=wx_id, wx_name=wx_name)
                at_msg += msg
                self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 删除管理员
    def del_admin(self, sender, wx_ids, room_id):
        if wx_ids:
            for wx_id in wx_ids:
                wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                at_msg = f'@{wx_name}\n'
                msg = self.Dms.del_admin(room_id=room_id, wx_id=wx_id, wx_name=wx_name)
                at_msg += msg
                self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加推送群聊
    def add_push_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_push_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除推送服务
    def del_push_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_push_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加白名单群聊
    def add_white_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_white_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除白名单群聊
    def del_white_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_white_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加白名单公众号
    def add_white_gh(self, msg):
        try:
            root_xml = ET.fromstring(msg.content)
            at_msg = f'@{self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)}\n'
            gh_id = root_xml.find('.//sourceusername').text
            gh_name = root_xml.find('.//sourcedisplayname').text
            print('公众号信息：', gh_id, gh_name)
            if not gh_id and not gh_name:
                gh_name = re.search(r'sourcedisplayname&gt;(?P<gh_name>.*?)&lt;/sourcedisplayname&gt;',
                                    str(msg.content).strip(),
                                    re.DOTALL)
                gh_id = re.search(r'sourceusername&gt;(?P<gh_id>.*?)&lt;/sourceusername&gt;',
                                  str(msg.content).strip(),
                                  re.DOTALL)
                if not gh_name.group('gh_name'):
                    gh_name = re.search(r'&lt;appname&gt;(?P<gh_name>.*?)&lt;/appname&gt', str(msg.content).strip(),
                                        re.DOTALL)
                if gh_name and gh_id:
                    gh_name = gh_name.group('gh_name')
                    gh_id = gh_id.group('gh_id')
                    add_msg = self.Dms.add_white_gh(gh_name=gh_name, gh_id=gh_id)
                    if not add_msg:
                        return
                    at_msg += self.Dms.add_white_gh(gh_name=gh_name, gh_id=gh_id)
                    self.wcf.send_text(msg=at_msg, receiver=msg.roomid, aters=msg.sender)

            if gh_id:
                gh_msg = self.Dms.add_white_gh(gh_id=gh_id, gh_name=gh_name)
                if not gh_msg:
                    return
                at_msg += gh_msg
                self.wcf.send_text(msg=at_msg, receiver=msg.roomid, aters=msg.sender)
        except Exception as e:
            OutPut.outPut(f'[~]: 添加公众号白名单出了点小问题 :{e}')

    # 移除白名单公众号
    def del_white_gh(self, msg):
        if 'gh_' in msg:
            gh_name = '不知名广告'
            try:
                at_msg = f'@{self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)}\n'
                res = re.search(r'sourcedisplayname&gt;(?P<gh_name>.*?)&lt;/sourcedisplayname&gt;',
                                str(msg.content).strip(),
                                re.DOTALL)
                if not res.group('gh_name'):
                    res = re.search(r'&lt;appname&gt;(?P<gh_name>.*?)&lt;/appname&gt', str(msg.content).strip(),
                                    re.DOTALL)
                if res:
                    gh_name = res.group('gh_name')
                    at_msg += self.Dms.del_white_gh(gh_name=gh_name)
                    self.wcf.send_text(msg=at_msg, receiver=msg.roomid, aters=msg.sender)
                else:
                    at_msg += '出错了, 请自己调试一下 ~~~~~~'
                    self.wcf.send_text(msg=at_msg, receiver=msg.roomid, aters=msg.sender)
            except Exception as e:
                OutPut.outPut(f'[-]: 移除白名单公众号出现错误，错误信息：{e}')

    # 添加黑名单群聊
    def add_black_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_black_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除黑名单群聊
    def del_black_room(self, sender, room_id):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_black_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 把人移出群聊
    def del_user(self, sender, room_id, wx_ids):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        ret = self.wcf.del_chatroom_members(roomid=room_id, wxids=','.join(wx_ids))
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                del_user_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                if ret:
                    msg = f'@{wx_name}\n群友 [{del_user_name}] 被管理踢出去了, 剩下的群友小心点 ~~~~~~'
                else:
                    msg = f'@{wx_name}\n群友 [{del_user_name}] 还没踢出去, 赶紧看日志找找原因！！！'
            else:
                msg = f'@{wx_name}\n 你小子想退群了是吧'
            OutPut.outPut(msg)
            self.wcf.send_text(msg=msg, receiver=room_id, aters=sender)

    # 检测广告并自动踢出
    def detecting_advertisements(self, msg):
        white_ghs = self.Dms.show_white_ghs().keys()
        root_xml = ET.fromstring(msg.content)
        try:
            gh_id = root_xml.find('.//sourceusername').text
            gh_name = root_xml.find('.//sourcedisplayname').text
            if gh_name == None:
                gh_name = root_xml.find('.//appname').text
            if gh_name == None:
                gh_name = root_xml.find('.//nickname').text
            if gh_id not in white_ghs:
                send_msg = f'检测到广告, 名字为 [{gh_name}], 已自动踢出, 还请群友们不要学他 ~~~~~~'
                self.wcf.del_chatroom_members(roomid=msg.roomid, wxids=msg.sender)
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[-]: 检测广告功能出现错误，错误信息: {e}')

    # 增加积分
    # TODO: 出现过异常，暂不确定原因，有可能是“退出的群聊”导致
    def Add_Point(self, msg, content, at_user_list):
        try:
            OutPut.outPut(f'[*]: 增加积分接口接收到的消息: {content}')
            point = content.strip().split(' ')[-1]
            for wx_id in at_user_list:
                wx_name = self.wcf.get_alias_in_chatroom(wxid=wx_id, roomid=msg.roomid)
                room_name = self.Dms.query_room_name(room_id=msg.roomid)
                add_msg = self.Dps.add_point(wx_id=wx_id, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                             point=point)
                add_msg = f'@{wx_name}\n' + add_msg
                self.wcf.send_text(msg=add_msg, receiver=msg.roomid, aters=wx_id)
            OutPut.outPut(f'[+]: 增加积分接口调用成功')
        except Exception as e:
            OutPut.outPut(f'[-]: 增加积分接口出现错误，错误信息: {e}')

    # 减少积分
    def Del_Point(self, msg, content, at_user_list):
        try:
            point = content.strip().split(' ')[-1]
            for wx_id in at_user_list:
                wx_name = self.wcf.get_alias_in_chatroom(wxid=wx_id, roomid=msg.roomid)
                if wx_id not in self.administrators:
                    room_name = self.Dms.query_room_name(room_id=msg.roomid)
                    del_msg = self.Dps.del_point(wx_id=wx_id, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                                 point=point)
                    send_msg = f'@{wx_name}\n' + str(del_msg)
                    self.wcf.send_text(msg=del_msg, receiver=msg.roomid, aters=wx_id)
                else:
                    send_msg = f'@{wx_name}\n你小子想退群了是吧'
                    self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=wx_id)
        except Exception as e:
            OutPut.outPut(f'[-]: 减少积分接口出现错误，错误信息: {e}')

    # 返回引用XML消息的类型
    def handle_xml_type(self, msg):
        ttype = re.search(r'<type>(?P<type>.*?)</type>', msg.content)
        if ttype:
            return ttype.group('type')
        else:
            return None

    # 返回引用XML消息的title
    def handle_xml_msg(self, msg):
        send_text = re.search(r'<title>(?P<title>.*?)</title>', msg.content)
        if send_text:
            return send_text.group('title')
        else:
            return None

    # 被@人 wx_id 获取
    def get_at_wx_id(self, xml):
        root_xml = ET.fromstring(xml)
        try:
            at_user_lists = root_xml.find('.//atuserlist').text.strip(',')
            if ',' in at_user_lists:
                at_user_lists = at_user_lists.split(',')
            else:
                at_user_lists = [at_user_lists]
        except AttributeError:
            OutPut.outPut(f'[~]: 获取被@的微信id出了点小问题, 不用管 ~~~')
            at_user_lists = []
        return at_user_lists

    # 处理@人后的消息
    def handle_atMsg(self, msg, at_user_lists):
        if at_user_lists:
            content = msg.content
            for wx_id in at_user_lists:
                content = content.replace('@' + self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=wx_id), '')
            return content.strip()

    # 关键词判断
    def judge_keyword(self, keyword, msg, list_bool=False, equal_bool=False, in_bool=False,
                      split_bool=False):
        # 如果触发词是列表 并且只需要包含则执行
        if list_bool and in_bool:
            for word in keyword:
                if word in msg:
                    return True

        # 如果触发词是列表 并且需要相等则执行
        if list_bool and equal_bool:
            for word in keyword:
                if word == msg:
                    return True

        # 如果关键词是列表, 并且判断的消息需要以空格切割 判断第一个元素位置与关键词相等则触发
        if list_bool and split_bool:
            try:
                if ' ' in msg or msg == 'help':
                    for word in keyword:
                        split_one = msg.split(' ')[0]
                        if word == split_one:
                            return True
            except Exception:
                return

    def send_music_message(self, digest, url, receiver):
        self.wcf.send_rich_text(name='点歌',
                                account='',
                                title='MyFreeMP3',
                                digest=digest,
                                url=url,
                                thumburl='https://tool.liumingye.cn/music/img/pwa-192x192.png',
                                receiver=receiver)

    def get_xiuren_pic_path(self):
        root_dir = self.current_path + '/../XiuRen_downloads'

        def generate_path():
            page_number = random.randint(1, 59)
            second_number = random.randint(1, 24)
            image_number = random.randint(0, 4)
            return f"{root_dir}/page_{page_number}/{second_number}/image_{image_number}.jpg"

        def check_file(path):
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                if file_size > 10240:  # 10KB
                    return True
            return False

        while True:
            random_path = generate_path()
            if not check_file(random_path):
                print(f"文件 {random_path} 不存在或大小大于10KB，重新生成...")
            else:
                print(f"文件 {random_path}")
                return random_path
