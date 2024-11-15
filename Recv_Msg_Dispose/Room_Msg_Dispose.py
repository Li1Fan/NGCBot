import json
import math
import os
import random
import re
import subprocess
import threading
import time
import traceback
import xml.etree.ElementTree as ET
from collections import namedtuple
from datetime import datetime
from threading import Thread

import lz4.block as lb
import requests
import yaml

from Api_Server.Api_Main_Server import Api_Main_Server
from Db_Server.Db_Main_Server import Db_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from OutPut import OutPut
from Util.md5 import calculate_md5
from Util.meme import emoji_value_reply_msg
from Util.meme_info import emoji_value4jpg, emoji_mapping_dict_reverse, emoji_value_custom, emoji_value_double_jpg, \
    api_emoji_value
from Util.util_db import QuestionDB
from Util.util_gif_handle import gif_minimize
from advanced_path import PRJ_PATH


class Room_Msg_Dispose:
    def __init__(self, wcf, main_server):
        self.wcf = wcf
        self.main_server = main_server
        self.bot_wxid = self.main_server.bot_wxid
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

        self.Pic_Words = config['Function_Key_Word']['Pic_Word']
        self.Video_Words = config['Function_Key_Word']['Video_Word']

        self.Morning_Words = config['Function_Key_Word']['Morning_Word']
        self.s60_Words = config['Function_Key_Word']['60s_Word']
        self.Fish_Words = config['Function_Key_Word']['Fish_Word']
        self.Kfc_Words = config['Function_Key_Word']['Kfc_Word']

        self.HelpMenu_Words = config['Function_Key_Word']['Help_Menu']
        self.Custom_Key_Words = config['Custom_KeyWord']

        self.GPT_Words = config['Function_Key_Word']['GPT_Word']
        self.Spark_Words = config['Function_Key_Word']['Spark_Word']
        self.Tencent_Words = config['Function_Key_Word']['Tencent_Word']
        self.Metaso_Words = config['Function_Key_Word']['Metaso_Word']

        self.Sign_Words = config['Point_Config']['Sign']['Word']
        self.Query_Point_Words = config['Point_Config']['Query_Point_Word']
        self.Add_Point_Words = config['Point_Config']['Add_Point_Word']
        self.Del_Point_Words = config['Point_Config']['Del_Point_Word']
        self.Ai_Point = config['Point_Config']['Function_Point']['Ai_point']

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
        self.game_starter = {}

        # 看图猜成语-图片地址
        self.idiom_pic = {}

        # 成语接龙-用户答案
        self.idiom_usr_answer = {}
        # 成语接龙-用户答案历史
        self.idiom_usr_answer_history = {}
        # 成语接龙-题目
        self.idiom_question = {}

        # 一站到底-题目id历史
        self.question_id_history = {}
        # 一站到底-答错人
        self.question_wrong = {}
        # 一站到底-选项
        self.question_options = {}
        # 一站到底-题库
        self.question_db = {}

        # 创建一个线程锁
        self.counter_lock = threading.RLock()
        # 加一个数据库锁
        self.db_lock = threading.RLock()

        # 屏蔽
        self.block_wx_ids = self.state.get('block_wx_ids', [])
        # 防撤回功能 {"room_id": True}
        self.recall_msg_dict = {}
        self.recall_mode_rooms = self.state.get('recall_mode_rooms', {})
        # 启动撤回消息删除线程
        self.thread_del_recall_msg_dict = threading.Thread(target=self.del_recall_msg_dict)
        self.thread_del_recall_msg_dict.start()

        # 搜歌链接
        self.search_link_dict = {}
        # 搜小说链接
        self.search_novel_link_dict = {}

        # 开启进群欢迎
        self.join_room_push_rooms = self.state.get('join_room_push_rooms', {})
        # 开启退群提醒
        self.quit_room_push_rooms = self.state.get('quit_room_push_rooms', {})
        # 形如 { roomid1: {wxid1: 昵称1, wxid2: 昵称2, ...} }
        self.quit_room_numbers = {}

        # 开启退群通知
        self.quit_room_push_room_ids = self.state.get('quit_room_push_room_ids', [])

        # 群每天AI最大调用次数
        self.ai_max_call = {}

        # 自定义关键字
        self.custom_keyword = self.state.get('custom_keyword', {})

        # 限制一下抢劫间隔
        self.rob_time = {}

        # 启动退群提醒线程
        self.thread_quit_room_push = threading.Thread(target=self.quit_room_push)
        self.thread_quit_room_push.start()

        # 开关机器人
        self.robot_switch = self.state.get('robot_switch', True)

        # 是否重启过
        self.is_reboot = False

    def save_state(self):
        self.state = {}
        self.state['block_wx_ids'] = self.block_wx_ids
        self.state['robot_switch'] = self.robot_switch
        self.state['manager_mode_rooms'] = self.manager_mode_rooms
        self.state['recall_mode_rooms'] = self.recall_mode_rooms
        self.state['join_room_push_rooms'] = self.join_room_push_rooms
        self.state['quit_room_push_rooms'] = self.quit_room_push_rooms
        self.state['quit_room_push_room_ids'] = self.quit_room_push_room_ids

        # 排序依据
        order = {'txt': 0, 'pic': 1, 'gif': 1, 'vid': 2}
        # 对 自定义关键字 重新排序
        self.custom_keyword = dict(
            sorted(self.custom_keyword.items(),
                   key=lambda item: (order[item[1]['typ']], len(item[0]), item[1]['is_arg'])))

        self.state['custom_keyword'] = self.custom_keyword
        save_state_file(self.state_json_file, self.state)

    def quit_room_push(self):
        while True:
            for roomid, switch in self.quit_room_push_rooms.items():
                if switch:
                    # threading.Thread(target=self.monitor_quit_room, args=(roomid,)).start()
                    self.monitor_quit_room(roomid)
            time.sleep(55)

    def monitor_quit_room(self, roomid):
        with self.counter_lock:
            try:
                cur_time = time.time()
                members = {}
                quit_members_set = set()
                while time.time() - cur_time < 5:
                    members = self.get_room_numbers(roomid)
                    if not members:
                        return
                    if len(self.quit_room_numbers.get(roomid, {})) == 0:
                        self.quit_room_numbers[roomid] = members
                        return
                    old_members_set = set(self.quit_room_numbers[roomid].keys())
                    new_members_set = set(members.keys())
                    quit_members_set = old_members_set - new_members_set

                    if len(quit_members_set) > 0:
                        time.sleep(0.3)
                        continue
                    else:
                        self.quit_room_numbers[roomid] = members
                        return

                OutPut.outPut(f"[+]: roomid: {roomid}")
                OutPut.outPut(f"[+]: old_members_set: {old_members_set}")
                OutPut.outPut(f"[+]: new_members_set: {new_members_set}")
                for wxid in quit_members_set:
                    for administrator in self.administrators:
                        name_list = self.query_sql("MicroMsg.db",
                                                   f"SELECT UserName, NickName FROM Contact WHERE UserName = '{wxid}';")
                        if not name_list:
                            name = 'unknown'
                        else:
                            name = name_list[0]['NickName']
                        room_name = self.Dms.query_room_name(room_id=roomid)
                        msg = f'退群提醒：\n' \
                              f'群友 [{name}] 退出了群聊 [{room_name}]\n' \
                              f'wxid: {wxid}\n' \
                              f'time: {time.strftime("%y-%m-%d %H:%M:%S", time.localtime())}'
                        self.wcf.send_text(msg=msg, receiver=administrator)
                        # 开启退群通知
                        if roomid in self.quit_room_push_room_ids:
                            self.wcf.send_text(msg=msg, receiver=roomid)
                self.quit_room_numbers[roomid] = members
            except Exception as e:
                pass

    def get_room_numbers(self, roomid):
        with self.db_lock:
            members = self.wcf.get_chatroom_members(roomid)
        if len(members) == 0:
            return {}
        if self.bot_wxid not in members:
            return {}
        for administrator in self.administrators:
            if administrator not in members:
                return {}
        return members

    def del_recall_msg_dict(self):
        while True:
            with self.counter_lock:
                # 删除超过10分钟的撤回消息
                for key in list(self.recall_msg_dict.keys()):
                    if time.time() - self.recall_msg_dict[key]['ts'] > 600:
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
                    wx_name = self.get_wx_name(msg)
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

    def add_custom_keyword(self, msg):
        try:
            msg_lst = msg.content.split(' ')
            if len(msg_lst) == 4:
                _, keyword, url, typ = msg_lst
                res_typ = 'raw'
                is_arg = False
            elif len(msg_lst) == 5:
                _, keyword, url, typ, res_typ = msg_lst
                is_arg = False
            else:
                _, keyword, url, typ, res_typ, is_arg = msg_lst

            if typ not in ['txt', 'pic', 'gif', 'vid']:
                return
            if not url.startswith('http'):
                return
            if res_typ != 'raw' and not res_typ.startswith('json'):
                return
            is_arg = True if is_arg else False

            if keyword not in self.custom_keyword.keys():
                self.custom_keyword[keyword] = {'typ': typ, 'url': url, 'res_typ': res_typ, 'is_arg': is_arg}
                self.wcf.send_text(msg=f'自定义关键字【{keyword}】\n添加成功', receiver=msg.roomid, aters=msg.sender)
                self.save_state()
        except Exception as e:
            OutPut.outPut(f'[-]: 添加自定义关键字失败 {e}')

    def handle_emoji_refer(self, msg):
        try:
            # 引用消息
            content = re.findall(f"<title>(.*?)</title>", msg.content)[0]
            type_, msg_id = re.findall(f"<refermsg>\s*<type>(\d+)</type>\s*<svrid>(\d+)</svrid>", msg.content)[0]
            print(f'Content: {content}')
            print(f'Type: {type_}')
            print(f'SvrId: {msg_id}')
            if type_ == '3':
                if msg_id in self.recall_msg_dict.keys():
                    recall_msg = self.recall_msg_dict[msg_id]
                    file_path = recall_msg.get("content", "")

                    Thread(target=self.gen_emoji_self, name="个性表情",
                           args=(msg, content, [], file_path)).start()
                    OutPut.outPut(f"[+]: 引用消息处理成功 {content}")
                    return
            if type_ == '1':
                refer_content = re.findall(f"<content>(.*?)</content>", msg.content, re.DOTALL)[0]
                content = f"{content} {refer_content}"
                print(f'Compile Content: {content}')
                Msg = namedtuple("Msg", ["roomid", "sender", "content"])
                msg = Msg(msg.roomid, msg.sender, content)
                self.Point_Function(msg, [])
                self.Happy_Function(msg)
        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f"[-]: 引用消息处理失败 {e}")

    def identify_images(self, msg):
        try:
            # 引用消息
            content = re.findall(f"<title>(.*?)</title>", msg.content)[0]
            type_, msg_id = re.findall(f"<refermsg>\s*<type>(\d+)</type>\s*<svrid>(\d+)</svrid>", msg.content)[0]
            print(f'Content: {content}')
            print(f'Type: {type_}')
            print(f'SvrId: {msg_id}')
            if type_ == '3':
                if msg_id in self.recall_msg_dict.keys():
                    recall_msg = self.recall_msg_dict[msg_id]
                    file_path = recall_msg.get("content", "")
                    question = msg.content.split(' ', 1)[1]
                    res = self.Ams.get_ai_identify_images(file_path, question)
                    if res:
                        self.send_at_msg(msg.roomid, msg.sender, res)
                    return
        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f"[-]: 引用消息处理失败 {e}")

    def handle_article_refer(self, msg):
        try:
            # 引用消息
            content = re.findall(f"<title>(.*?)</title>", msg.content)[0]
            type_, msg_id = re.findall(f"<refermsg>\s*<type>(\d+)</type>\s*<svrid>(\d+)</svrid>", msg.content)[0]
            print(f'Content: {content}')
            print(f'Type: {type_}')
            print(f'SvrId: {msg_id}')
            if type_ == '49':
                url = re.search(r'url&gt;(?P<url>.*?)&lt;/url&gt;',
                                str(msg.content).strip(),
                                re.DOTALL)
                if url:
                    url = url.group('url').replace('&amp;', '&').replace('amp;', '')
                    question = "总结一下文章内容，按照标题、简介、核心观点、标签给出回复。以普通文本形式回复，尽可能简洁。"
                    question += f"链接：{url}"
                    res, _ = self.Ams.getHunYuanAi(question)
                    if res:
                        res = res.replace("*", "")
                        self.send_at_msg(msg.roomid, msg.sender, res)
                        return
                    else:
                        self.send_at_msg(msg.roomid, msg.sender, "AI总结失败")
                        return

        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f"[-]: 引用消息处理失败 {e}")

    def handle_txt_refer(self, msg):
        try:
            # 引用消息
            content = re.findall(f"<title>(.*?)</title>", msg.content)[0]
            type_, msg_id = re.findall(f"<refermsg>\s*<type>(\d+)</type>\s*<svrid>(\d+)</svrid>", msg.content)[0]
            print(f'Content: {content}')
            print(f'Type: {type_}')
            print(f'SvrId: {msg_id}')
            if type_ == '1':
                refer_content = re.findall(f"<content>(.*?)</content>", msg.content, re.DOTALL)[0]
                content = f"{content} {refer_content}"
                print(f'Compile Content: {content}')
                Msg = namedtuple("Msg", ["roomid", "sender", "content"])
                msg = Msg(msg.roomid, msg.sender, content)
                self.Point_Function(msg, [])
                self.Happy_Function(msg)
        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f"[-]: 引用消息处理失败 {e}")

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
        # # 数据库异常告警
        # if self.main_server.is_db_error:
        #     if self.is_reboot:
        #         return
        #     self.wcf.send_text(msg='数据库出现错误, 即将自动重启', receiver=self.administrators[0])
        #
        #     # self.wcf.send_text(msg='数据库出现错误, 即将自动重启', receiver=msg.roomid)
        #
        #     def reboot():
        #         # time.sleep(60)
        #         os.chdir(PRJ_PATH + '/Config')
        #         subprocess.Popen(["reboot.exe"])
        #
        #     Thread(target=reboot, name="数据库异常告警", daemon=True).start()
        #     self.is_reboot = True
        #     return
        # 超级管理员功能
        if msg.sender in self.administrators:
            Thread(target=self.Administrator_Function, name="超级管理员处理流程", args=(msg, at_user_lists,)).start()
            return
        # 管理员功能
        elif msg.sender in admin_dicts.keys():
            Thread(target=self.Admin_Function, name="管理员处理流程", args=(msg, at_user_lists)).start()
            return
        # 关机模式下，屏蔽所有消息
        elif not self.robot_switch:
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
        # 添加白名单公众号（订阅文章，推送至群聊） 引用
        elif self.judge_keyword(keyword=["订阅", "订阅推送", "订阅公众号推送"], msg=self.handle_xml_msg(msg),
                                list_bool=True,
                                equal_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.add_white_gh, name="添加白名单公众号", args=(msg,)).start()
            return
        # 移除白名单公众号 引用
        elif self.judge_keyword(keyword=["取消订阅"], msg=self.handle_xml_msg(msg),
                                list_bool=True,
                                equal_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.del_white_gh, name="移除白名单公众号", args=(msg,)).start()
            return
        # 查看白名单公众号
        elif self.judge_keyword(
                keyword=['查看白名单公众号', '白名单公众号', '订阅列表', '订阅清单', '订阅菜单', '订阅公众号列表'],
                msg=msg.content, list_bool=True, equal_bool=True):
            white_gh_dict = self.Dms.show_white_ghs()
            white_gh_values = white_gh_dict.values()
            self.wcf.send_text(msg='、'.join(white_gh_values), receiver=msg.roomid)
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
        # 积分限制功能
        elif msg.content.strip() in ['取消积分限制', '取消积分', '取消限制', '关闭积分限制', '关闭积分', '关闭限制']:
            self.Ai_Point = 0
            self.wcf.send_text(msg='关闭积分限制成功', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['开启积分限制', '开启积分', '开启限制']:
            self.Ai_Point = 10
            self.wcf.send_text(msg='开启积分限制成功', receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() in ['萝卜开机', '萝卜上班', '萝卜开启', '萝卜启动', "开机"]:
            self.robot_switch = True
            self.wcf.send_text(msg='萝卜开机成功', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['萝卜关机', '萝卜下班', '萝卜关闭', '萝卜停止', "关机"]:
            self.robot_switch = False
            self.wcf.send_text(msg='萝卜关机成功', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        # elif msg.content.strip() in ['萝卜重启', "重启"]:
        #     self.robot_switch = False
        #     self.wcf.send_text(msg='萝卜重启中，请等待约 1 min', receiver=msg.roomid, aters=msg.sender)
        #     os.chdir(PRJ_PATH + '/Config')
        #     subprocess.Popen(["reboot.exe"])
        #     return
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
        elif msg.content.strip() in ['清除缓存', '清除缓存信息']:
            self.main_server.Cms.delete_file()
            return
        elif msg.content.strip() in ['开启进群欢迎', '开启进群欢迎功能']:
            self.join_room_push_rooms[msg.roomid] = True
            self.wcf.send_text(msg=f'已开启进群欢迎', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['关闭进群欢迎', '关闭进群欢迎功能']:
            self.join_room_push_rooms[msg.roomid] = False
            self.wcf.send_text(msg=f'已关闭进群欢迎', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['开启退群提醒', '开启退群提醒功能']:
            self.quit_room_push_rooms[msg.roomid] = True
            self.wcf.send_text(msg=f'已开启退群提醒', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['关闭退群提醒', '关闭退群提醒功能']:
            self.quit_room_push_rooms[msg.roomid] = False
            self.quit_room_numbers[msg.roomid] = {}
            self.wcf.send_text(msg=f'已关闭退群提醒', receiver=msg.roomid, aters=msg.sender)
            self.save_state()
            return
        elif msg.content.strip() in ['开启退群通知', '开启退群通知功能']:
            if msg.roomid not in self.quit_room_push_room_ids:
                self.quit_room_push_room_ids.append(msg.roomid)
                self.wcf.send_text(msg=f'已开启退群通知', receiver=msg.roomid, aters=msg.sender)
                self.save_state()
            return
        elif msg.content.strip() in ['关闭退群通知', '关闭退群通知功能']:
            if msg.roomid in self.quit_room_push_room_ids:
                self.quit_room_push_room_ids.remove(msg.roomid)
                self.wcf.send_text(msg=f'已关闭退群通知', receiver=msg.roomid, aters=msg.sender)
                self.save_state()
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
                result = self.query_sql(db, query)
                result = str(result)
                self.wcf.send_text(msg=result, receiver=msg.roomid, aters=msg.sender)
            except Exception as e:
                OutPut.outPut(f'[-]: 查询数据库失败 {e}')
            return
        elif self.judge_keyword(keyword=["归零", '积分归零', '重置积分', '清空积分', '积分重置'],
                                msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True,
                                equal_bool=True):
            for at_user in at_user_lists:
                self.reset_point(msg.roomid, at_user)
                return
        elif self.judge_keyword(keyword=["归零", '积分归零', '重置积分', '清空积分', '积分重置'],
                                msg=msg.content.strip(),
                                list_bool=True,
                                equal_bool=True):
            self.reset_point(msg.roomid, msg.sender)
            return

        # 处理图片引用消息49-57-3
        if self.judge_keyword(keyword=["表情", "个性表情"], msg=self.handle_xml_msg(msg), list_bool=True,
                              split_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.handle_emoji_refer, name="表情引用", args=(msg,)).start()
            return

        # 处理图片引用消息49-57-3
        if self.judge_keyword(keyword=["识图", "AI识图"], msg=self.handle_xml_msg(msg), list_bool=True,
                              split_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.identify_images, name="识图", args=(msg,)).start()
            return

        # 处理推文引用消息49-57-49，总结推文
        if self.judge_keyword(keyword=["总结一下", "总结", "总结文章"], msg=self.handle_xml_msg(msg), list_bool=True,
                              equal_bool=True) and self.handle_xml_type(msg) == '57':
            Thread(target=self.handle_article_refer, name="总结推文", args=(msg,)).start()
            return

        # 添加自定义关键字 txt/pic/vid 关键字 地址 raw/json_image/json_video arg/!arg
        if self.judge_keyword(keyword=["添加自定义关键字", "添加自定义"], msg=msg.content, list_bool=True,
                              split_bool=True):
            Thread(target=self.add_custom_keyword, name="添加自定义关键字", args=(msg,)).start()
            return
        elif self.judge_keyword(keyword=["删除自定义关键字", "删除自定义"], msg=msg.content, list_bool=True,
                                split_bool=True):
            try:
                _, keyword = msg.content.split(' ', 1)
                if keyword in self.custom_keyword.keys():
                    self.custom_keyword.pop(keyword)
                    self.wcf.send_text(msg=f'自定义关键字【{keyword}】\n删除成功', receiver=msg.roomid, aters=msg.sender)
                    self.save_state()
            except Exception as e:
                OutPut.outPut(f'[-]: 删除自定义关键字失败 {e}')
            return
        elif self.judge_keyword(keyword=["查看自定义关键字", "查看自定义", "自定义查看"], msg=msg.content,
                                list_bool=True,
                                equal_bool=True):
            msg_list = []
            for key, value in self.custom_keyword.items():
                msg_list.append(f'{key}\n{value}')
            self.wcf.send_text(msg='\n\n'.join(msg_list), receiver=msg.roomid)
            return
        elif self.judge_keyword(
                keyword=["自定义回复", "自定义回复功能", "自定义回复帮助", "自定义关键字", "自定义关键字功能",
                         "自定义"],
                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            reply = ('自定义关键字功能：\n' +
                     "添加自定义 关键字 url txt/pic/vid raw/json_* arg/*" + '\n' +
                     "删除自定义 关键字" + '\n' +
                     "查看自定义")
            self.wcf.send_text(msg=reply, receiver=msg.roomid)
            return
        Thread(target=self.OrdinaryRoom_Function, name="普通群聊功能", args=(msg, at_user_lists)).start()

    # 白名单群聊功能
    def WhiteRoom_Function(self, msg, at_user_lists):
        Thread(target=self.OrdinaryRoom_Function, name="普通群聊功能", args=(msg, at_user_lists)).start()

    # 黑名单群聊功能
    def BlackRoom_Function(self, msg, at_user_lists):
        Thread(target=self.Point_Function, name="积分功能", args=(msg, at_user_lists)).start()

    # 普通群聊功能
    def OrdinaryRoom_Function(self, msg, at_user_lists):
        Thread(target=self.Happy_Function, name="娱乐功能", args=(msg, at_user_lists)).start()
        Thread(target=self.Point_Function, name="积分功能", args=(msg, at_user_lists,)).start()

    # 娱乐功能
    def Happy_Function(self, msg, at_user_lists=None):
        if msg.sender in self.block_wx_ids:
            return

        if at_user_lists is None:
            at_user_lists = []

        if self.game_mode_rooms.get(msg.roomid, False):
            self.gaming_function(msg)
            return
        if self.game_function(msg):
            return

        # 处理引用消息49-57-1，文本消息，直接作为参数，再给机器人处理
        if self.handle_xml_type(msg) == '57':
            Thread(target=self.handle_txt_refer, name="文本消息", args=(msg,)).start()
            return

        # 天气查询
        if self.judge_keyword(keyword=['天气查询', '查询天气'], msg=msg.content.strip(), list_bool=True,
                              split_bool=True):
            weather_msg = self.Ams.query_weather(msg.content.strip())
            if weather_msg:
                self.send_at_msg(msg.roomid, msg.sender, weather_msg)
            return

        # 早安寄语
        elif self.judge_keyword(keyword=self.Morning_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            morning_msg = self.Ams.get_morning()
            if morning_msg:
                self.send_at_msg(msg.roomid, msg.sender, morning_msg)
            return
        # 60s
        elif self.judge_keyword(keyword=self.s60_Words + ["60s图片", "60图片", "60pic", "60spic"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            save_path = self.Ams.get_60s_pic()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        # 摸鱼日记
        elif self.judge_keyword(keyword=self.Fish_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            save_path = self.Ams.get_fish()
            if save_path:
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
        # 疯狂星期四文案
        elif self.judge_keyword(keyword=self.Kfc_Words, msg=msg.content.strip(), list_bool=True, equal_bool=True):
            kfc_msg = self.Ams.get_kfc()
            if kfc_msg:
                self.send_at_msg(msg.roomid, msg.sender, kfc_msg.replace('\\n', '\n'))
            return

        # 自定义回复
        elif self.judge_keyword(keyword=self.custom_keyword.keys(), msg=msg.content.strip(), list_bool=True,
                                equal_bool=True, split_bool=True):
            if '呀' in msg.content.strip() or '鸭' in msg.content.strip():
                Thread(target=self.deduct_points_func, name="付费回复",
                       args=(msg, self.custom_reply,
                             msg,)).start()
                return
            Thread(target=self.custom_reply, name="自定义回复", args=(msg,)).start()
            return

        # 每日英语
        elif self.judge_keyword(keyword=["每日英语", "来一句英语"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            english_msg = self.Ams.get_daily_english()
            if english_msg:
                self.send_at_msg(msg.roomid, msg.sender, english_msg)
            return
        # 虎扑热搜
        elif self.judge_keyword(keyword=["虎扑热搜"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            hupu_msg = self.Ams.get_hupu()
            if hupu_msg:
                self.wcf.send_text(msg=hupu_msg[0], receiver=msg.roomid, aters=msg.sender)
                # self.wcf.send_text(msg=hupu_msg[1], receiver=msg.roomid, aters=msg.sender)
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

        # # 点歌功能
        # elif self.judge_keyword(keyword=["点歌", "听歌"], msg=msg.content.strip(), list_bool=True, split_bool=True):
        #     music_name = msg.content.strip().split(' ', 1)[1].strip()
        #     digest = '搜索歌曲：{}'.format(music_name)
        #     url = 'https://tool.liumingye.cn/music/#/search/M/song/{}'.format(music_name)
        #     self.send_music_message(digest, url, msg.roomid)
        #     return
        # elif msg.content.strip() in ["点歌", "听歌"]:
        #     digest = '点击进入点歌页面'
        #     url = 'https://tool.liumingye.cn/music/'
        #     self.send_music_message(digest, url, msg.roomid)
        #     return

        elif self.judge_keyword(keyword=["点歌"],
                                msg=msg.content.strip(),
                                list_bool=True,
                                split_bool=True):
            try:
                music_name = msg.content.strip().split(' ', 1)[1].strip()
                url = f"https://www.hhlqilongzhu.cn/api/dg_kgmusic.php?gm={music_name}&n=1"
                # url = f"https://www.hhlqilongzhu.cn/api/dg_mgmusic_24bit.php?msg={music_name}&n=1"

                song_info = self.Ams.parse_song_url(url)
                return self.send_music(msg, song_info)
            except Exception as e:
                OutPut.outPut(f'[-]: 点歌失败 {e}')
                print(traceback.format_exc())
            return

        elif self.judge_keyword(keyword=["随机音乐", "随机歌曲", "随机点歌", "随机点歌曲"], msg=msg.content.strip(),
                                list_bool=True, equal_bool=True):
            song_info = self.Ams.get_random_music()
            return self.send_music(msg, song_info)

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
            english_content = self.Ams.get_translate(chinese_content) or self.Ams.get_translate_by_api(chinese_content)
            if not english_content:
                OutPut.outPut(f'[-]: 翻译接口出错')
                return
            trans_msg = f'原文：{chinese_content}\n' \
                        + f'译文：{english_content}'
            self.send_at_msg(msg.roomid, msg.sender, trans_msg)
            return
        # help帮助菜单
        elif self.judge_keyword(keyword=self.HelpMenu_Words + ["功能", "萝卜功能", "萝卜菜单"], msg=msg.content.strip(),
                                list_bool=True, equal_bool=True):
            Thread(target=self.get_help, name="Help帮助菜单", args=(msg,)).start()
            return
        elif self.judge_keyword(keyword=["自定义菜单", "关键字菜单"], msg=msg.content, list_bool=True,
                                equal_bool=True):
            msg_list = [key + "*" if self.custom_keyword.get(key).get("is_arg") else key
                        for key in self.custom_keyword.keys()]

            msg_list = ["\n运势" if item == "运势" else item for item in msg_list]
            msg_list = ["\n随机视频" if item == "随机视频" else item for item in msg_list]

            msg_list = [key for key in msg_list if '呀' not in key]
            msg_list = [key for key in msg_list if '鸭' not in key]
            self.wcf.send_text(msg='、 '.join(msg_list), receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["自定义完整菜单", "关键字完整菜单"], msg=msg.content, list_bool=True,
                                equal_bool=True):
            if msg.sender not in self.administrators:
                return
            msg_list = [key + "*" if self.custom_keyword.get(key).get("is_arg") else key
                        for key in self.custom_keyword.keys()]

            msg_list = ["\n运势" if item == "运势" else item for item in msg_list]
            msg_list = ["\n随机视频" if item == "随机视频" else item for item in msg_list]

            self.wcf.send_text(msg='、 '.join(msg_list), receiver=msg.roomid)
            return
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
        elif self.judge_keyword(keyword=["搜书", "搜小说"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            search_msg = msg.content.strip().split(' ', 1)[1].strip()
            novel_msg, novel_link = self.Ams.search_novel(search_msg)
            if novel_msg:
                introduce_msg = "请回复“选书 小说序号”进行下载，将以文件形式发送"
                self.send_at_msg(msg.roomid, msg.sender, introduce_msg + '\n\n' + novel_msg)
                self.search_novel_link_dict[msg.roomid] = novel_link
            return
        elif self.judge_keyword(keyword=["选书", "选小说"], msg=msg.content.strip(), list_bool=True, split_bool=True):
            chose_msg = msg.content.strip().split(' ', 1)[1].strip()
            if chose_msg.isdigit() and 0 < int(chose_msg) <= 60:
                novel_link = self.search_novel_link_dict.get(msg.roomid, "")
                if novel_link:
                    novel_link = novel_link + chose_msg
                    novel_file_path = self.Ams.down_novel_by_url(novel_link)
                    if novel_file_path:
                        self.wcf.send_file(path=novel_file_path, receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=["表情选项", "表情菜单", "表情功能"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            reply = '表情选项：\n' + emoji_value_reply_msg
            self.send_at_msg(msg.roomid, msg.sender, reply)
            return
        elif self.judge_keyword(keyword=["表情用法", "表情帮助", "表情使用", "表情使用帮助", "表情", "个性表情"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            reply = '表情使用：\n' \
                    '1、表情 XXX\n' + \
                    '2、@某人 XXX\n' + \
                    '3、随机表情\n\n' + \
                    '完整表情列表，请回复“表情菜单”'
            self.send_at_msg(msg.roomid, msg.sender, reply)
            return
        elif self.judge_keyword(keyword=["测试"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            db_list = self.wcf.get_dbs()
            print(db_list)
            for db in db_list:
                print(self.wcf.get_tables(db))
            return
            # self.send_at_all_msg(msg.roomid, "测试")
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
        if msg.sender in self.block_wx_ids:
            return

        # 签到功能
        if msg.content.strip() == '签到':
            sign_word = f'@{self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}' + f'\n签到口令已改为：{self.Sign_Words}'
            self.wcf.send_text(msg=sign_word, receiver=msg.roomid, aters=msg.sender)
            return
        elif msg.content.strip() == self.Sign_Words:
            wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
            room_name = self.Dms.query_room_name(room_id=msg.roomid)
            sign_msg = f'@{wx_name}\n'
            sign_msg += self.Dps.sign(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name)
            self.wcf.send_text(msg=sign_msg, receiver=msg.roomid, aters=msg.sender)
            return
        elif self.judge_keyword(keyword=["积分排行榜", "积分排行", "积分排名"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            points = self.Dps.query_top(room_id=msg.roomid)
            if points:
                reply = '积分排行榜：\n'
                for rand, (name, point) in enumerate(points):
                    name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=name).strip()
                    reply += f'{rand + 1}、{name}：{point}分\n'
                    reply = reply.replace("\n\n", "\n")
                self.send_at_msg(msg.roomid, msg.sender, reply)
        elif self.judge_keyword(keyword=["积分倒数排行榜", "积分倒数排行", "积分倒数排名"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            points = self.Dps.query_bottom(room_id=msg.roomid)
            if points:
                reply = '积分倒数排行榜：\n'
                for rand, (name, point) in enumerate(points):
                    name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=name).strip()
                    reply += f'{rand + 1}、{name}：{point}分\n'
                    reply = reply.replace("\n\n", "\n")
                self.send_at_msg(msg.roomid, msg.sender, reply)
        # 个性表情功能
        elif self.judge_keyword(keyword=["随机表情"],
                                msg=msg.content.strip(), list_bool=True, equal_bool=True):
            # Thread(target=self.gen_random_emoji, name="随机表情",args=(msg,)).start()
            Thread(target=self.deduct_points_func, name="随机表情",
                   args=(msg, self.gen_random_emoji,
                         msg,)).start()
            return
        elif self.judge_keyword(keyword=emoji_value4jpg + emoji_value_custom + emoji_value_double_jpg,
                                msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True, equal_bool=True, split_bool=True):
            # Thread(target=self.gen_emoji, name="个性表情",
            #        args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
            Thread(target=self.deduct_points_func, name="表情",
                   args=(msg, self.gen_emoji,
                         msg, self.handle_atMsg(msg, at_user_lists),
                         at_user_lists,)).start()
            return
        elif self.judge_keyword(keyword=["表情", "个性表情"],
                                msg=msg.content.strip(),
                                list_bool=True, split_bool=True):
            # Thread(target=self.gen_emoji_self, name="个性表情",
            #        args=(msg, msg.content.strip(), at_user_lists,)).start()
            Thread(target=self.deduct_points_func, name="表情",
                   args=(msg, self.gen_emoji_self,
                         msg, msg.content.strip(), at_user_lists,)).start()
            return
        elif self.judge_keyword(keyword=["抢劫", "打劫"],
                                msg=self.handle_atMsg(msg, at_user_lists),
                                list_bool=True, equal_bool=True):
            Thread(target=self.robbery_point, name="抢劫", args=(msg, at_user_lists)).start()
            return
        elif self.judge_keyword(keyword=["购买冷却时间", "购买冷却"],
                                msg=msg.content.strip(),
                                list_bool=True, equal_bool=True):
            Thread(target=self.deduct_points_func_general, name="够买冷却时间",
                   args=(msg, 8, "您购买了冷却时间恢复",
                         self.buy_cooling_time, msg)).start()
            return

        # 美女图片
        elif self.judge_keyword(keyword=self.Pic_Words, msg=msg.content, list_bool=True, equal_bool=True):
            def fun_pic():
                save_path = self.Ams.get_girl_pic()
                if save_path:
                    self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                return

            Thread(target=self.deduct_points_func, name="美女图片",
                   args=(msg, fun_pic)).start()
            return
        # 美女视频
        elif self.judge_keyword(keyword=self.Video_Words, msg=msg.content, list_bool=True, equal_bool=True):
            def fun_video():
                save_path = self.Ams.get_girl_video()
                if check_file(save_path):
                    self.wcf.send_file(path=save_path, receiver=msg.roomid)
                return

            Thread(target=self.deduct_points_func, name="美女视频",
                   args=(msg, fun_video)).start()
        # # 小姐姐视频
        # elif self.judge_keyword(keyword=["随机小姐姐模式"], msg=msg.content, list_bool=True, equal_bool=True):
        #     def fun_video():
        #         try:
        #             title = '随机小姐姐'
        #             digest = '恭喜你解锁隐藏功能，开启刷手机模式！'
        #             # url = 'https://mm.diskgirl.com'
        #             url = requests.get("https://api.yujn.cn/api/dwz.php?url=https://mm.diskgirl.com").json().get(
        #                 "msg").get("url")
        #             print("短链接生成地址：", url)
        #             thumb_url = self.get_head_img_pro_url(self.wcf.self_wxid)
        #             if not thumb_url:
        #                 thumb_url = ''
        #             receiver = msg.roomid
        #             self.send_video_message(title=title, digest=digest, url=url, thumburl=thumb_url,
        #                                     receiver=receiver)
        #         except Exception as e:
        #             print(e)
        #
        #     Thread(target=self.deduct_points_func_general, name="小姐姐视频",
        #            args=(msg, 50, "您使用了隐藏福利功能",
        #                  fun_video)).start()

        # AI生图的图片重发
        elif msg.content.strip() in ['重新发送图片', '重新发送', '重发图片']:
            if self.save_path:
                self.send_image_ensure_success(path=self.save_path, receiver=msg.roomid)
        # # 赠送积分功能
        # elif self.judge_keyword(keyword=self.Send_Point_Words, msg=self.handle_atMsg(msg, at_user_lists),
        #                         list_bool=True, split_bool=True):
        #     Thread(target=self.send_point, name="赠送积分",
        #            args=(msg, self.handle_atMsg(msg, at_user_lists), at_user_lists,)).start()
        #     return
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
        # 腾讯混元对话
        elif self.judge_keyword(keyword=self.Tencent_Words,
                                msg=msg.content.strip(), list_bool=True,
                                split_bool=True):
            Thread(target=self.get_ai, name="腾讯混元对话", args=(msg, at_user_lists, 'tx')).start()
            return
        # 秘塔搜索
        elif self.judge_keyword(keyword=self.Metaso_Words, msg=msg.content.strip(), list_bool=True, split_bool=True):
            Thread(target=self.get_ai, name="秘塔搜索", args=(msg, at_user_lists, 'metaso')).start()
            return
        elif ' ' in msg.content.strip() and msg.content.strip().split(' ')[0] in ['秘塔搜索', '秘塔AI搜索']:
            question = msg.content.strip().split(' ', 1)[1]
            self.wcf.send_rich_text(name='秘塔AI搜索',
                                    account='gh_d6931e1cbcd9',
                                    title='秘塔AI搜索',
                                    digest=question,
                                    url='https://metaso.cn/?q=%s' % question,
                                    thumburl='https://metaso.cn/apple-touch-icon.png',
                                    receiver=msg.roomid)
            return
        elif self.judge_keyword(keyword=['百度百科'], msg=msg.content.strip(), list_bool=True, split_bool=True):
            question = msg.content.strip().split(' ', 1)[1]
            res, content = self.Ams.get_baidu_baike(question)
            if not res:
                self.send_at_msg(msg.roomid, msg.sender, content)
                return
            self.wcf.send_rich_text(name='百度App',
                                    account='gh_5fc573ba9375',
                                    title=f'{question}_百度百科',
                                    digest=content.get('result'),
                                    url=content.get('url'),
                                    thumburl=content.get('image'),
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
        if self.judge_keyword(keyword=["看图猜成语无尽模式", "萝卜看图猜成语无尽模式"], msg=msg.content.strip(),
                              list_bool=True,
                              equal_bool=True):
            Thread(target=self.start_guess_idiom_image, name="看图猜成语", args=(msg, 999)).start()
            return True
        elif self.judge_keyword(keyword=["成语接龙", "萝卜成语接龙"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_idiom_chain, name="成语接龙", args=(msg,)).start()
            return True
        elif self.judge_keyword(keyword=["成语接龙无尽模式", "萝卜成语接龙无尽模式"], msg=msg.content.strip(),
                                list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_idiom_chain, name="成语接龙", args=(msg, 999)).start()
            return True
        elif self.judge_keyword(keyword=["表情猜成语", "萝卜表情猜成语"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_guess_idiom_emoji, name="表情猜成语", args=(msg,)).start()
            return True
        elif self.judge_keyword(keyword=["表情猜成语无尽模式", "萝卜表情猜成语无尽模式"], msg=msg.content.strip(),
                                list_bool=True,
                                equal_bool=True):
            Thread(target=self.start_guess_idiom_emoji, name="表情猜成语", args=(msg, 999)).start()
            return True
        elif self.judge_keyword(keyword=["一站到底", "萝卜一站到底", "一站到底无尽模式", "萝卜一站到底无尽模式"],
                                msg=msg.content.strip(),
                                list_bool=True,
                                split_bool=True,
                                equal_bool=True):
            with self.counter_lock:
                if ' ' in msg.content.strip():
                    db_path_map = {"knowledge": "questions.db",
                                   "java": "questions_java.db",
                                   "ja": "questions_java.db",
                                   "python": "questions_python.db",
                                   "py": "questions_python.db",
                                   "en": "questions_english.db",
                                   "english": "questions_english.db"}
                    db_path = msg.content.strip().split(' ')[1]
                    db_path = db_path_map.get(db_path, "questions.db")
                    ques_db = QuestionDB(PRJ_PATH + "/Config/" + db_path)
                else:
                    ques_db = QuestionDB(PRJ_PATH + "/Config/questions.db")
                self.question_db[msg.roomid] = ques_db
                Thread(target=self.start_challenge, name="一站到底", args=(msg, 999)).start()
                return True

    def gaming_function(self, msg):
        if self.judge_keyword(keyword=["退出游戏"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            if msg.sender == self.game_starter.get(msg.roomid, '') or \
                    msg.sender in self.administrators:
                self.game_mode_rooms[msg.roomid] = False
                self.wcf.send_text(msg=f'游戏已中止！', receiver=msg.roomid)
                return
            return
        elif self.judge_keyword(keyword=["重发"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            if self.idiom_pic[msg.roomid]:
                self.send_image_ensure_success(path=self.idiom_pic[msg.roomid], receiver=msg.roomid)
            return
        # 成语解析功能
        elif self.judge_keyword(keyword=["成语解析", "成语解释", "成语查询"], msg=msg.content.strip(), list_bool=True,
                                split_bool=True):
            with self.counter_lock:
                idiom_name = msg.content.strip().split(' ', 1)[1].strip()
                idiom_msg = f'@{self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)}\n' \
                            + self.Ams.get_idiom_explain(idiom_name)
                self.wcf.send_text(msg=idiom_msg, receiver=msg.roomid, aters=msg.sender)
                return
        # 成语接龙提示功能
        elif self.judge_keyword(keyword=["提示", "给点提示", "解释"], msg=msg.content.strip(), list_bool=True,
                                equal_bool=True):
            with self.counter_lock:
                idiom = self.idiom_question.get(msg.roomid, '')
                answer_tip = self.Ams.db_idiom.get_info_by_word(idiom)
                if answer_tip:
                    answer = f"成语：{answer_tip.get('word', '')}\n" \
                             f"拼音：{answer_tip.get('pinyin', '')}\n" \
                             f"解释：{answer_tip.get('explanation', '')}\n" \
                             f"出处：{answer_tip.get('derivation', '')}\n" \
                             f"例句：{answer_tip.get('example', '')}"
                    self.wcf.send_text(msg=answer, receiver=msg.roomid)
        # 一站到底购买复活币
        elif self.judge_keyword(keyword=["购买复活币"], msg=msg.content.strip(), list_bool=True, equal_bool=True):
            Thread(target=self.deduct_points_func_general, name="购买复活币",
                   args=(msg, 1, "您购买了复活币原地复活",
                         self.buy_relive_coin, msg)).start()
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
                            wx_id = msg.sender
                            wx_name = self.get_wx_name(msg)
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_id in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_id] += 1
                                else:
                                    self.game_point[msg.roomid][wx_id] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_id: 1}
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
                            wx_id = msg.sender
                            wx_name = self.get_wx_name(msg)
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 接龙成功！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_id in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_id] += 1
                                else:
                                    self.game_point[msg.roomid][wx_id] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_id: 1}
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
                            wx_id = msg.sender
                            wx_name = self.get_wx_name(msg)
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_id in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_id] += 1
                                else:
                                    self.game_point[msg.roomid][wx_id] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_id: 1}
                except Exception as e:
                    OutPut.outPut(f'[-]: 表情猜成语游戏出问题了 :{e}')
            elif self.game_mode_rooms.get(msg.roomid, False) == "start_challenge":
                try:
                    with self.counter_lock:
                        if self.game_success.get(msg.roomid, False):
                            return
                        if self.judge_keyword(keyword=self.question_options.get(msg.roomid, []),
                                              msg=msg.content.strip().upper(), list_bool=True, equal_bool=True):
                            if msg.sender in self.question_wrong.get(msg.roomid, []):
                                return
                            wx_id = msg.sender
                            wx_name = self.get_wx_name(msg)
                            if not self.game_answer[msg.roomid] == msg.content.strip().upper():
                                self.wcf.send_text(msg=f'很遗憾 {wx_name} 答错了，取消继续游戏资格！',
                                                   receiver=msg.roomid)
                                self.question_wrong[msg.roomid].append(wx_id)
                                return
                            self.game_success[msg.roomid] = True
                            self.game_answer[msg.roomid] = None
                            self.question_options[msg.roomid] = []
                            self.wcf.send_text(msg=f'恭喜 {wx_name} 答对了！', receiver=msg.roomid)
                            if msg.roomid in self.game_point.keys():
                                if wx_id in self.game_point[msg.roomid].keys():
                                    self.game_point[msg.roomid][wx_id] += 1
                                else:
                                    self.game_point[msg.roomid][wx_id] = 1
                            else:
                                self.game_point[msg.roomid] = {wx_id: 1}
                except Exception as e:
                    OutPut.outPut(f'[-]: 一站到底游戏出问题了 :{e}')

    def start_guess_idiom_image(self, msg, number_of_rounds=5):
        with self.counter_lock:
            if self.game_mode_rooms.get(msg.roomid, False):
                return
            self.game_mode_rooms[msg.roomid] = "guess_idiom_image"
            self.game_starter[msg.roomid] = msg.sender

        wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n看图猜成语游戏开始，总共 {number_of_rounds} 轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。'
                               f'\n如果未成功收到图片，'
                               f'\n请回复“重发”。',
                           receiver=msg.roomid, aters=msg.sender)
        try:
            i = 0
            for i in range(number_of_rounds):
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
                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                self.wcf.send_text(msg=f'第{i + 1}轮题目，请在60秒内回答：', receiver=msg.roomid)
                time.sleep(0.1)
                self.game_answer[msg.roomid] = idiom_data
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
                        msg_tip = f'还剩20秒！\n答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.3)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    self.wcf.send_text(msg='没有人回答正确！', receiver=msg.roomid)
                    # 无尽模式终止循环
                    if number_of_rounds == 999:
                        answer = f"答案：{idiom_data.get('答案', '')}\n" \
                                 f"拼音：{idiom_data.get('拼音', '')}\n" \
                                 f"解释：{idiom_data.get('解释', '')}\n" \
                                 f"出处：{idiom_data.get('出处', '')}\n" \
                                 f"例句：{idiom_data.get('例句', '')}"
                        self.wcf.send_text(msg=answer, receiver=msg.roomid)
                        break
                answer = f"答案：{idiom_data.get('答案', '')}\n" \
                         f"拼音：{idiom_data.get('拼音', '')}\n" \
                         f"解释：{idiom_data.get('解释', '')}\n" \
                         f"出处：{idiom_data.get('出处', '')}\n" \
                         f"例句：{idiom_data.get('例句', '')}"
                self.wcf.send_text(msg=answer, receiver=msg.roomid)
                time.sleep(1)
            msg_over = ["游戏结束！"]
            champion = None
            runner_up = None
            third_place_winner = None
            if msg.roomid in self.game_point.keys():
                sorted_points = sorted(self.game_point[msg.roomid].items(), key=lambda x: x[1], reverse=True)
                for idx, (wx_id, point) in enumerate(sorted_points):
                    msg.sender = wx_id
                    if len(sorted_points) == 1:
                        msg_over.append(f"🏆 {self.get_wx_name(msg)}：{point} 题")
                        champion = wx_id
                    else:
                        if idx == 0:
                            msg_over.append(f"🥇 {self.get_wx_name(msg)}：{point} 题")
                            champion = wx_id
                        elif idx == 1:
                            msg_over.append(f"🥈 {self.get_wx_name(msg)}：{point} 题")
                            runner_up = wx_id
                        elif idx == 2:
                            msg_over.append(f"🥉 {self.get_wx_name(msg)}：{point} 题")
                            third_place_winner = wx_id
                        else:
                            msg_over.append(f"🏅 {self.get_wx_name(msg)}：{point} 题")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
            if champion:
                if i >= 3 * 5:
                    max_point = (i // 5) * 10
                else:
                    max_point = 15
                point = random.randint(1, max_point)
                content = f'恭喜你成为本轮游戏的冠军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！\nคิดถึง'
                self.send_at_msg(msg.roomid, champion, content)
                self.add_point(msg.roomid, champion, point)
                if i >= 44:
                    if runner_up:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的亚军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, runner_up, content)
                        self.add_point(msg.roomid, runner_up, point)
                    if third_place_winner:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的季军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, third_place_winner, content)
                        self.add_point(msg.roomid, third_place_winner, point)
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
    def start_idiom_chain(self, msg, number_of_rounds=10):
        with self.counter_lock:
            if self.game_mode_rooms.get(msg.roomid, False):
                return
            self.game_mode_rooms[msg.roomid] = "idiom_chain"
            self.game_starter[msg.roomid] = msg.sender
            self.idiom_usr_answer_history[msg.roomid] = []

        wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n成语接龙游戏开始，总共 {number_of_rounds} 轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。',
                           receiver=msg.roomid, aters=msg.sender)
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
            self.idiom_usr_answer_history[msg.roomid].append(idiom)

            i = 0
            for i in range(number_of_rounds):
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
                    OutPut.outPut(f'成语接龙：{idiom} 无法继续接龙！')
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                self.wcf.send_text(msg=f'第{i + 1}轮题目，请在60秒内回答：\n【{idiom}】', receiver=msg.roomid)
                time.sleep(0.1)
                self.game_answer[msg.roomid] = answers
                print(answers)
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
                        msg_tip = f'还剩20秒！\n参考答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.3)
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
                    OutPut.outPut(f'成语接龙：{usr_answer} 无法继续接龙！')
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                idiom = random.choice(idiom_lst)
                while (not self.Ams.db_idiom.get_words_by_word(idiom)) or (
                        idiom in self.idiom_usr_answer_history[msg.roomid]):
                    idiom_lst.remove(idiom)
                    if not idiom_lst:
                        break
                    idiom = random.choice(idiom_lst)
                if not idiom_lst:
                    OutPut.outPut(f'成语接龙：{usr_answer} 无法继续为其接龙！')
                    self.wcf.send_text(msg='成语接龙已到达终点，游戏提前结束！', receiver=msg.roomid)
                    break
                self.idiom_usr_answer_history[msg.roomid].append(idiom)
                time.sleep(1)
            msg_over = ["游戏结束！"]
            champion = None
            runner_up = None
            third_place_winner = None
            if msg.roomid in self.game_point.keys():
                sorted_points = sorted(self.game_point[msg.roomid].items(), key=lambda x: x[1], reverse=True)
                for idx, (wx_id, point) in enumerate(sorted_points):
                    msg.sender = wx_id
                    if len(sorted_points) == 1:
                        msg_over.append(f"🏆 {self.get_wx_name(msg)}：{point} 题")
                        champion = wx_id
                    else:
                        if idx == 0:
                            msg_over.append(f"🥇 {self.get_wx_name(msg)}：{point} 题")
                            champion = wx_id
                        elif idx == 1:
                            msg_over.append(f"🥈 {self.get_wx_name(msg)}：{point} 题")
                            runner_up = wx_id
                        elif idx == 2:
                            msg_over.append(f"🥉 {self.get_wx_name(msg)}：{point} 题")
                            third_place_winner = wx_id
                        else:
                            msg_over.append(f"🏅 {self.get_wx_name(msg)}：{point} 题")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
            if champion:
                if i >= 3 * 10:
                    max_point = (i // 10) * 10
                else:
                    max_point = 15
                point = random.randint(1, max_point)
                content = f'恭喜你成为本轮游戏的冠军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！\nคิดถึง'
                self.send_at_msg(msg.roomid, champion, content)
                self.add_point(msg.roomid, champion, point)
                if i >= 88:
                    if runner_up:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的亚军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, runner_up, content)
                        self.add_point(msg.roomid, runner_up, point)
                    if third_place_winner:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的季军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, third_place_winner, content)
                        self.add_point(msg.roomid, third_place_winner, point)
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
    def start_guess_idiom_emoji(self, msg, number_of_rounds=5):
        with self.counter_lock:
            if self.game_mode_rooms.get(msg.roomid, False):
                return
            self.game_mode_rooms[msg.roomid] = "guess_idiom_emoji"
            self.game_starter[msg.roomid] = msg.sender

        wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n表情猜成语游戏开始，总共 {number_of_rounds} 轮！'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。',
                           receiver=msg.roomid, aters=msg.sender)
        try:
            i = 0
            for i in range(number_of_rounds):
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
                self.wcf.send_text(msg=f'第{i + 1}轮题目，请在60秒内回答：\n{emoji}', receiver=msg.roomid)
                time.sleep(0.1)
                self.game_answer[msg.roomid] = idiom
                print(idiom)
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
                        msg_tip = f'还剩20秒！\n答案提示：{answer_tip}'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.3)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    self.wcf.send_text(msg='没有人回答正确！', receiver=msg.roomid)
                    # 无尽模式终止循环
                    if number_of_rounds == 999:
                        answer = f"答案：{idiom_data.get('word', '')}\n" \
                                 f"拼音：{idiom_data.get('pinyin', '')}\n" \
                                 f"解释：{idiom_data.get('explanation', '')}\n" \
                                 f"出处：{idiom_data.get('derivation', '')}\n" \
                                 f"例句：{idiom_data.get('example', '')}"
                        self.wcf.send_text(msg=answer, receiver=msg.roomid)
                        break
                answer = f"答案：{idiom_data.get('word', '')}\n" \
                         f"拼音：{idiom_data.get('pinyin', '')}\n" \
                         f"解释：{idiom_data.get('explanation', '')}\n" \
                         f"出处：{idiom_data.get('derivation', '')}\n" \
                         f"例句：{idiom_data.get('example', '')}"
                self.wcf.send_text(msg=answer, receiver=msg.roomid)
                time.sleep(1)
            msg_over = ["游戏结束！"]
            champion = None
            runner_up = None
            third_place_winner = None
            if msg.roomid in self.game_point.keys():
                sorted_points = sorted(self.game_point[msg.roomid].items(), key=lambda x: x[1], reverse=True)
                for idx, (wx_id, point) in enumerate(sorted_points):
                    msg.sender = wx_id
                    if len(sorted_points) == 1:
                        msg_over.append(f"🏆 {self.get_wx_name(msg)}：{point} 题")
                        champion = wx_id
                    else:
                        if idx == 0:
                            msg_over.append(f"🥇 {self.get_wx_name(msg)}：{point} 题")
                            champion = wx_id
                        elif idx == 1:
                            msg_over.append(f"🥈 {self.get_wx_name(msg)}：{point} 题")
                            runner_up = wx_id
                        elif idx == 2:
                            msg_over.append(f"🥉 {self.get_wx_name(msg)}：{point} 题")
                            third_place_winner = wx_id
                        else:
                            msg_over.append(f"🏅 {self.get_wx_name(msg)}：{point} 题")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
            if champion:
                if i >= 3 * 5:
                    max_point = (i // 5) * 10
                else:
                    max_point = 15
                point = random.randint(1, max_point)
                content = f'恭喜你成为本轮游戏的冠军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！\nคิดถึง'
                self.send_at_msg(msg.roomid, champion, content)
                self.add_point(msg.roomid, champion, point)
                if i >= 44:
                    if runner_up:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的亚军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, runner_up, content)
                        self.add_point(msg.roomid, runner_up, point)
                    if third_place_winner:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的季军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, third_place_winner, content)
                        self.add_point(msg.roomid, third_place_winner, point)
        except Exception as e:
            OutPut.outPut(f'[-]: 表情猜成语游戏出问题了 :{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False

    # 答题挑战
    def start_challenge(self, msg, number_of_rounds=5):
        with self.counter_lock:
            if self.game_mode_rooms.get(msg.roomid, False):
                return
            self.game_mode_rooms[msg.roomid] = "start_challenge"
            self.game_starter[msg.roomid] = msg.sender
            self.question_id_history[msg.roomid] = []
            self.question_wrong[msg.roomid] = []
            self.question_options[msg.roomid] = []

        wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        self.wcf.send_text(msg=f'@{wx_name} '
                               f'\n一站到底游戏开始，总共 {number_of_rounds} 轮！'
                               f'\n每答错一题，暂时取消游戏资格，每 6 轮将自动复活 或 购买复活币 原地复活。'
                               f'\n如果要提前中止游戏，'
                               f'\n请回复“退出游戏”。',
                           receiver=msg.roomid, aters=msg.sender)
        try:
            i = 0
            for i in range(number_of_rounds):
                if not self.game_mode_rooms.get(msg.roomid, False):
                    # 清空游戏数据
                    self.game_mode_rooms[msg.roomid] = False
                    self.game_point[msg.roomid] = {}
                    self.game_answer[msg.roomid] = None
                    self.game_success[msg.roomid] = False
                    self.question_id_history[msg.roomid] = []
                    self.question_wrong[msg.roomid] = []
                    self.question_options[msg.roomid] = []
                    return
                option_str = ""
                while True:
                    ques_db = self.question_db.get(msg.roomid, self.Ams.db_question)
                    question_info = ques_db.get_random_question()
                    question_id = question_info.get("id", "")
                    question = question_info.get("question", "")
                    options = question_info.get("options", [])
                    answer = question_info.get("answer", "")
                    explanation = question_info.get("explanation", "")

                    if len(self.question_id_history.get(msg.roomid, [])) == ques_db.get_total_question():
                        self.game_success[msg.roomid] = True
                        break

                    # 处理一下问题跟选项
                    if 'english' not in ques_db.db_path:
                        question = question.replace("\xa0", " ").replace(" ", "_")
                    options = json.loads(options)
                    for key, value in options.items():
                        option_str += f"{key}: {value}\n"

                    if question_id in self.question_id_history.get(msg.roomid, []):
                        continue
                    else:
                        self.question_id_history[msg.roomid].append(question_id)
                        break
                # 题库没了，游戏结束
                if self.game_success.get(msg.roomid, False):
                    break
                # 每6轮复活一次
                if (i + 1) % 6 == 0:
                    content = f"古娜拉黑暗之神\n✨全体复活✨"
                    self.wcf.send_text(content, receiver=msg.roomid)
                    self.question_wrong[msg.roomid] = []
                    time.sleep(0.1)
                self.wcf.send_text(msg=f'第{i + 1}轮题目，请在60秒内回答：\n\n'
                                       f'{question}\n{option_str}', receiver=msg.roomid)
                time.sleep(0.1)
                self.game_answer[msg.roomid] = answer
                self.question_options[msg.roomid] = list(options.keys())
                print(answer)
                cur_time = time.time()
                flag_tip = False
                while time.time() - cur_time < 61:
                    if not self.game_mode_rooms.get(msg.roomid, False):
                        # 清空游戏数据
                        self.game_mode_rooms[msg.roomid] = False
                        self.game_point[msg.roomid] = {}
                        self.game_answer[msg.roomid] = None
                        self.game_success[msg.roomid] = False
                        self.question_id_history[msg.roomid] = []
                        self.question_wrong[msg.roomid] = []
                        self.question_options[msg.roomid] = []
                        return
                    if self.game_success.get(msg.roomid, False):
                        break
                    if time.time() - cur_time > 40 and not flag_tip:
                        msg_tip = f'还剩20秒！'
                        self.wcf.send_text(msg=msg_tip, receiver=msg.roomid)
                        flag_tip = True
                    time.sleep(0.3)
                self.game_answer[msg.roomid] = None
                if self.game_success.get(msg.roomid, False):
                    self.game_success[msg.roomid] = False
                else:
                    res_content = f'没有人回答正确，提前结束游戏！\n' \
                                  f'正确答案：{answer}'
                    if explanation:
                        res_content += f'\n解析：\n{explanation}'
                    self.wcf.send_text(msg=res_content, receiver=msg.roomid)
                    break
                time.sleep(1.8)
            msg_over = ["游戏结束！"]
            champion = None
            runner_up = None
            third_place_winner = None
            if msg.roomid in self.game_point.keys():
                sorted_points = sorted(self.game_point[msg.roomid].items(), key=lambda x: x[1], reverse=True)
                for idx, (wx_id, point) in enumerate(sorted_points):
                    msg.sender = wx_id
                    if len(sorted_points) == 1:
                        msg_over.append(f"🏆 {self.get_wx_name(msg)}：{point} 题")
                        champion = wx_id
                    else:
                        if idx == 0:
                            msg_over.append(f"🥇 {self.get_wx_name(msg)}：{point} 题")
                            champion = wx_id
                        elif idx == 1:
                            msg_over.append(f"🥈 {self.get_wx_name(msg)}：{point} 题")
                            runner_up = wx_id
                        elif idx == 2:
                            msg_over.append(f"🥉 {self.get_wx_name(msg)}：{point} 题")
                            third_place_winner = wx_id
                        else:
                            msg_over.append(f"🏅 {self.get_wx_name(msg)}：{point} 题")
            self.wcf.send_text(msg='\n'.join(msg_over), receiver=msg.roomid)
            if champion:
                if i >= 3 * 5:
                    max_point = (i // 10) * 10
                else:
                    max_point = 15
                point = random.randint(1, max_point)
                content = f'恭喜你成为本轮游戏的冠军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！\nคิดถึง'
                self.send_at_msg(msg.roomid, champion, content)
                self.add_point(msg.roomid, champion, point)
                if i >= 88:
                    if runner_up:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的亚军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, runner_up, content)
                        self.add_point(msg.roomid, runner_up, point)
                    if third_place_winner:
                        max_point = max_point // 2
                        point = random.randint(1, max_point)
                        content = f'恭喜你成为本轮游戏的季军，获得随机积分奖励 {point} 分！\n全拼人品，1-{max_point} 积分不等！'
                        self.send_at_msg(msg.roomid, third_place_winner, content)
                        self.add_point(msg.roomid, third_place_winner, point)
        except Exception as e:
            print(traceback.format_exc())
            OutPut.outPut(f'[-]: 一站到底游戏出问题了 :{e}')
        finally:
            # 清空游戏数据
            self.game_mode_rooms[msg.roomid] = False
            self.game_point[msg.roomid] = {}
            self.game_answer[msg.roomid] = None
            self.game_success[msg.roomid] = False
            self.question_id_history[msg.roomid] = []
            self.question_wrong[msg.roomid] = []
            self.question_options[msg.roomid] = []

    # 积分查询
    def query_point(self, msg):
        wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name)
        send_msg = f'@{wx_name} 您当前剩余积分: {point}\n还望好好努力，平时给我的主人发个红包啥的，就给你加积分啦~'
        self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 自定义回复
    def custom_get(self, msg):
        for key, values in self.Custom_Key_Words.items():
            for value in values:
                if value == msg.content.strip():
                    OutPut.outPut(f'[+]: 调用自定义回复成功！！！')
                    send_msg = key.replace('\\n', '\n')
                    self.wcf.send_text(
                        msg=f'@{self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)} {send_msg}',
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

    # 尝试将字符串解析为 JSON 格式
    @staticmethod
    def try_json_format(json_string):
        try:
            # 确保输入是字符串
            if not isinstance(json_string, str):
                raise TypeError("Input must be a string.")

            # 尝试将字符串解析为 JSON
            value = json.loads(json_string)
            return True, value  # 成功时返回 True 和解析后的值
        except json.JSONDecodeError as e:
            return False, f"JSON Decode Error: {str(e)}"  # 解析失败
        except TypeError as e:
            return False, f"Type Error: {str(e)}"  # 输入类型错误
        except Exception as e:
            return False, f"Unexpected Error: {str(e)}"  # 其他异常

    # 自定义回复
    def custom_reply(self, msg):
        try:
            content = msg.content.strip()
            keyword, arg = (content.split(' ', 1) + ['', ''])[:2]
            custom_reply_dict = self.custom_keyword.get(keyword, {})
            if custom_reply_dict:
                typ = custom_reply_dict.get('typ', '')
                url = custom_reply_dict.get('url', '')
                res_typ = custom_reply_dict.get('res_typ', '')
                is_arg = custom_reply_dict.get('is_arg', False)
                if is_arg:
                    response = self.request_custom_reply(url=url, arg=arg)
                else:
                    response = self.request_custom_reply(url=url)

                if not response:
                    # 重试一次
                    if is_arg:
                        response = self.request_custom_reply(url=url, arg=arg)
                    else:
                        response = self.request_custom_reply(url=url)
                    if not response:
                        return
                if typ == "txt":
                    if res_typ == "raw":
                        send_msg = response.text
                        is_json_format, value = self.try_json_format(send_msg)
                        if is_json_format:
                            send_msg = value

                        # 这里对云端插件特别处理
                        if keyword == "云端插件":
                            if isinstance(send_msg, dict):
                                send_msg_type = send_msg.get("type", "")
                                send_msg_code = send_msg.get("code", "")
                                send_msg_plugin_name = send_msg.get("plugin_name", "")
                                if send_msg_type == "text" and send_msg_code == 200:
                                    send_msg = send_msg.get("msg", "")
                                elif send_msg_plugin_name == "去水印解析":
                                    send_msg = send_msg.get("msg", "")

                        if isinstance(send_msg, str):
                            send_msg = send_msg.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r'). \
                                replace("<br>", '\n').replace("<br >", '\n'). \
                                replace("<p>", '\n').replace("</p>", '\n').replace("<p >", '\n').replace("</p >", '\n')
                            send_msg = send_msg.strip()
                        elif isinstance(send_msg, dict) or isinstance(send_msg, list):
                            send_msg = json.dumps(send_msg, ensure_ascii=False, indent=2)

                        if send_msg:
                            self.send_at_msg(msg.roomid, msg.sender, send_msg)
                    else:
                        json_data = response.json()
                        split_res_lst = res_typ.split("_")[1:]
                        send_msg = json_data
                        for res in split_res_lst:
                            if res.isdigit():
                                send_msg = send_msg[int(res)]
                            else:
                                send_msg = send_msg.get(res, "")
                        is_json_format, value = self.try_json_format(send_msg)
                        if is_json_format:
                            send_msg = value
                        if isinstance(send_msg, str):
                            send_msg = send_msg.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r'). \
                                replace("<br>", '\n').replace("<br >", '\n'). \
                                replace("<p>", '\n').replace("</p>", '\n').replace("<p >", '\n').replace("</p >", '\n')
                            send_msg = send_msg.strip()
                        elif isinstance(send_msg, dict) or isinstance(send_msg, list):
                            send_msg = json.dumps(send_msg, ensure_ascii=False, indent=2)
                        if send_msg:
                            self.send_at_msg(msg.roomid, msg.sender, send_msg)
                elif typ in ["pic", "gif"]:
                    tail_decoration = ".jpg" if typ == "pic" else ".gif"
                    if res_typ == "raw":
                        save_path = self.Ams.Cache_path + '/Pic_Cache/' + str(int(time.time() * 1000)) + tail_decoration
                        with open(save_path, mode='wb') as f:
                            f.write(response.content)
                        if save_path.endswith(".jpg"):
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                        else:
                            self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                    else:
                        json_data = response.json()
                        split_res_lst = res_typ.split("_")[1:]
                        new_url = json_data
                        for res in split_res_lst:
                            new_url = new_url.get(res, "")
                        if new_url:
                            save_path = self.Ams.Cache_path + '/Pic_Cache/' + str(
                                int(time.time() * 1000)) + tail_decoration
                            self.download_file(url=new_url, save_path=save_path)
                            if save_path.endswith(".jpg"):
                                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                            else:
                                self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                elif typ == "vid":
                    if res_typ == "raw":
                        save_path = self.Ams.Cache_path + '/Video_Cache/' + str(int(time.time() * 1000)) + '.mp4'
                        with open(save_path, mode='wb') as f:
                            f.write(response.content)
                        self.wcf.send_file(path=save_path, receiver=msg.roomid)
                    else:
                        json_data = response.json()
                        split_res_lst = res_typ.split("_")[1:]
                        new_url = json_data
                        for res in split_res_lst:
                            new_url = new_url.get(res, "")
                        if new_url:
                            save_path = self.Ams.Cache_path + '/Video_Cache/' + str(int(time.time() * 1000)) + '.mp4'
                            self.download_file(url=new_url, save_path=save_path)
                            self.wcf.send_file(path=save_path, receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[-]: 自定义回复出现错误：{e}')
            return

    @staticmethod
    def request_custom_reply(url, arg=None):
        try:
            if arg:
                url = url + arg
            response = requests.get(url=url, timeout=30, verify=False)
            if response.status_code == 200:
                return response
            else:
                return None
        except Exception as e:
            OutPut.outPut(f'[-]: 请求自定义回复出现错误：{e}')
            return None

    @staticmethod
    def download_file(url, save_path):
        """
        通用下载文件函数
        :param url:
        :param save_path:
        :return:
        """
        try:
            response = requests.get(url, timeout=30, verify=False)
            if response.status_code == 200:
                with open(save_path, mode='wb') as f:
                    f.write(response.content)
                return save_path
            else:
                return None
        except Exception as e:
            OutPut.outPut(f'[-]: 通用下载文件函数出现错误, 错误信息: {e}')
            return None

    # Ai对话
    def get_ai(self, msg, at_user_lists, model=None):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)

        if self.ai_max_call.get(msg.roomid, 0) >= 100:
            self.wcf.send_text(msg=f'@{wx_name}\n今日调用次数已达上限，请明天再来~', receiver=msg.roomid,
                               aters=msg.sender)
            return

        if "轮题目，请在60秒内回答：" in msg.content:
            self.wcf.send_text(msg=f'@{wx_name}\n别问我，我也不知道！',
                               receiver=msg.roomid, aters=msg.sender)
            return

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
                with self.counter_lock:
                    # 记录调用次数
                    if msg.sender not in self.ai_max_call:
                        self.ai_max_call[msg.sender] = 1
                    else:
                        self.ai_max_call[msg.sender] += 1
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
                    with self.counter_lock:
                        # 记录调用次数
                        if msg.sender not in self.ai_max_call:
                            self.ai_max_call[msg.sender] = 1
                        else:
                            self.ai_max_call[msg.sender] += 1
                else:
                    usr_msg = f'@{wx_name}\n [{question}]：\n图片生成失败！'
                    self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
        # 不是管理员
        else:
            # 获取所有白名单群聊
            whiteRooms_dicts = self.Dms.show_white_rooms()
            # 扣除积分
            if msg.roomid in whiteRooms_dicts.keys():
                deduct_point = 0
            else:
                deduct_point = int(self.Ai_Point)
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                    room_name=room_name) >= deduct_point:
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=deduct_point)
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                point_msg = f'@{wx_name} 您使用了Ai对话功能，扣除您 {deduct_point} 点积分,\n当前剩余积分: {now_point}'
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
                    with self.counter_lock:
                        # 记录调用次数
                        if msg.sender not in self.ai_max_call:
                            self.ai_max_call[msg.sender] = 1
                        else:
                            self.ai_max_call[msg.sender] += 1
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
                        with self.counter_lock:
                            # 记录调用次数
                            if msg.sender not in self.ai_max_call:
                                self.ai_max_call[msg.sender] = 1
                            else:
                                self.ai_max_call[msg.sender] += 1
                    else:
                        usr_msg = f'@{wx_name}\n [{question}]：\n图片生成失败！'
                        self.wcf.send_text(msg=usr_msg, receiver=msg.roomid)
            else:
                send_msg = f'@{wx_name} 积分不足, 我的主人高兴了就会送积分哦~'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    def get_xiuren_pic(self, msg):
        if not (msg.sender in self.administrators):
            return

        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            # admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次操作不扣除积分'
            # self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            pic_path = self.get_xiuren_pic_path()
            self.send_image_ensure_success(path=pic_path, receiver=msg.roomid)
        # 不是管理员
        else:
            # 获取所有白名单群聊
            whiteRooms_dicts = self.Dms.show_white_rooms()
            # 扣除积分
            if msg.roomid in whiteRooms_dicts.keys():
                deduct_point = 0
            else:
                deduct_point = int(self.Ai_Point)
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    deduct_point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=deduct_point)
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                # scan_msg = f'@{wx_name} 您使用了隐藏功能-拒绝者，扣除您 {deduct_point} 点积分,\n当前剩余积分: {now_point}'
                # self.wcf.send_text(msg=scan_msg, receiver=msg.roomid, aters=msg.sender)
                pic_path = self.get_xiuren_pic_path()
                self.send_image_ensure_success(path=pic_path, receiver=msg.roomid)
            else:
                send_msg = f'@{wx_name} 积分不足, 我的主人高兴了就会送积分哦~'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    def deduct_points_func(self, msg, func, *args):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            # admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次操作不扣除积分'
            # self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            func(*args)
        # 不是管理员
        else:
            # 获取所有白名单群聊
            whiteRooms_dicts = self.Dms.show_white_rooms()
            # 扣除积分
            if msg.roomid in whiteRooms_dicts.keys():
                deduct_point = 0
            else:
                deduct_point = 2
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    deduct_point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=deduct_point)
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                # scan_msg = f'@{wx_name} 您使用了表情功能，扣除您 {deduct_point} 点积分,\n当前剩余积分: {now_point}'
                # self.wcf.send_text(msg=scan_msg, receiver=msg.roomid, aters=msg.sender)
                func(*args)
            else:
                send_msg = f'@{wx_name} 积分不足, 我的主人高兴了就会送积分哦~'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    def deduct_points_func_general(self, msg, point, msg_str, func, *args):
        admin_dicts = self.Dms.show_admins(wx_id=msg.sender, room_id=msg.roomid)
        room_name = self.Dms.query_room_name(room_id=msg.roomid)
        wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
        # 是管理员
        if msg.sender in admin_dicts.keys() or msg.sender in self.administrators:
            admin_msg = f'@{wx_name} 您是尊贵的管理员/超级管理员，本次操作不扣除积分'
            self.wcf.send_text(msg=admin_msg, receiver=msg.roomid, aters=msg.sender)
            func(*args)
        # 不是管理员
        else:
            # 获取所有白名单群聊
            whiteRooms_dicts = self.Dms.show_white_rooms()
            # 扣除积分
            if msg.roomid in whiteRooms_dicts.keys():
                deduct_point = 0
            else:
                deduct_point = point
            if self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name) >= int(
                    deduct_point):
                self.Dps.del_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                   point=deduct_point)
                now_point = self.Dps.query_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                 room_name=room_name, )
                scan_msg = f'@{wx_name} {msg_str}，扣除您 {deduct_point} 点积分,\n当前剩余积分: {now_point}'
                self.wcf.send_text(msg=scan_msg, receiver=msg.roomid, aters=msg.sender)
                func(*args)
            else:
                send_msg = f'@{wx_name} 积分不足, 我的主人高兴了就会送积分哦~'
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)

    # 赠送积分
    def send_point(self, msg, content, at_user_lists):
        try:
            OutPut.outPut(f'[*]: 赠送积分接口接收到的消息: {content}')
            point = content.split(' ')[-1]
            wx_name = self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)
            room_name = self.Dms.query_room_name(room_id=msg.roomid)
            for give_sender in at_user_lists:
                give_name = self.get_alias_in_chatroom(wxid=give_sender, roomid=msg.roomid)
                send_msg = f'@{wx_name}\n'
                send_msg += self.Dps.send_point(wx_id=msg.sender, wx_name=wx_name, room_id=msg.roomid,
                                                room_name=room_name,
                                                give_sender=give_sender, give_name=give_name, point=point)
                self.wcf.send_text(msg=send_msg, receiver=msg.roomid, aters=msg.sender)
        except Exception as e:
            OutPut.outPut(f'[~]: 赠送积分出了点小问题 :{e}')

    # 生成个性表情
    def gen_emoji(self, msg, content, at_user_lists):
        try:
            OutPut.outPut(f'[*]: 个性表情接口接收到的消息: {content}')
            option = None
            if ' ' in content:
                content, option = content.split(' ', 1)
                option = [option]

            # api表情
            if content in api_emoji_value:
                emoji = content
                for give_sender in at_user_lists:
                    url = self.get_head_img_pro_url(give_sender)
                    save_path = self.Ams.magic_emoji_by_api(emoji, url)
                    if save_path:
                        if save_path.endswith('.gif'):
                            self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                        else:
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                return
            if content in emoji_value_double_jpg:
                if len(at_user_lists) == 1:
                    head_img = self.get_head_img(msg.sender)
                    head_img2 = self.get_head_img(at_user_lists[0])
                else:
                    head_img = self.get_head_img(at_user_lists[0])
                    head_img2 = self.get_head_img(at_user_lists[1])
                if head_img and head_img2:
                    emoji = emoji_mapping_dict_reverse.get(content, None)
                    save_path = self.Ams.magic_emoji_by_head_and_emoji(head_img, emoji, option, head_img2)
                    if save_path:
                        if save_path.endswith('.gif'):
                            self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                        else:
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                return
            for give_sender in at_user_lists:
                head_img = self.get_head_img(give_sender)
                if head_img:
                    emoji = emoji_mapping_dict_reverse.get(content, None)
                    save_path = self.Ams.magic_emoji_by_head_and_emoji(head_img, emoji, option)
                    if save_path:
                        if save_path:
                            if save_path.endswith('.gif'):
                                self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                            else:
                                self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
        except Exception as e:
            OutPut.outPut(f'[~]: 个性表情出了点小问题 :{e}')

    def gen_emoji_self(self, msg, content, at_user_lists, is_refer=False):
        try:
            OutPut.outPut(f'[*]: 个性表情接口接收到的消息: {content}')
            content_lst = content.split(' ', 2)
            if len(content_lst) < 2:
                return
            elif len(content_lst) == 2:
                content = content_lst[1]
                option = None
            else:
                content = content_lst[1]
                option = content_lst[2]
                option = [option]

            # api表情
            if content in api_emoji_value:
                emoji = content
                url = self.get_head_img_pro_url(msg.sender)
                save_path = self.Ams.magic_emoji_by_api(emoji, url)
                if save_path:
                    if save_path.endswith('.gif'):
                        self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                    else:
                        self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
                return
            if content not in emoji_value4jpg + emoji_value_custom:
                return
            if is_refer:
                head_img = is_refer
            else:
                head_img = self.get_head_img(msg.sender)
            if head_img:
                emoji = emoji_mapping_dict_reverse.get(content, None)
                if emoji:
                    save_path = self.Ams.magic_emoji_by_head_and_emoji(head_img, emoji, option)
                    if save_path:
                        if save_path.endswith('.gif'):
                            self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                        else:
                            self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
            return
        except Exception as e:
            OutPut.outPut(f'[~]: 个性表情出了点小问题 :{e}')

    # 生成随机表情
    def gen_random_emoji(self, msg):
        head_img = self.get_head_img(msg.sender)
        if head_img:
            save_path, key_word = self.Ams.magic_emoji_by_head(head_img)
            if save_path:
                reply = f'关键字: {key_word}\n表情可能会有点慢，请稍等片刻'
                self.send_at_msg(msg.roomid, msg.sender, reply)
                if save_path.endswith('.gif'):
                    self.send_emotion_ensure_success(path=save_path, receiver=msg.roomid)
                else:
                    self.send_image_ensure_success(path=save_path, receiver=msg.roomid)
        return

    def robbery_point(self, msg, at_user_lists):
        with self.counter_lock:
            if len(at_user_lists) > 1:
                return

            rob_time_dict = self.rob_time.get(msg.roomid, {})
            last_rob_time = rob_time_dict.get(msg.sender, 0)
            if msg.sender not in self.administrators:
                if time.time() - last_rob_time <= 30 * 60:
                    self.send_at_msg(msg.roomid, msg.sender,
                                     f"下次抢结时间为 {time.strftime('%H:%M:%S', time.localtime(last_rob_time + 30 * 60))} ")
                    return
            if msg.roomid not in self.rob_time:
                self.rob_time[msg.roomid] = {}
            self.rob_time[msg.roomid][msg.sender] = time.time()

            if self.wcf.self_wxid in at_user_lists:
                msg_rob = "你小子胆子挺肥呀，连萝卜都敢抢，它可是开挂的存在，你被抓去挑大粪，损失10积分！"
                point = 10
                self.del_point(msg.roomid, msg.sender, point)
                self.send_at_msg(msg.roomid, msg.sender, msg_rob)
                return

            for give_sender in at_user_lists:
                msg_rob, point = self.robbery()
                if '抢结成功' in msg_rob:
                    self.add_point(msg.roomid, msg.sender, point)
                    self.del_point(msg.roomid, give_sender, point)
                elif '抢结失败' in msg_rob:
                    self.del_point(msg.roomid, msg.sender, point)
                else:
                    self.del_point(msg.roomid, msg.sender, point)
                    self.add_point(msg.roomid, give_sender, point)
                self.send_at_msg(msg.roomid, msg.sender, msg_rob)

    @staticmethod
    def robbery():
        point = random.randint(1, 20)
        index = random.randint(1, 10)
        if index in [1, 2, 3, 4, 5]:
            index = 0
        elif index in [6, 7]:
            index = 1
        else:
            index = 2
        msg_win = [f"抢结成功，给了对方一闷棍，成功抢到{point}积分！",
                   f"抢结成功，对方被你一拳打趴下，成功抢到{point}积分！",
                   f"抢结成功，对方被你一招制胜，成功抢到{point}积分！",
                   f"抢结成功，对方被你一招秒杀，成功抢到{point}积分！",
                   f"抢结成功，一记猴子偷桃，成功抢到{point}积分！",
                   f"抢结成功，躲在墙角偷袭，成功抢到{point}积分！",
                   f"抢结成功，天下武功唯快不破，成功抢到{point}积分！",
                   f"抢结成功，不愧为万中无一的练武奇才，成功抢到{point}积分！",
                   f"抢结成功，板砖在手，天下我有，成功抢到{point}积分！",
                   f"抢结成功，不愧为“给他爱”1000小时选手，成功抢到{point}积分！"]
        msg_lose = [f"抢结失败，没想到对方是个长跑冠军，被追跑虚脱了，损失{point}积分！",
                    f"抢结失败，被对方一拳打趴下，损失{point}积分！",
                    f"抢结失败，被对方一招制胜，损失{point}积分！",
                    f"抢结失败，被对方一招秒杀，损失{point}积分！",
                    f"抢结失败，出门踩到了香蕉皮，重伤住院，损失{point}积分！",
                    f"抢结失败，出门撞见了警察，被抓进局子，损失{point}积分！",
                    f"抢结失败，出门撞见仇家，直接被砍，损失{point}积分！",
                    f"抢结失败，迷路了，最终被警察送回家，损失{point}积分！",
                    f"抢结失败，忘记带丝袜头套，被对方认出，损失{point}积分！",
                    f"抢结失败，丝袜头套破了个大洞，被对方认出，损失{point}积分！",
                    f"抢结失败，扶老奶奶过马路，被老奶奶碰瓷，损失{point}积分！",
                    f"抢结失败，哪个缺德的偷了井盖，你刚好掉进去，损失{point}积分！",
                    f"抢结失败，吃花生米噎住了，差点送命，损失{point}积分！",
                    f"抢结失败，拿了块泡沫板砖就想抢结，结果被人家一记勾拳打趴下，损失{point}积分！",
                    f"抢结失败，楼上装修，一块板砖掉下来砸中了你，重伤住院，损失{point}积分！",
                    f"抢结失败，出门碰瓷，结果路口有监控，被送进局子，损失{point}积分！",
                    f"抢结失败，出门被狗咬，结果狂犬病，住院治疗，损失{point}积分！",
                    f"抢结失败，出门被车撞，结果躺在医院，损失{point}积分！",
                    f"抢结失败，出门被雷劈，结果被送进医院，损失{point}积分！",
                    f"抢结失败，出门被花瓶砸中，结果住进ICU，损失{point}积分！",
                    f"抢结失败，出门被砖头砸中，结果住进ICU，损失{point}积分！",
                    f"抢结失败，干什么不好非学人家抢结，喜提一副银手镯，损失{point}积分！",
                    f"抢结失败，出门撞见债主，老老实实还钱，损失{point}积分！"]
        msg_pants = [f"没打过对面，被对方一招脱裤子，反倒被抢了{point}积分！",
                     f"拿了一把萝卜刀就想抢结，结果被一拳打倒，反倒被抢了{point}积分！",
                     f"对方竟然是散打冠军，被打在地上滚，老老实实上交家当，损失{point}积分！",
                     f"对方竟然是跆拳道黑带，被踢到墙上，还得赔偿对方{point}积分！",
                     f"对方竟然是柔道高手，被摔到地上，还得赔偿对方{point}积分！",
                     f"对方竟然是拳击冠军，被打到鼻青脸肿，还得赔偿对方{point}积分！",
                     f"使出一招葵花点穴手，还没碰到对方，就被人家拿枪指着，老老实实赔偿对方{point}积分！",
                     f"对方掏出一本富婆通讯录，你被忽悠购买了，血亏{point}积分！",
                     f"对方正在遛狗，结果被狗一路狂追，还得给狗狗买狗粮，血亏{point}积分！",
                     f"对方竟然是黑社会老大，你被带到了他的地盘，还得交保护费{point}积分！",
                     f"对方竟然是警察，你被带到了派出所，还得交罚款{point}积分！"]
        msg_lst = [msg_win, msg_lose, msg_pants]
        msg_rob = random.choice(msg_lst[index])
        return msg_rob, point

    def buy_cooling_time(self, msg):
        try:
            self.rob_time[msg.roomid][msg.sender] = time.time() - 30 * 60
        except Exception as e:
            OutPut.outPut(f'[~]: 冷却出了点小问题 :{e}')

    def buy_relive_coin(self, msg):
        with self.counter_lock:
            if self.game_mode_rooms.get(msg.roomid, False) == "start_challenge":
                if msg.sender in self.question_wrong.get(msg.roomid, []):
                    self.question_wrong[msg.roomid].remove(msg.sender)
                return

    # 新增管理员
    def add_admin(self, sender, wx_ids, room_id):
        if wx_ids:
            for wx_id in wx_ids:
                wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                at_msg = f'@{wx_name}\n'
                wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = self.Dms.add_admin(room_id=room_id, wx_id=wx_id, wx_name=wx_name)
                at_msg += msg
                self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 删除管理员
    def del_admin(self, sender, wx_ids, room_id):
        if wx_ids:
            for wx_id in wx_ids:
                wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                at_msg = f'@{wx_name}\n'
                msg = self.Dms.del_admin(room_id=room_id, wx_id=wx_id, wx_name=wx_name)
                at_msg += msg
                self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加推送群聊
    def add_push_room(self, sender, room_id):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_push_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除推送服务
    def del_push_room(self, sender, room_id):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_push_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加白名单群聊
    def add_white_room(self, sender, room_id):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_white_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除白名单群聊
    def del_white_room(self, sender, room_id):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_white_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 添加白名单公众号
    def add_white_gh(self, msg):
        try:
            root_xml = ET.fromstring(msg.content)
            at_msg = f'@{self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)}\n'
            gh_id = root_xml.find('.//sourceusername')
            gh_id = gh_id.text if gh_id else None
            gh_name = root_xml.find('.//sourcedisplayname')
            gh_name = gh_name.text if gh_name else None
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
            print('公众号信息：', gh_id, gh_name)
            if gh_id:
                gh_msg = self.Dms.add_white_gh(gh_id=gh_id, gh_name=gh_name)
                if not gh_msg:
                    return
                at_msg += gh_msg
                self.wcf.send_text(msg=at_msg, receiver=msg.roomid, aters=msg.sender)
                return
        except Exception as e:
            OutPut.outPut(f'[~]: 添加公众号白名单出了点小问题 :{e}')

    # 移除白名单公众号
    def del_white_gh(self, msg):
        if 'gh_' in msg.content:
            try:
                at_msg = f'@{self.get_alias_in_chatroom(wxid=msg.sender, roomid=msg.roomid)}\n'
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
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.add_black_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 移除黑名单群聊
    def del_black_room(self, sender, room_id):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        at_msg = f'@{wx_name}\n'
        msg = self.Dms.del_black_room(room_id=room_id)
        at_msg += msg
        self.wcf.send_text(msg=at_msg, receiver=room_id, aters=sender)

    # 把人移出群聊
    def del_user(self, sender, room_id, wx_ids):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        ret = self.wcf.del_chatroom_members(roomid=room_id, wxids=','.join(wx_ids))
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                del_user_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
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
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                self.block_wx_ids.append(wx_id) if wx_id not in self.block_wx_ids else None
                block_user_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = f'@{wx_name}\n群友 [{block_user_name}] 消息已被屏蔽'
                OutPut.outPut(msg)
                self.wcf.send_text(msg=msg, receiver=room_id, aters=sender)
                self.save_state()

    # 解除屏蔽个人消息
    def unblock_personal_msg(self, sender, room_id, wx_ids):
        wx_name = self.get_alias_in_chatroom(roomid=room_id, wxid=sender)
        for wx_id in wx_ids:
            if wx_id not in self.administrators:
                self.block_wx_ids.remove(wx_id) if wx_id in self.block_wx_ids else None
                unblock_user_name = self.get_alias_in_chatroom(roomid=room_id, wxid=wx_id)
                msg = f'@{wx_name}\n群友 [{unblock_user_name}] 消息已解除屏蔽'
                OutPut.outPut(msg)
                self.wcf.send_text(msg=msg, receiver=room_id, aters=sender)
                self.save_state()

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
    def Add_Point(self, msg, content, at_user_list):
        try:
            OutPut.outPut(f'[*]: 增加积分接口接收到的消息: {content}')
            point = content.strip().split(' ')[-1]
            for wx_id in at_user_list:
                wx_name = self.get_alias_in_chatroom(wxid=wx_id, roomid=msg.roomid)
                room_name = self.Dms.query_room_name(room_id=msg.roomid)
                add_msg = self.Dps.add_point(wx_id=wx_id, wx_name=wx_name, room_id=msg.roomid, room_name=room_name,
                                             point=point)
                add_msg = f'@{wx_name}\n' + add_msg
                self.wcf.send_text(msg=add_msg, receiver=msg.roomid, aters=wx_id)
            OutPut.outPut(f'[+]: 增加积分接口调用成功')
        except Exception as e:
            OutPut.outPut(f'[-]: 增加积分接口出现错误，错误信息: {e}')

    def add_point(self, roomid, wxid, point):
        try:
            wx_name = self.get_alias_in_chatroom(wxid=wxid, roomid=roomid)
            room_name = self.Dms.query_room_name(room_id=roomid)
            add_msg = self.Dps.add_point(wx_id=wxid, wx_name=wx_name, room_id=roomid, room_name=room_name,
                                         point=point)
            # add_msg = f'@{wx_name}\n' + add_msg
            # self.wcf.send_text(msg=add_msg, receiver=roomid, aters=wxid)
        except Exception as e:
            OutPut.outPut(f'[-]: 增加积分功能出现错误，错误信息: {e}')

    # 减少积分
    def Del_Point(self, msg, content, at_user_list):
        try:
            OutPut.outPut(f'[*]: 减少积分接口接收到的消息: {content}')
            point = content.strip().split(' ')[-1]
            for wx_id in at_user_list:
                wx_name = self.get_alias_in_chatroom(wxid=wx_id, roomid=msg.roomid)
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

    def del_point(self, roomid, wxid, point):
        try:
            wx_name = self.get_alias_in_chatroom(wxid=wxid, roomid=roomid)
            room_name = self.Dms.query_room_name(room_id=roomid)
            del_msg = self.Dps.del_point(wx_id=wxid, wx_name=wx_name, room_id=roomid, room_name=room_name,
                                         point=point)
            # send_msg = f'@{wx_name}\n' + str(del_msg)
            # self.wcf.send_text(msg=del_msg, receiver=roomid, aters=wxid)
        except Exception as e:
            OutPut.outPut(f'[-]: 减少积分功能出现错误，错误信息: {e}')

    def reset_point(self, roomid, wxid):
        try:
            wx_name = self.get_alias_in_chatroom(wxid=wxid, roomid=roomid)
            room_name = self.Dms.query_room_name(room_id=roomid)
            reset_msg = self.Dps.zero_point(wx_id=wxid, wx_name=wx_name, room_id=roomid, room_name=room_name)
            send_msg = f'@{wx_name}\n' + str(reset_msg)
            self.wcf.send_text(msg=send_msg, receiver=roomid, aters=wxid)
        except Exception as e:
            OutPut.outPut(f'[-]: 重置积分功能出现错误，错误信息: {e}')

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
            at_user_lists = [i.strip() for i in at_user_lists]
            at_user_lists = [i for i in at_user_lists if i != '']
        except AttributeError:
            OutPut.outPut(f'[~]: 获取被@的微信id出了点小问题, 不用管 ~~~')
            at_user_lists = []
        return at_user_lists

    # 处理@人后的消息
    def handle_atMsg(self, msg, at_user_lists):
        if at_user_lists:
            content = msg.content
            for wx_id in at_user_lists:
                print(self.get_alias_in_chatroom(roomid=msg.roomid, wxid=wx_id))
                content = content.replace('@' + self.get_alias_in_chatroom(roomid=msg.roomid, wxid=wx_id), '')
            OutPut.outPut(f'[+]: 处理@人后的消息: {content}')
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

    def send_music(self, msg, song_info):
        if not song_info:
            return

    def send_music_message(self, digest, url, receiver):
        self.wcf.send_rich_text(name='点歌',
                                account='',
                                title='MyFreeMP3',
                                digest=digest,
                                url=url,
                                thumburl='https://tool.liumingye.cn/music/img/pwa-192x192.png',
                                receiver=receiver)

    def send_video_message(self, title, digest, url, thumburl, receiver):
        self.wcf.send_rich_text(name=title,
                                account='',
                                title=title,
                                digest=digest,
                                url=url,
                                thumburl=thumburl,
                                receiver=receiver)

    @staticmethod
    def get_xiuren_pic_path():
        root_dir = r'D:/share/XiuRen_downloads'

        # root_dir = r'D:/share/XiuRen_jpgs2'

        def generate_path():
            page_number = random.randint(1, 59)
            second_number = random.randint(1, 24)
            image_number = random.randint(0, 4)
            return f"{root_dir}/page_{page_number}/{second_number}/image_{image_number}.jpg"
            # image_number = random.randint(1, 5984)
            # return f"{root_dir}/{image_number}.jpg"

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
            res = self.query_sql("MSG0.db", sql_query)
            print(f"recall msg res = {res}")
            # 撤回消息ID
            msg_svr_id = res[0].get('MsgSvrID')
            if msg_svr_id == 0:
                OutPut.outPut(f'[-]: 撤回消息失败，消息ID为0')
                return
            self.wcf.revoke_msg(msg_svr_id)
        except Exception as e:
            OutPut.outPut(f'[-]: 撤回消息出现错误，错误信息: {e}')

    # 获取头像缓存，清晰度低
    def get_head_img(self, wxid):
        try:
            self.get_head_img_pro(wxid)

            img_dir = PRJ_PATH + '/Cache/Head_Img_Cache'
            os.makedirs(img_dir, exist_ok=True)
            file_path = f'{img_dir}/{wxid}.jpg'
            if os.path.exists(file_path):
                return file_path

            sql_query = f'SELECT usrName,smallHeadBuf FROM ContactHeadImg1 WHERE usrName="{wxid}";'
            res = self.query_sql("Misc.db", sql_query)
            # print(f"head img res = {res}")

            if not res:
                OutPut.outPut(f'[-]: 获取头像失败，未找到头像信息')
                return self.get_head_img_pro(wxid)
            head_img_buf = res[0].get('smallHeadBuf')

            # 写入文件
            with open(file_path, 'wb') as f:
                f.write(head_img_buf)
            OutPut.outPut(f'[+]: 获取头像成功，头像路径: {file_path}')

            return file_path
        except Exception as e:
            OutPut.outPut(f'[-]: 获取头像出现错误，错误信息: {e}')
            return self.get_head_img_pro(wxid)

    # 获取高清头像，清晰度高
    def get_head_img_pro(self, wxid):
        try:
            img_dir = PRJ_PATH + '/Cache/Head_Img_Cache'
            os.makedirs(img_dir, exist_ok=True)
            file_path = f'{img_dir}/{wxid}_pro.jpg'
            if os.path.exists(file_path):
                return file_path
            headImgData = self.query_sql("MicroMsg.db",
                                         f"SELECT * FROM ContactHeadImgUrl WHERE usrName = '{wxid}';")
            if headImgData:
                if headImgData[0]:
                    bigHeadImgUrl = headImgData[0]['bigHeadImgUrl']
                    content = requests.get(url=bigHeadImgUrl, timeout=30).content
                    with open(file_path, mode='wb') as f:
                        f.write(content)
                    # 如果头像获取失败，删除文件
                    if calculate_md5(file_path) == 'fee9458c29cdccf10af7ec01155dc7f0':
                        os.remove(file_path)
                        return None
                    return file_path
        except Exception as e:
            OutPut.outPut(f'[-]: 获取头像出现错误，错误信息: {e}')
            return None

    # 获取高清头像，清晰度高
    def get_head_img_pro_url(self, wxid):
        try:
            img_dir = PRJ_PATH + '/Cache/Head_Img_Cache'
            os.makedirs(img_dir, exist_ok=True)
            file_path = f'{img_dir}/{wxid}_pro.jpg'
            headImgData = self.query_sql("MicroMsg.db",
                                         f"SELECT * FROM ContactHeadImgUrl WHERE usrName = '{wxid}';")
            if headImgData:
                if headImgData[0]:
                    bigHeadImgUrl = headImgData[0]['bigHeadImgUrl']
                    content = requests.get(url=bigHeadImgUrl, timeout=30).content
                    with open(file_path, mode='wb') as f:
                        f.write(content)
                    # 如果头像获取失败，删除文件
                    if calculate_md5(file_path) == 'fee9458c29cdccf10af7ec01155dc7f0':
                        os.remove(file_path)
                        return None
                    return bigHeadImgUrl
        except Exception as e:
            OutPut.outPut(f'[-]: 获取头像出现错误，错误信息: {e}')
            return None

    def get_wx_name(self, msg):
        wx_name = self.get_alias_in_chatroom(roomid=msg.roomid, wxid=msg.sender)
        # 如果获取不到群昵称，则获取微信昵称
        if not wx_name:
            wx_name = self.wcf.get_info_by_wxid(wxid=msg.sender).get("name")
        return wx_name

    def get_alias_in_chatroom(self, roomid, wxid):
        with self.db_lock:
            return self.wcf.get_alias_in_chatroom(roomid=roomid, wxid=wxid)

    def query_sql(self, db_name, sql_query):
        with self.db_lock:
            return self.wcf.query_sql(db_name, sql_query)

    def send_at_msg(self, roomid, wxid, content):
        at_msg = f"@{self.get_alias_in_chatroom(roomid=roomid, wxid=wxid)}\n{content}"
        self.wcf.send_text(msg=at_msg, receiver=roomid, aters=wxid)

    def send_at_all_msg(self, roomid, content):
        at_msg = f"@所有人\n{content}"
        self.wcf.send_text(msg=at_msg, receiver=roomid, aters='notify@all')

    def find_latest_msg_db(self):
        db_list = self.wcf.get_dbs()
        db_list = [db for db in db_list if db.startswith('MSG')]
        db_list.sort(reverse=True)
        return db_list[0]

    def send_image_ensure_success(self, path, receiver, retry_count=0):
        if not check_file(path):
            print(f"文件 {path} 不存在或大小大于600B")
            return
        db_name = self.find_latest_msg_db()
        print(db_name)
        try:
            print(self.wcf.send_image(path=path, receiver=receiver))
            time.sleep(0.2)
            sql_query = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                        f'WHERE IsSender = 1 AND Type = 3 AND StrTalker = "{receiver}" ORDER BY localId DESC LIMIT 1;'
            res = self.query_sql(db_name, sql_query)
            print(f"res = {res}")
            local_id = res[0].get('localId')

            def ensure(local_id, path, receiver):
                max_check_retries = 8
                retry_check_count = 0
                msg_svr_id = 0

                while retry_check_count < max_check_retries:
                    time.sleep(1)

                    sql_query_again = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                                      f'WHERE localId = {local_id};'
                    res_again = self.query_sql(db_name, sql_query_again)
                    print(f"res_again = {res_again}")

                    # 撤回消息ID
                    msg_svr_id = res_again[0].get('MsgSvrID')
                    if msg_svr_id != 0:
                        break
                    retry_check_count += 1

                if msg_svr_id == 0:
                    if retry_count < 1:
                        OutPut.outPut('[-]: 图片发送失败,重新发送,回调中...')
                        return self.send_image_ensure_success(path, receiver, retry_count + 1)
                    else:
                        OutPut.outPut('[-]: 已达到最大重试次数,放弃重新发送。')
                        self.wcf.send_file(path=path, receiver=receiver)
                        return

                OutPut.outPut(f'[+]: 图片发送成功')
                # 自己发送成功的图片消息也存到撤回字典中，用于生成表情包
                self.recall_msg_dict.update({str(msg_svr_id): {'content': path, 'ts': time.time()}})
                return

            thread_ensure = threading.Thread(target=ensure, args=(local_id, path, receiver))
            thread_ensure.start()

        except Exception as e:
            OutPut.outPut(f'[-]: 图片发送失败，错误信息: {e}')
            return

    def send_emotion_ensure_success(self, path, receiver, retry_count=0):
        if not check_file(path):
            return
        db_name = self.find_latest_msg_db()
        print(db_name)
        # 表情包大于1000k进行压缩
        if check_file_over_1000k(path) and retry_count > 0:
            with self.counter_lock:
                # 加个标识，转成jpg有时候更好，有时候不好
                is_jpg_better = False
                # 文件先预处理，压缩，如果压缩后还是大于1000k，则进行后续处理
                OutPut.outPut(f'压缩前大小: {os.path.getsize(path) / 1024 / 1024}MB')
                tmp_path = path.replace('.gif', '_tmp.gif')
                gif_minimize(path, tmp_path, quality=40)
                OutPut.outPut(f'压缩后大小: {os.path.getsize(tmp_path) / 1024 / 1024}MB')
                if os.path.getsize(tmp_path) < os.path.getsize(path):
                    # 压缩后文件小于原文件，删除原文件，重命名压缩后文件
                    os.remove(path)
                    os.rename(tmp_path, path)
                    is_jpg_better = True
                    OutPut.outPut(f'[+]: is_jpg_better = {is_jpg_better}')

                if not check_file_over_1000k(path):
                    OutPut.outPut(f'[+]: 表情包一次压缩成功')
                else:
                    OutPut.outPut(f'[-]: 表情包压缩后仍然大于1000k')

                # 向上取整计算步长
                step = math.ceil(os.path.getsize(path) / (1 * 1024 * 1024))
                new_path = path.replace('.gif', '_min.gif')
                # 对于科目三的表情包，特殊处理
                keywords = ['subject3', 'lick_candy']
                if any(keyword in path for keyword in keywords):
                    gif_minimize(path, new_path, step, True, is_jpg=is_jpg_better)
                else:
                    gif_minimize(path, new_path, step, is_jpg=is_jpg_better)
                OutPut.outPut(f'[+]: 表情包压缩成功，压缩后文件名: {new_path}，\n'
                              f'压缩前大小: {os.path.getsize(path) / 1024 / 1024}MB，'
                              f'压缩后大小: {os.path.getsize(new_path) / 1024 / 1024}MB')
                if check_file_over_1000k(new_path):
                    step += 1
                    # 对于科目三的表情包，特殊处理
                    if any(keyword in path for keyword in keywords):
                        gif_minimize(path, new_path, step, True, is_jpg=is_jpg_better)
                    else:
                        gif_minimize(path, new_path, step, is_jpg=is_jpg_better)
                    OutPut.outPut(f'[+]: 表情包再次压缩成功，压缩后文件名: {new_path}，\n'
                                  f'压缩前大小: {os.path.getsize(path) / 1024 / 1024}MB，'
                                  f'压缩后大小: {os.path.getsize(new_path) / 1024 / 1024}MB')
                path = new_path
        try:
            print(self.wcf.send_emotion(path=path, receiver=receiver))
            time.sleep(0.2)
            sql_query = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                        f'WHERE IsSender = 1 AND Type = 47 AND StrTalker = "{receiver}" ORDER BY localId DESC LIMIT 1;'
            res = self.query_sql(db_name, sql_query)
            print(f"res = {res}")
            local_id = res[0].get('localId')

            def ensure(local_id, path, receiver):
                max_check_retries = 8
                retry_check_count = 0
                msg_svr_id = 0

                while retry_check_count < max_check_retries:
                    time.sleep(1)

                    sql_query_again = f'SELECT localId, TalkerId, MsgSvrID, Type, IsSender, CreateTime, StrTalker, StrContent FROM MSG ' \
                                      f'WHERE localId = {local_id};'
                    res_again = self.query_sql(db_name, sql_query_again)
                    print(f"res_again = {res_again}")

                    # 撤回消息ID
                    msg_svr_id = res_again[0].get('MsgSvrID')
                    if msg_svr_id != 0:
                        break
                    retry_check_count += 1

                if msg_svr_id == 0:
                    if retry_count < 1:
                        OutPut.outPut('[-]: 表情发送失败,重新发送,回调中...')
                        return self.send_emotion_ensure_success(path, receiver, retry_count + 1)
                    else:
                        OutPut.outPut('[-]: 已达到最大重试次数,放弃重新发送。')
                        self.wcf.send_file(path=path, receiver=receiver)
                        return
                OutPut.outPut('[+]: 表情发送成功')
                return

            thread_ensure = threading.Thread(target=ensure, args=(local_id, path, receiver))
            thread_ensure.start()

        except Exception as e:
            OutPut.outPut(f'[-]: 表情发送失败，错误信息: {e}')
            return


def check_file(path):
    if os.path.exists(path):
        file_size = os.path.getsize(path)
        if file_size > 600:  # 256 B
            return True
    return False


def check_file_over_1000k(path):
    if os.path.exists(path):
        file_size = os.path.getsize(path)
        if file_size > 1000 * 1024:
            return True
    return False


# 保存状态到文件
def save_state_file(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# 加载状态从文件
def load_state_file(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
