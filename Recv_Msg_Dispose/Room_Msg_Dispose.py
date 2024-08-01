import json
import os
import random
import re
import threading
import time
import traceback
import xml.etree.ElementTree as ET
from threading import Thread

import requests
import yaml

from Api_Server.Api_Main_Server import Api_Main_Server
from Db_Server.Db_Main_Server import Db_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from OutPut import OutPut
from Util.meme import all_emojis_dict_with_jpg_keys, all_emojis_dict_with_jpg
from advanced_path import PRJ_PATH


class Room_Msg_Dispose:
    def __init__(self, wcf, main_server):
        self.wcf = wcf
        self.main_server = main_server
        # 实例化数据操作类
        self.Dms = Db_Main_Server(wcf=self.wcf)
        # 实例化积分数据类
        self.Dps = Db_Point_Server()

        # 实例化API类
        self.Ams = Api_Main_Server(wcf=self.wcf)

        # 读取配置文件
        config = yaml.load(open(PRJ_PATH + '/Config/config.yaml', encoding='UTF-8'), yaml.Loader)
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

        # 读取状态配置文件
        self.state_json_file = PRJ_PATH + '/Config/state.json'
        self.state = load_state_file(self.state_json_file)

        # 管理员模式 {"room_id": True}
        self.manager_mode_rooms = self.state.get('manager_mode_rooms', {})
        # 游戏模式
        self.game_mode_rooms = {}
        self.game_point = {}
        self.game_answer = {}
        self.game_success = {}
        # 看图猜成语-图片地址
        self.idiom_pic = {}
        # 成语接龙-用户答案
        self.idiom_usr_answer = {}
        # 成语接龙-用户答案历史
        self.idiom_usr_answer_history = {}
        # 成语接龙-题目
        self.idiom_question = {}
        # 创建一个线程锁
        self.counter_lock = threading.Lock()
        # 屏蔽
        self.block_wx_ids = ['wxid_5neoavqeubzm22']
        # 防撤回功能 {"room_id": True}
        self.recall_msg_dict = {}
        self.recall_mode_rooms = self.state.get('recall_mode_rooms', {})
        # 启动撤回消息删除线程
        self.thread_del_recall_msg_dict = threading.Thread(target=self.del_recall_msg_dict)
        self.thread_del_recall_msg_dict.start()
        # 搜歌链接
        self.search_link_dict = {}

    def save_state(self):
        self.state['manager_mode_rooms'] = self.manager_mode_rooms
        self.state['recall_mode_rooms'] = self.recall_mode_rooms
        save_state_file(self.state_json_file, self.state)

    def del_recall_msg_dict(self):
        while True:
            with self.counter_lock:
                # 删除超过3分钟的撤回消息
                for key in list(self.recall_msg_dict.keys()):
                    if time.time() - self.recall_msg_dict[key]['ts'] > 180:
                        self.recall_msg_dict.pop(key)
            time.sleep(60)

    def handle_recall(self, msg):
        try:
            if not self.recall_mode_rooms.get(msg.roomid, False):
                return
            # 撤回消息
            if msg.type == 10002:
                msg_id = re.findall(f"<newmsgid>(.*)</newmsgid>", msg.content)[0]
                msg_id = str(msg_id)
                if msg_id in self.recall_msg_dict.keys():
                    recall_msg = self.recall_msg_dict[msg_id]
                    recall_type = recall_msg.get("type")
                    wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
                    # 如果获取不到群昵称，则获取微信昵称
                    if not wx_name:
                        wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
                    if recall_type == 1:
                        self.wcf.send_text(msg=f'【{wx_name}】 撤回了\n{recall_msg.get("content", "")}',
                                           receiver=msg.roomid)
                    else:
                        self.wcf.send_text(msg=f'【{wx_name}】 撤回了一条消息', receiver=msg.roomid)
                        self.send_image_ensure_success(path=recall_msg.get("content", ""), receiver=msg.roomid)
                    self.recall_msg_dict.pop(msg_id)
            # 普通文本消息
            elif msg.type == 1:
                with self.counter_lock:
                    self.recall_msg_dict.update(
                        {str(msg.id): {'sender': msg.sender, 'roomid': msg.roomid, 'ts': msg.ts,
                                       'content': msg.content, 'type': msg.type}})
            # 图片消息
            elif msg.type == 3:
                with self.counter_lock:
                    img_dir = PRJ_PATH + '/Cache/Recall_Pic_Cache'
                    os.makedirs(img_dir, exist_ok=True)

                    time.sleep(1)
                    img_path = self.wcf.download_image(msg.id, msg.extra, img_dir)
                    # 如果下载失败，再次下载一次
                    if not img_path:
                        time.sleep(1)
                        img_path = self.wcf.download_image(msg.id, msg.extra, img_dir)

                    if img_path:
                        self.recall_msg_dict.update(
                            {str(msg.id): {'sender': msg.sender, 'roomid': msg.roomid, 'ts': msg.ts,
                                           'content': img_path, 'type': msg.type}})
                    else:
                        OutPut.outPut(f"[-]: 图片下载失败 {msg.id}")
        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f"[-]: 撤回消息处理失败 {e}")

    # 主消息处理
    def Msg_Dispose(self, msg):
        # 处理撤回消息
        self.handle_recall(msg)

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
            OutPut.outPut(f"[*]: 艾特列表 {at_user_lists}")
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
            return
        # 删除管理员流程
        elif self.judge_keyword(keyword=self.Del_Admin_KeyWords, msg=msg.content, list_bool=True, in_bool=True):
            Thread(target=self.del_admin, name="删除管理员", args=(msg.sender, at_user_lists, msg.roomid,)).start()
            return
        self.Admin_Function(msg, at_user_lists)

    # 管理员功能
    def Admin_Function(self, msg, at_user_lists):
        # 开启推送服务
        if self.judge_keyword(keyword=self.Add_Push_KeyWords, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.add_push_room, name="添加推送群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 关闭推送服务
        elif self.judge_keyword(keyword=self.Del_Push_KeyWords, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_push_room, name="移除推送群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 添加白名单群聊
        elif self.judge_keyword(keyword=self.Add_WhiteRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.add_white_room, name="添加白名单群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 移除白名单群聊
        elif self.judge_keyword(keyword=self.Del_WhiteRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_white_room, name="移除白名单群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 添加黑名单群聊
        elif self.judge_keyword(keyword=self.Add_BlackRoom_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.add_black_room, name="添加黑名单群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 移除黑名单群聊
        elif self.judge_keyword(keyword=self.Del_Black_Room_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_black_room, name="移除黑名单群聊", args=(msg.sender, msg.roomid,)).start()
            return
        # 把人移出群聊
        elif self.judge_keyword(keyword=self.Del_User_Words, msg=self.handle_atMsg(msg, at_user_lists), list_bool=True,
                                equal_bool=True):
            Thread(target=self.del_user, name="把人移出群聊", args=(msg.sender, msg.roomid, at_user_lists,)).start()
            return
        # 屏蔽个人消息
        elif self.judge_keyword(keyword=["屏蔽", "屏蔽消息"], msg=self.handle_atMsg(msg, at_user_lists), list_bool=True,
                                equal_bool=True):
            Thread(target=self.block_personal_msg, name="屏蔽个人消息",
                   args=(msg.sender, msg.roomid, at_user_lists,)).start()
            return
        # 取消屏蔽个人消息
        elif self.judge_keyword(keyword=["取消屏蔽", "取消屏蔽消息"], msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True,
                                equal_bool=True):
            Thread(target=self.unblock_personal_msg, name="取消屏蔽个人消息",
                   args=(msg.sender, msg.roomid, at_user_lists,)).start()
            return
        # 移除白名单公众号
        elif self.judge_keyword(keyword=self.Del_WhiteGh_Words, msg=self.handle_xml_msg(msg), list_bool=True,
                                equal_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.del_white_gh, name="移除白名单公众号", args=(msg,)).start()
            return
        # 增加用户积分
        elif self.judge_keyword(keyword=self.Add_Point_Words, msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True,
                                split_bool=True):
            Thread(target=self.Add_Point, name="增加积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            return
        # 减少用户积分
        elif self.judge_keyword(keyword=self.Del_Point_Words, msg=self.handle_atMsg(msg, at_user_lists), list_bool=True,
                                split_bool=True):
            Thread(target=self.Del_Point, name="减少积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            return
        # 添加白名单公众号
        elif msg.type == 49:
            Thread(target=self.add_white_gh, name="添加白名单公众号", args=(msg,)).start()
            return
        # 积分限制功能
        elif msg.content.strip() in ['取消积分限制', '取消积分', '取消限制', '关闭积分限制', '关闭积分', '关闭限制']:
            self.Ai_Point = 0
            self.wcf.send_text(msg='关闭积分限制成功', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['开启积分限制', '开启积分', '开启限制']:
            self.Ai_Point = 10
            self.wcf.send_text(msg='开启积分限制成功', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['开启管理员模式', '管理员模式']:
            self.manager_mode_rooms[msg.roomid] = True
            self.wcf.send_text(msg=f'管理员模式开启成功，仅响应管理员消息', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['关闭管理员模式', '取消管理员模式', '退出管理员模式', '普通模式']:
            self.manager_mode_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'管理员模式关闭成功，恢复正常消息响应', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['开启防撤回', '开启防撤回功能']:
            self.recall_mode_rooms[msg.roomid] = True
            self.wcf.send_text(msg=f'已开启防撤回', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['关闭防撤回', '关闭防撤回功能']:
            self.recall_mode_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'已关闭防撤回', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['高级画画', '高级画画模型', '高级画画模式']:
            self.Ams.is_advanced_drawing = True
            self.wcf.send_text(msg=f'已经切换为高级画画模型', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['普通画画', '普通画画模型', '普通画画模式']:
            self.Ams.is_advanced_drawing = False
            self.wcf.send_text(msg=f'已经切换为普通画画模型', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['360', '360搜图', '360搜图模式']:
            self.Ams.search_pic_mode = "360"
            self.wcf.send_text(msg=f'已经切换为360搜图模式', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['百度', '百度搜图', '百度搜图模式', "baidu"]:
            self.Ams.search_pic_mode = "baidu"
            self.wcf.send_text(msg=f'已经切换为百度搜图模式', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['搜狗', '搜狗搜图', '搜狗搜图模式', "sogou"]:
            self.Ams.search_pic_mode = "sogou"
            self.wcf.send_text(msg=f'已经切换为搜狗搜图模式', receiver=msg.roomid, aters=msg.sender)
            return
        elif self.judge_keyword(keyword=["撤回最新消息", "撤回消息"],
                                msg=msg.content.strip(),
                                list_bool=True,
                                equal_bool=True):
            Thread(target=self.recall_msg, name="撤回", args=(msg,)).start()
            return
        elif self.judge_keyword(keyword=["查询数据库", 'sql'],
                                msg=msg.content.strip(),
                                list_bool=True,
                                split_bool=True):
            try:
                _, db, query = msg.content.strip().split(' ', 2)
                print(db, query)
                # "MSG0.db"
                result = self.wcf.query_sql(db, query)
                result = str(result)
                self.wcf.send_text(msg=result, receiver=msg.roomid, aters=msg.sender)
            except Exception as e:
                OutPut.outPut(f'[-]: 查询数据库失败 {e}')
            return
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
        Thread(target=self.Happy_Function, name="娱乐功能", args=(msg, at_user_lists)).start()
        Thread(target=self.Point_Function, name="积分功能", args=(msg, at_user_lists,)).start()

    # 娱乐功能
    def Happy_Function(self, msg, at_user_lists):
        if self.game_mode_rooms.get(msg.roomid, False):
            self.gaming_function(msg)
            return
        if self.game_function(msg):
            return
        # 美女图片
        if self.judge_keyword(keyword=self.Pic_Words, msg=msg.content, list_bool=True, equal_bool=True):
            save_path = self.Ams.get_girl_pic()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        # 美女视频
        elif self.judge_keyword(keyword=self.Video_Words, msg=msg.content, list_bool=True, equal_bool=True):
            save_path = self.Ams.get_girl_video()
            if save_path:
                self.wcf.send_file(path=save_path, receiver=msg.roomid)
            return
        # 天气查询
        elif self.judge_keyword(keyword=self.Weather_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            weather_msg = self.Ams.query_weather(msg.content.strip())
            if weather_msg:
                self.send_at_msg(msg.roomid, msg.sender, weather_msg)
            return
        # 舔狗日记
        elif self.judge_keyword(keyword=self.Dog_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            dog_msg = self.Ams.get_dog()
            if dog_msg:
                self.send_at_msg(msg.roomid, msg.sender, dog_msg)
            return
        # 早安寄语
        elif self.judge_keyword(keyword=self.Morning_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            morning_msg = self.Ams.get_morning()
            if morning_msg:
                self.send_at_msg(msg.roomid, msg.sender, morning_msg)
            return
        # 毒鸡汤
        elif self.judge_keyword(keyword=self.Poison_Chicken_Soup_Words, msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            poison_chicken_soup_msg = self.Ams.get_soup()
            if poison_chicken_soup_msg:
                self.send_at_msg(msg.roomid, msg.sender, poison_chicken_soup_msg)
            return
        # 讲笑话
        elif self.judge_keyword(keyword=self.Joke_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            joke_msg = self.Ams.get_joke()
            if joke_msg:
                self.send_at_msg(msg.roomid, msg.sender, joke_msg)
            return
        # 60s
        elif self.judge_keyword(keyword=self.s60_Words + ["60s图片", "60图片", "60pic", "60spic"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            save_path = self.Ams.get_60s_pic()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        # 虎扑热搜
        elif self.judge_keyword(keyword=self.Hupu_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            hupu_msg = self.Ams.get_hupu()
            if hupu_msg:
                self.wcf.send_text(msg=hupu_msg[0], receiver=msg.roomid, aters=msg.sender)
                self.wcf.send_text(msg=hupu_msg[1], receiver=msg.roomid, aters=msg.sender)
            return
        # 神回复
        elif self.judge_keyword(keyword=["神回复"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            god_msg = self.Ams.get_god_reply()
            if god_msg:
                self.send_at_msg(msg.roomid, msg.sender, god_msg)
            return
        # 每日英语
        elif self.judge_keyword(keyword=["每日英语", "来一句英语"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            english_msg = self.Ams.get_daily_english()
            if english_msg:
                self.send_at_msg(msg.roomid, msg.sender, english_msg)
            return
        # 摸鱼日记
        elif self.judge_keyword(keyword=self.Fish_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            save_path = self.Ams.get_fish()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
        # 内涵段子
        elif self.judge_keyword(keyword=["内涵段子", "段子", "讲段子"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            save_path = self.Ams.get_duanzi()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            else:
                text = self.Ams.get_duanzi_text()
                self.wcf.send_text(msg=text, receiver=msg.roomid) if text else None
            return
        # 喜加一
        elif self.judge_keyword(keyword=["喜加一", "EPIC喜加一", "STEAM喜加一", "免费游戏"],
                                msg=msg.content.strip().upper(),
                                list_bool=True,
                                equal_bool=True):
            content_list = self.Ams.get_steam_plus_one()
            if content_list:
                for content in content_list:
                    self.wcf.send_text(msg=content, receiver=msg.roomid)
            return
        # 点歌功能
        elif self.judge_keyword(keyword=["点歌", "听歌"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            music_name = msg.content.strip().split(' ', 1)[1].strip()
            digest = '搜索歌曲：{}'.format(music_name)
            url = 'https://tool.liumingye.cn/music/#/search/M/song/{}'.format(music_name)
            self.send_music_message(digest, url, msg.roomid)
            return
        elif msg.content.strip() in ["点歌", "听歌"]:
            digest = '点击进入点歌页面'
            url = 'https://tool.liumingye.cn/music/'
            self.send_music_message(digest, url, msg.roomid)
            return
        # 成语解析功能
        elif self.judge_keyword(keyword=["成语解析", "成语解释", "成语查询"], msg=msg.content.strip(), list_bool=True,
                                split_bool=True):
            idiom_name = msg.content.strip().split(' ', 1)[1].strip()
            idiom_explain = self.Ams.get_idiom_explain(idiom_name)
            if idiom_explain:
                self.send_at_msg(msg.roomid, msg.sender, idiom_explain)
            return
        # 谷歌翻译
        elif self.judge_keyword(keyword=["谷歌翻译", "翻译", "翻译翻译", "给我翻译翻译"], msg=msg.content.strip(),
                                list_bool=True,
                                split_bool=True):
            chinese_content = msg.content.strip().split(' ', 1)[1].strip()
            english_content = self.Ams.get_translate_by_api(chinese_content) or self.Ams.get_translate(chinese_content)
            if not english_content:
                OutPut.outPut(f'[-]: 翻译接口出错')
                return
            trans_msg = f'原文：{chinese_content}\n' \
                        + f'译文：{english_content}'
            self.send_at_msg(msg.roomid, msg.sender, trans_msg)
            return
        # 疯狂星期四文案
        elif self.judge_keyword(keyword=self.Kfc_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            kfc_msg = self.Ams.get_kfc()
            if kfc_msg:
                self.send_at_msg(msg.roomid, msg.sender, kfc_msg.replace('\\n', '\n'))
            return
        # help帮助菜单
        elif self.judge_keyword(keyword=self.HelpMenu_Words + ["功能", "萝卜功能", "萝卜菜单"], msg=msg.content.strip(),
                                list_bool=True, equal_bool=True):
            Thread(target=self.get_help, name="Help帮助菜单", args=(msg,)).start()
            return
        # # 自定义回复
        # Thread(target=self.custom_get, name="自定义回复", args=(msg,)).start()

        # 定时提醒功能
        elif self.judge_keyword(keyword=["定时提醒", "定时任务"], msg=msg.content.strip(), list_bool=True,
                                split_bool=True, equal_bool=True):
            try:
                key_, days, times, content = msg.content.strip().split(' ', 3)
                if not days or not times or not content:
                    return
                if key_ == "定时提醒":
                    Thread(target=self.main_server.Tms.add_remind_task,
                           args=(days, times, content, msg.roomid, msg.sender)).start()
                else:
                    Thread(target=self.main_server.Tms.add_remind_task,
                           args=(days, times, content, msg.roomid, msg.sender, True)).start()
            except Exception as e:
                OutPut.outPut(f'[-]: 定时事件设置失败 {e}')
                reply = ('示例：\n'
                         '“定时提醒/任务 周一/星期一/每天/工作日 一点十分/1.10/1:10 摸鱼”\n'
                         '或者：\n'
                         '“定时提醒/任务 明天/12.7/12月7日 一点十分/1.10/1:10 摸鱼”')
                self.send_at_msg(msg.roomid, msg.sender, reply)
            return
        elif self.judge_keyword(keyword=["取消提醒", "关闭提醒", "删除提醒",
                                         "取消任务", "关闭任务", "删除任务",
                                         "取消定时事件", "关闭定时事件", "删除定时事件"],
                                msg=msg.content.strip(), list_bool=True, split_bool=True):
            try:
                id_ = msg.content.strip().split(' ', 1)[1]
                id_ = int(id_)
                Thread(target=self.main_server.Tms.delete_job,
                       args=(id_, msg.roomid, msg.sender)).start()
            except Exception as e:
                OutPut.outPut(f'[-]: 取消提醒设置失败 {e}')
            return
        elif self.judge_keyword(keyword=["管理员删除提醒", "管理员删除任务", "管理员删除定时事件"],
                                msg=msg.content.strip(), list_bool=True, split_bool=True):
            try:
                id_ = msg.content.strip().split(' ', 1)[1]
                id_ = int(id_)
                Thread(target=self.main_server.Tms.delete_job,
                       args=(id_, msg.roomid, msg.sender, True)).start()
            except Exception as e:
                OutPut.outPut(f'[-]: 取消提醒设置失败 {e}')
            return
        elif self.judge_keyword(keyword=["提醒查询", "提醒查看", "查询提醒", "查看提醒",
                                         "任务查询", "任务查看", "查询任务", "查看任务",
                                         "定时事件查询", "定时事件查看", "查询定时事件", "查看定时事件"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            try:
                Thread(target=self.main_server.Tms.show_jobs,
                       args=(msg.roomid, msg.sender)).start()
            except Exception as e:
                OutPut.outPut(f'[-]: 提醒查询失败 {e}')
            return
        elif self.judge_keyword(keyword=["管理员提醒查询", "管理员任务查询", "管理员定时事件查询"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            try:
                Thread(target=self.main_server.Tms.show_jobs,
                       args=(msg.roomid, msg.sender, True)).start()
            except Exception as e:
                OutPut.outPut(f'[-]: 提醒查询失败 {e}')
            return
        elif self.judge_keyword(keyword=["放烟花", "放礼花", "放炸弹", "放鞭炮"],
                                msg=msg.content.strip(), list_bool=True, split_bool=True, equal_bool=True):
            try:
                content_list = msg.content.strip().split()
                name = content_list[0] if content_list else msg.content.strip()

                if len(content_list) == 2:
                    num = min(int(content_list[1]), 10)
                    time_interval = 1.8
                elif len(content_list) == 3:
                    num = min(int(content_list[1]), 10)
                    time_interval = min(float(content_list[2]), 5)
                else:
                    num = 3
                    time_interval = 1.8
            except Exception as e:
                OutPut.outPut(f'[-]: 放烟花、放礼花解析失败 {e}')
                return

            emoji_name = {"放烟花": "烟花", "放礼花": "庆祝", "放炸弹": "炸弹", "放鞭炮": "爆竹"}. \
                get(name, "烟花")
            Thread(target=self.play_fireworks, name="放烟花", args=(msg, num, emoji_name, time_interval)).start()
            return
        elif self.judge_keyword(keyword=["放烟花帮助", "放礼花帮助", "放炸弹帮助", "放鞭炮帮助"],
                                msg=msg.content.strip(), list_bool=True, split_bool=True, equal_bool=True):
            reply = ('示例：\n'
                     '“放烟花”\n'
                     '“放礼花”\n'
                     '“放炸弹 3”\n'
                     '“放鞭炮 3 1.5”')
            self.send_at_msg(msg.roomid, msg.sender, reply)
            return
        # 搜图功能
        elif self.judge_keyword(keyword=["搜图", "搜图片"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            search_msg = msg.content.strip().split(' ', 1)[1].strip()
            save_path = self.Ams.search_image(search_msg)
            if save_path:
                ret = f'[*]: 搜图API接口返回值：{save_path}'
                OutPut.outPut(ret)
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        # 搜歌功能
        elif self.judge_keyword(keyword=["搜歌", "搜歌曲"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            search_msg = msg.content.strip().split(' ', 1)[1].strip()
            music_msg, music_link = self.Ams.search_song(search_msg)
            if music_msg:
                introduce_msg = "请回复“选歌 歌曲序号”进行播放，将以文件形式发送"
                self.send_at_msg(msg.roomid, msg.sender, introduce_msg + '\n\n' + music_msg)
                self.search_link_dict[msg.roomid] = music_link
            return
        elif self.judge_keyword(keyword=["选歌", "选歌曲"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            chose_msg = msg.content.strip().split(' ', 1)[1].strip()
            if chose_msg.isdigit() and 0 < int(chose_msg) <= 20:
                music_link = self.search_link_dict.get(msg.roomid, "")
                if music_link:
                    music_link = music_link + chose_msg
                    music_file_path = self.Ams.down_song_by_url(music_link)
                    if music_file_path:
                        self.wcf.send_file(path=music_file_path, receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["搜番", "搜动漫"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            return
        # 个性表情功能
        elif self.judge_keyword(keyword=["随机表情", "个性表情", "头像表情", "魔法表情", "个性头像"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            head_img = self.get_head_img(msg.sender)
            if head_img:
                save_path = self.Ams.magic_emoji_by_head(head_img)
                if save_path:
                    if save_path.endswith('.gif'):
                        self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                    else:
                        self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["表情选项", "表情菜单", "表情功能"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            reply = '表情选项：\n' + '、'.join(all_emojis_dict_with_jpg_keys)
            self.send_at_msg(msg.roomid, msg.sender, reply)
            return
        elif self.judge_keyword(keyword=all_emojis_dict_with_jpg_keys, msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True, equal_bool=True):
            Thread(target=self.gen_emoji, name="个性表情",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            return
        elif self.judge_keyword(keyword=["测试"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            db_list = self.wcf.get_dbs()
            print(db_list)
            for db in db_list:
                print(self.wcf.get_tables(db))
            return
        elif self.judge_keyword(keyword=["测试图片"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            file_path = f"{PRJ_PATH}/Pic/work.gif"
            if os.path.exists(file_path):
                self.wcf.send_image(path=file_path, receiver=msg.roomid)
                time.sleep(2)
                self.wcf.send_emotion(path=file_path, receiver=msg.roomid)
                time.sleep(2)
                self.wcf.send_file(path=file_path, receiver=msg.roomid)
            return

    # 积分功能
    def Point_Function(self, msg, at_user_lists):
        # 签到功能
        if msg.content.strip() == '签到':
            sign_word = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}' + f'\n签到口令已改为：{self.Sign_Words}'
            self.wcf.send_text(msg=sign_word, receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() == self.Sign_Words:
            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
            room_name = self.Dms.query_room_name(room_id=msg.roomid)
            sign_msg = f'@{wx_name}\n'
            sign_msg += self.Dps.sign(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name)
            self.wcf.send_text(msg=sign_msg, receiver=msg.roomid, aters=msg.sender)
            return
        # AI生图的图片重发
        elif msg.content.strip() in ['重新发送图片', '重新发送', '重发图片']:
            if self.save_path:
                self.send_image_ensure_success(path=self.save_path, receiver=msg.roomid)
        # 赠送积分功能
        elif self.judge_keyword(keyword=self.Send_Point_Words, msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True, split_bool=True):
            Thread(target=self.send_point, name="赠送积分",
                   args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            return
        # 拒绝者
        elif self.judge_keyword(keyword=['拒绝者'], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.get_xiuren_pic, name="拒绝者", args=(msg,)).start()
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
        if self.judge_keyword(keyword=["看图猜成语", "萝卜看图猜成语"], msg=msg.content.strip(), list_bool=True,
                              equal_bool=True):
            Thread(target=self.start_guess_idiom_image, name="看图猜成语", args=(msg,)).start()
            return True
        elif self.judge_keyword(keyword=["成语接龙", "萝卜成语接龙"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_idiom_chain, name="成语接龙", args=(msg,)).start()
            return True
        elif self.judge_keyword(keyword=["表情猜成语", "萝卜表情猜成语"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_guess_idiom_emoji, name="表情猜成语", args=(msg,)).start()
            return True

    def gaming_function(self, msg):
        if self.judge_keyword(keyword=["退出游戏"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            self.game_mode_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'游戏已中止！', receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["重发"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            if self.idiom_pic[msg.roomid]:
                self.send_image_ensure_success(path=self.idiom_pic[msg.roomid], receiver=msg.roomid)
            return
        # 成语解析功能
        elif self.judge_keyword(keyword=["成语解析", "成语解释", "成语查询"], msg=msg.content.strip(), list_bool=True,
                                split_bool=True):
            idiom_name = msg.content.strip().split(' ', 1)[1].strip()
            idiom_msg = f'@{self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' \
                        + self.Ams.get_idiom_explain(idiom_name)
            self.wcf.send_text(msg=idiom_msg, receiver=msg.roomid, aters=msg.sender)
            return
        # 成语接龙提示功能
        elif self.judge_keyword(keyword=["提示", "给点提示", "解释"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            idiom = self.idiom_question.get(msg.roomid, '')
            answer_tip = self.Ams.db_idiom.get_info_by_word(idiom)
            if answer_tip:
                answer = f"成语：{answer_tip.get('word', '')}\n" \
                         f"拼音：{answer_tip.get('pinyin', '')}\n" \
                         f"解释：{answer_tip.get('explanation', '')}\n" \
                         f"出处：{answer_tip.get('derivation', '')}\n" \
                         f"例句：{answer_tip.get('example', '')}"
                self.wcf.send_text(msg=answer, receiver=msg.roomid)
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
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_name in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_name] += 1
                                else:
                                    self.game_point[msg.roomid][wx_name] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_name: 1}
                except Exception as e:
                    OutPut.outPut(f'[-]: 看图猜成语游戏出问题了 :{e}')
            elif self.game_mode_rooms.get(msg.roomid, False) == "idiom_chain":
                try:
                    with self.counter_lock:
                        if self.game_success.get(msg.roomid, False):
                            return
                        if self.judge_keyword(keyword=self.game_answer[msg.roomid],
                                              msg=msg.content.strip(), list_bool=True, equal_bool=True):
                            if msg.content.strip() in self.idiom_usr_answer_history[msg.roomid]:
                                self.wcf.send_text(msg=f'[{msg.content.strip()}]已经接过了！', receiver=msg.roomid)
                                return
                            self.game_success[msg.roomid] = True
                            self.game_answer[msg.roomid] = None
                            self.idiom_usr_answer[msg.roomid] = msg.content.strip()
                            self.idiom_usr_answer_history[msg.roomid].append(msg.content.strip())
                            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
                            # 如果获取不到群昵称，则获取微信昵称
                            if not wx_name:
                                wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 接龙成功！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_name in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_name] += 1
                                else:
                                    self.game_point[msg.roomid][wx_name] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_name: 1}
                except Exception as e:
                    OutPut.outPut(f'[-]: 成语接龙游戏出问题了 :{e}')
            elif self.game_mode_rooms.get(msg.roomid, False) == "guess_idiom_emoji":
                try:
                    with self.counter_lock:
                        if self.game_success.get(msg.roomid, False):
                            return
                        if self.judge_keyword(keyword=[self.game_answer[msg.roomid]],
                                              msg=msg.content.strip(), list_bool=True, equal_bool=True):
                            self.game_success[msg.roomid] = True
                            self.game_answer[msg.roomid] = None
                            wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
                            # 如果获取不到群昵称，则获取微信昵称
                            if not wx_name:
                                wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_name in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_name] += 1
                                else:
                                    self.game_point[msg.roomid][wx_name] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_name: 1}
                except Exception as e:
                    OutPut.outPut(f'[-]: 表情猜成语游戏出问题了 :{e}')

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
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                self.wcf.send_text(msg=f'第{i + 1}轮题目：', receiver=msg.roomid)
                self.wcf.send_text(msg='请在六十秒内回答，否则将跳过此题', receiver=msg.roomid)
                cur_time = time.time()
                flag_tip = False
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
                    if time.time() - cur_time > 40 and not flag_tip:
                        answer = idiom_data.get("答案", "")
                        answer_tip = answer[0] + ' ? ' * (len(answer) - 2) + answer[-1]
                        msg_tip = f'还剩 20 秒！\n答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.5)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
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
            OutPut.outPut(f'[-]: 看图猜成语游戏出问题了 :{e}')
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
        self.idiom_usr_answer_history[msg.roomid] = []
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
                self.idiom_question[msg.roomid] = idiom
                if not self.game_mode_rooms.get(msg.roomid, False):
                    # 清空游戏数据
                    self.game_mode_rooms[msg.roomid] = False
                    self.game_point[msg.roomid] = {}
                    self.game_answer[msg.roomid] = None
                    self.game_success[msg.roomid] = False
                    self.idiom_usr_answer[msg.roomid] = None
                    self.idiom_usr_answer_history[msg.roomid] = []
                    self.idiom_question[msg.roomid] = None
                    return
                answers = self.Ams.db_idiom.get_words_by_word(idiom)
                if not answers:
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                self.game_answer[msg.roomid] = answers
                self.wcf.send_text(msg=f'第{i + 1}轮题目：【{idiom}】', receiver=msg.roomid)
                self.wcf.send_text(msg='请在六十秒内回答，否则结束游戏', receiver=msg.roomid)
                cur_time = time.time()
                flag_tip = False
                random_answer = random.choice(answers)
                while time.time() - cur_time < 61:
                    if not self.game_mode_rooms.get(msg.roomid, False):
                        # 清空游戏数据
                        self.game_mode_rooms[msg.roomid] = False
                        self.game_point[msg.roomid] = {}
                        self.game_answer[msg.roomid] = None
                        self.game_success[msg.roomid] = False
                        self.idiom_usr_answer[msg.roomid] = None
                        self.idiom_usr_answer_history[msg.roomid] = []
                        self.idiom_question[msg.roomid] = None
                        return
                    if self.game_success.get(msg.roomid, False):
                        break
                    if time.time() - cur_time > 40 and not flag_tip:
                        answer = random_answer
                        answer_tip = answer[0] + ' ? ' * (len(answer) - 2) + answer[-1]
                        msg_tip = f'还剩 20 秒！\n参考答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.5)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    self.wcf.send_text(msg=f'没有人接龙成功！\n'
                                           f'参考答案：{random_answer}', receiver=msg.roomid)
                    answer_data = self.Ams.db_idiom.get_info_by_word(random_answer)
                    if answer_data:
                        answer = f"成语：{answer_data.get('word', '')}\n" \
                                 f"拼音：{answer_data.get('pinyin', '')}\n" \
                                 f"解释：{answer_data.get('explanation', '')}\n" \
                                 f"出处：{answer_data.get('derivation', '')}\n" \
                                 f"例句：{answer_data.get('example', '')}"
                        self.wcf.send_text(msg=answer, receiver=msg.roomid)
                    break
                usr_answer = self.idiom_usr_answer[msg.roomid]
                idiom_lst = self.Ams.db_idiom.get_words_by_word(usr_answer)
                if not idiom_lst:
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                idiom = random.choice(idiom_lst)
                time.sleep(0.3)
            msg_over = ["游戏结束！"]
            if msg.roomid in self.game_point.keys():
                for wx_name, point in self.game_point[msg.roomid].items():
                    msg_over.append(f"{wx_name}：{point} 分")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[-]: 成语接龙游戏出问题了：{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False
            self.idiom_usr_answer[msg.roomid] = None
            self.idiom_usr_answer_history[msg.roomid] = []
            self.idiom_question[msg.roomid] = None

    # 表情猜成语
    def start_guess_idiom_emoji(self, msg):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n表情猜成语游戏开始，总共五轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。',
                           receiver=msg.roomid, aters=msg.sender)
        self.game_mode_rooms[msg.roomid] = "guess_idiom_emoji"
        try:
            for i in range(5):
                if not self.game_mode_rooms.get(msg.roomid, False):
                    # 清空游戏数据
                    self.game_mode_rooms[msg.roomid] = False
                    self.game_point[msg.roomid] = {}
                    self.game_answer[msg.roomid] = None
                    self.game_success[msg.roomid] = False
                    return
                while True:
                    # num = random.randint(1, 10305)
                    # emoji_info = self.Ams.db_emoji.get_info_by_id(num)
                    num = random.randint(1, 1653)
                    emoji_info = self.Ams.db_emoji.get_common_idiom_info_by_id(num)
                    emoji = emoji_info.get("emoji", "")
                    idiom = emoji_info.get("idiom", "")
                    idiom_data = self.Ams.db_idiom.get_info_by_word(idiom)
                    if idiom_data:
                        break
                self.game_answer[msg.roomid] = idiom
                self.wcf.send_text(msg=f'第{i + 1}轮题目：\n{emoji}', receiver=msg.roomid)
                self.wcf.send_text(msg='请在六十秒内回答，否则将跳过此题', receiver=msg.roomid)
                cur_time = time.time()
                flag_tip = False
                while time.time() - cur_time < 61:
                    if not self.game_mode_rooms.get(msg.roomid, False):
                        # 清空游戏数据
                        self.game_mode_rooms[msg.roomid] = False
                        self.game_point[msg.roomid] = {}
                        self.game_answer[msg.roomid] = None
                        self.game_success[msg.roomid] = False
                        return
                    if self.game_success.get(msg.roomid, False):
                        break
                    if time.time() - cur_time > 40 and not flag_tip:
                        answer = idiom
                        answer_tip = answer[0] + ' ? ' * (len(answer) - 2) + answer[-1]
                        msg_tip = f'还剩 20 秒！\n答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.5)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    self.wcf.send_text(msg='没有人回答正确！', receiver=msg.roomid)
                answer = f"答案：{idiom_data.get('word', '')}\n" \
                         f"拼音：{idiom_data.get('pinyin', '')}\n" \
                         f"解释：{idiom_data.get('explanation', '')}\n" \
                         f"出处：{idiom_data.get('derivation', '')}\n" \
                         f"例句：{idiom_data.get('example', '')}"
                self.wcf.send_text(msg=answer, receiver=msg.roomid)
                time.sleep(0.3)
            msg_over = ["游戏结束！"]
            if msg.roomid in self.game_point.keys():
                for wx_name, point in self.game_point[msg.roomid].items():
                    msg_over.append(f"{wx_name}：{point} 分")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[-]: 表情猜成语游戏出问题了 :{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False

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

    # 烟花
    def play_fireworks(self, msg, num, type_="烟花", time_interval=1.8):
        for i in range(num):
            self.wcf.send_text(msg=f'[{type_}]', receiver=msg.roomid)
            time.sleep(time_interval)

    # 帮助菜单
    def get_help(self, msg):
        OutPut.outPut(f'[*]: 正在调用Help功能菜单... ...')
        help_pic_path = PRJ_PATH + '/help.jpg'
        self.send_image_ensure_success(path=help_pic_path, receiver=msg.roomid)

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

            if question and question.startswith("画"):
                model = 'image'

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
                        self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                        self.save_path = save_path
                    # usr_msg = f'@{wx_name}\n [{question}]：\n{url}'
                    usr_msg = f'@{wx_name}\n [{question}]：\n图片已发送，请查收！'
                    self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
                else:
                    usr_msg = f'@{wx_name}\n [{question}]：\n图片生成失败！'
                    self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
        # 不是管理员
        else:
            if msg.sender in self.block_wx_ids:
                return
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

                if question and question.startswith("画"):
                    model = 'image'
                    question = question[1:]

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
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
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

    def get_xiuren_pic(self, msg):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.wcf.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次操作不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            pic_path = self.get_xiuren_pic_path()
            self.send_image_ensure_success(path=pic_path, receiver=msg.roomid)
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
                self.send_image_ensure_success(path=pic_path, receiver=msg.roomid)
            else:
                send_msg = f'@{wx_name} 积分不足, 请求管理员或其它群友给你施舍点'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 赠送积分
    def send_point(self, msg, content, at_user_lists):
        try:
            OutPut.outPut(f'[*]: 赠送积分接口接收到的消息: {content}')
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

    # 赠送积分
    def gen_emoji(self, msg, content, at_user_lists):
        try:
            OutPut.outPut(f'[*]: 个性表情接口接收到的消息: {content}')
            for give_sender in at_user_lists:
                head_img = self.get_head_img(give_sender)
                if head_img:
                    emoji = all_emojis_dict_with_jpg.get(content)
                    save_path = self.Ams.magic_emoji_by_head_and_emoji(head_img, emoji)
                    if save_path:
                        if save_path.endswith('.gif'):
                            self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                        else:
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[~]: 个性表情出了点小问题 :{e}')

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

    # 屏蔽个人消息
    def block_personal_msg(self, sender, room_id, wx_ids):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                self.block_wx_ids.append(wx_id) if wx_id not in self.block_wx_ids else None
                block_user_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = f'@{wx_name}\n群友 [{block_user_name}] 消息已被屏蔽'
                OutPut.outPut(msg)
                self.wcf.send_text(msg=msg, receiver=room_id, aters=sender)

    # 解除屏蔽个人消息
    def unblock_personal_msg(self, sender, room_id, wx_ids):
        wx_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                self.block_wx_ids.remove(wx_id) if wx_id in self.block_wx_ids else None
                unblock_user_name = self.wcf.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = f'@{wx_name}\n群友 [{unblock_user_name}] 消息已解除屏蔽'
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
    # TODO: 出现过异常，暂不确定原因，有可能是“退出的群聊”获取不到群昵称导致
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
            OutPut.outPut(f'[*]: 减少积分接口接收到的消息: {content}')
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
    @staticmethod
    def judge_keyword(keyword, msg, list_bool=False, equal_bool=False, in_bool=False,
                      split_bool=False):
        try:
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
        except Exception as e:
            OutPut.outPut(f'[-]: 关键词判断出现错误, 错误信息: {e}')
            return False

    def send_music_message(self, digest, url, receiver):
        self.wcf.send_rich_text(name='点歌',
                                account='',
                                title='MyFreeMP3',
                                digest=digest,
                                url=url,
                                thumburl='https://tool.liumingye.cn/music/img/pwa-192x192.png',
                                receiver=receiver)

    @staticmethod
    def get_xiuren_pic_path():
        root_dir = r'E:/system/XiuRen_jpgs2'

        def generate_path():
            image_number = random.randint(1, 5984)
            return f"{root_dir}/{image_number}.jpg"

        while True:
            random_path = generate_path()
            if not check_file(random_path):
                print(f"文件 {random_path} 不存在或大小大于5KB，重新生成...")
            else:
                print(f"文件 {random_path}")
                return random_path

    def recall_msg(self, msg):
        try:
            sql_query = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                        f'WHERE IsSender = 1 AND StrTalker = "{msg.roomid}" ORDER BY localId DESC LIMIT 1;'
            res = self.wcf.query_sql("MSG0.db", sql_query)
            print(f"recall msg res = {res}")
            # 撤回消息ID
            msg_svr_id = res[0].get('MsgSvrID')
            if msg_svr_id == 0:
                OutPut.outPut(f'[-]: 撤回消息失败，消息ID为0')
                return
            self.wcf.revoke_msg(msg_svr_id)
        except Exception as e:
            OutPut.outPut(f'[-]: 撤回消息出现错误，错误信息: {e}')

    def get_head_img(self, wxid):
        try:
            img_dir = PRJ_PATH + '/Cache/Head_Img_Cache'
            os.makedirs(img_dir, exist_ok=True)
            file_path = f'{img_dir}/{wxid}.jpg'
            if os.path.exists(file_path):
                return file_path

            time.sleep(0.5)
            sql_query = f'SELECT usrName,smallHeadBuf FROM ContactHeadImg1 WHERE usrName="{wxid}";'
            res = self.wcf.query_sql("Misc.db", sql_query)
            # print(f"head img res = {res}")

            if not res:
                OutPut.outPut(f'[-]: 获取头像失败，未找到头像信息')
                return
            head_img_buf = res[0].get('smallHeadBuf')

            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(head_img_buf)
            OutPut.outPut(f'[+]: 获取头像成功，头像路径: {file_path}')

            return file_path
        except Exception as e:
            OutPut.outPut(f'[-]: 获取头像出现错误，错误信息: {e}')

    def send_at_msg(self, roomid, wxid, content):
        at_msg = f"@{self.wcf.get_alias_in_chatroom(roomid=roomid, wxid=wxid)}\n{content}"
        self.wcf.send_text(msg=at_msg, receiver=roomid, aters=wxid)

    def send_image_ensure_success(self, path, receiver, retry_count=0):
        if not os.path.exists(path):
            return
        try:
            print(self.wcf.send_image(path=path, receiver=receiver))
            time.sleep(0.2)
            sql_query = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                        f'WHERE IsSender = 1 AND Type = 3 AND StrTalker = "{receiver}" ORDER BY localId DESC LIMIT 1;'
            res = self.wcf.query_sql("MSG0.db", sql_query)
            print(f"res = {res}")
            local_id = res[0].get('localId')

            def ensure(local_id, path, receiver):
                time.sleep(5)
                sql_query_again = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                                  f'WHERE localId = {local_id};'
                res_again = self.wcf.query_sql("MSG0.db", sql_query_again)
                print(f"res_again = {res_again}")
                # 撤回消息ID
                msg_svr_id = res_again[0].get('MsgSvrID')
                if msg_svr_id == 0:
                    OutPut.outPut('[-]: 图片发送失败，重新发送，回调中...')
                    if retry_count < 5:
                        return self.send_image_ensure_success(path, receiver, retry_count + 1)
                    else:
                        OutPut.outPut('[-]: 已达到最大重试次数，放弃重新发送。')
                return

            thread_ensure = threading.Thread(target=ensure, args=(local_id, path, receiver))
            thread_ensure.start()

        except Exception as e:
            OutPut.outPut(f'[-]: 图片发送失败，错误信息: {e}')
            return

    def send_emotion_ensure_success(self, path, receiver, retry_count=0):
        if not os.path.exists(path):
            return
        try:
            print(self.wcf.send_emotion(path=path, receiver=receiver))
            time.sleep(0.2)
            sql_query = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                        f'WHERE IsSender = 1 AND Type = 47 AND StrTalker = "{receiver}" ORDER BY localId DESC LIMIT 1;'
            res = self.wcf.query_sql("MSG0.db", sql_query)
            print(f"res = {res}")
            local_id = res[0].get('localId')

            def ensure(local_id, path, receiver):
                time.sleep(5)
                sql_query_again = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                                  f'WHERE localId = {local_id};'
                res_again = self.wcf.query_sql("MSG0.db", sql_query_again)
                print(f"res_again = {res_again}")
                # 撤回消息ID
                msg_svr_id = res_again[0].get('MsgSvrID')
                if msg_svr_id == 0:
                    OutPut.outPut('[-]: 表情发送失败，重新发送，回调中...')
                    if retry_count < 5:
                        return self.send_emotion_ensure_success(path, receiver, retry_count + 1)
                    else:
                        OutPut.outPut('[-]: 已达到最大重试次数，放弃重新发送。')
                return

            thread_ensure = threading.Thread(target=ensure, args=(local_id, path, receiver))
            thread_ensure.start()

        except Exception as e:
            OutPut.outPut(f'[-]: 表情发送失败，错误信息: {e}')
            return


def check_file(path):
    if os.path.exists(path):
        file_size = os.path.getsize(path)
        if file_size > 5120:  # 5KB
            return True
    return False


# 保存状态到文件
def save_state_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


# 加载状态从文件
def load_state_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
