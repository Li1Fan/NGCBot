import os
import threading
import time
import traceback
from datetime import datetime
from functools import wraps

import chinese_calendar
import schedule
import yaml

from Api_Server.Api_Main_Server import Api_Main_Server
from Cache.Cache_Main_Server import Cache_Main_Server
from Db_Server.Db_Main_Server import Db_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from OutPut import OutPut
from Util.my_db import TimingMsgDB
from Util.text_parse import parse_chinese_time, parse_chinese_date
from advanced_path import PRJ_PATH


# def check_workday(flag=True):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(self, *args, **kwargs):
#             if flag:
#                 # 获取当前日期
#                 current_date = datetime.now().date()
#                 # 如果不是工作日，直接返回
#                 if not chinese_calendar.is_workday(current_date):
#                     return
#             return func(self, *args, **kwargs)
#
#         return wrapper
#
#     return decorator

def check_workday(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # 获取当前日期
        current_date = datetime.now().date()
        # 如果不是工作日，直接返回
        if not chinese_calendar.is_workday(current_date):
            return
        return func(self, *args, **kwargs)

    return wrapper


def global_lock(func):
    lock = threading.Lock()

    def wrapper(*args, **kwargs):
        with lock:
            result = func(*args, **kwargs)
        return result

    return wrapper


class Push_Main_Server:
    def __init__(self, wcf):
        self.wcf = wcf
        current_path = os.path.dirname(__file__)
        config = yaml.load(open(current_path + '/../Config/config.yaml', encoding='UTF-8'), yaml.Loader)
        self.db_file = current_path + '/../Config/Point_db.db'
        self.Ams = Api_Main_Server(wcf=self.wcf)
        self.Dms = Db_Main_Server(wcf=self.wcf)
        self.Cms = Cache_Main_Server(wcf=self.wcf)
        self.Dps = Db_Point_Server()

        # 下班消息
        self.Off_Work_msg = config['Push_Config']['Key_Word']['Off_Work_Msg']

        # 推送时间
        self.Morning_Push_Time = config['Push_Config']['Morning_Push_Time']
        self.Morning_Page_Time = config['Push_Config']['Morning_Page_Time']
        self.Evening_Page_Time = config['Push_Config']['Evening_Page_Time']
        self.Off_Work_Time = config['Push_Config']['Off_Work_Time']
        self.Fish_Time = config['Push_Config']['Fish_Time']
        self.Kfc_Time = config['Push_Config']['Kfc_Time']

    # 早安寄语推送
    @check_workday
    def push_morning_msg(self):
        OutPut.outPut('[*]: 定时早安寄语推送中... ...')
        msg = self.Ams.get_morning()
        msg = "早安！打工人\n" + msg
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=msg, receiver=room_id)
        OutPut.outPut('[+]: 定时早安寄语推送成功！！！')

    # 60s推送
    @check_workday
    def push_60s(self):
        OutPut.outPut('[*]: 定时60s推送中... ...')
        msg = self.Ams.get_60s()
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=msg, receiver=room_id)
        OutPut.outPut('[+]: 定时60s推送成功！！！')

    # 早报推送
    def push_morning_page(self):
        OutPut.outPut('[*]: 定时早报推送中... ...')
        morning_msg = self.Ams.get_freebuf_news()
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=morning_msg, receiver=room_id)
        OutPut.outPut('[+]: 定时早报推送成功！！！')

    # 晚报推送
    def push_evening_page(self):
        OutPut.outPut('[*]: 定时晚报推送中... ...')
        evening_msg = self.Ams.get_safety_news()
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=evening_msg, receiver=room_id)
        OutPut.outPut('[+]: 定时晚报推送成功！！！')

    # 下班推送
    @check_workday
    def push_off_work(self):
        OutPut.outPut('[*]: 定时下班消息推送中... ...')
        off_Work_msg = self.Off_Work_msg.replace('\\n', '\n')
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=off_Work_msg, receiver=room_id)
        OutPut.outPut('[+]: 定时下班消息推送成功！！！')

    # 摸鱼日记推送
    @check_workday
    def push_fish(self):
        OutPut.outPut(f'[*]: 定时摸鱼日记推送中... ...')
        room_dicts = self.Dms.show_push_rooms()
        fish_img = self.Ams.get_fish()
        for room_id in room_dicts.keys():
            self.wcf.send_image(path=fish_img, receiver=room_id)
        OutPut.outPut('[+]: 定时摸鱼日记推送成功！！！')

    # 签到表清空
    def clear_sign(self):
        OutPut.outPut(f'[*]: 定时签到表清空中... ...')
        self.Dps.clear_sign()
        OutPut.outPut(f'[+]: 定时签到表清空成功！！！')

    # 缓存文件夹清空
    def clear_cache(self):
        OutPut.outPut(f'[*]: 定时缓存文件夹清空中... ...')
        self.Cms.delete_file()
        OutPut.outPut(f'[+]: 定时缓存文件夹清空成功！！！')

    # 清空日志文件夹
    @staticmethod
    def clear_log():
        OutPut.outPut(f'[*]: 定时日志文件夹清空中... ...')
        with open(f"{PRJ_PATH}/Log/log.txt", 'w') as f:
            f.write(f'NEW\n')
        OutPut.outPut(f'[+]: 定时日志文件夹清空成功！！！')

    # 每周四KFC文案推送
    @check_workday
    def push_kfc(self):
        OutPut.outPut(f'[*]: 定时KFC文案推送中... ...')
        kfc_msg = self.Ams.get_kfc()
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=kfc_msg, receiver=room_id)
        OutPut.outPut(f'[+]: 定时KFC文案发送成功！！！')

    def run(self):
        # # schedule.every().day.at(self.Morning_Push_Time).do(self.push_morning_msg)
        # # schedule.every().day.at(self.Morning_Page_Tome).do(self.push_morning_page)
        # schedule.every().day.at(self.Morning_Page_Time).do(self.push_60s)
        # schedule.every().day.at(self.Fish_Time).do(self.push_fish)
        # schedule.every().thursday.at(self.Kfc_Time).do(self.push_kfc)
        # # schedule.every().day.at(self.Evening_Page_Time).do(self.push_evening_page)
        # schedule.every().day.at(self.Off_Work_Time).do(self.push_off_work)
        # schedule.every().day.at('00:00').do(self.clear_sign)
        # # schedule.every().day.at('03:00').do(self.clear_cache)
        # OutPut.outPut(f'[+]: 已开启定时推送服务！！！')

        schedule.every().day.at(self.Morning_Push_Time).do(self.push_morning_msg)
        schedule.every().day.at(self.Morning_Page_Time).do(self.push_60s)
        schedule.every().day.at(self.Fish_Time).do(self.push_fish)
        schedule.every().thursday.at(self.Kfc_Time).do(self.push_kfc)
        schedule.every().day.at(self.Off_Work_Time).do(self.push_off_work)
        schedule.every().day.at('00:00').do(self.clear_sign)
        schedule.every().day.at('03:00').do(self.clear_cache)

        OutPut.outPut(f'[+]: 已开启定时推送服务！！！')

        while True:
            schedule.run_pending()
            time.sleep(30)


class TimingMsg:
    def __init__(self, wcf):
        self.wcf = wcf
        # 存储定时消息的job列表
        self.jobs = []

        db_path = f"{PRJ_PATH}/Config/job.db"
        self.db_timing = TimingMsgDB(db_path=db_path)

    def init_timing_msg(self):
        jobs = self.db_timing.get_all_jobs()
        for job in jobs:
            try:
                id_ = job.get('id', '')
                days = job.get('days', '')
                times = job.get('times', '')
                content = job.get('content', '')
                roomid = job.get('roomid', '')
                wxid = job.get('wxid', '')
                type_ = job.get('type', '')
                if type_ == "normal_remind":
                    schedule_obj = self.parse_task(days)
                    if not schedule_obj:
                        continue
                    job_obj = schedule_obj.at(times).do(self.send_msg, roomid, wxid, content)
                    job_dict = {"id": id_, "job_obj": job_obj}
                    self.jobs.append(job_dict)
                elif type_ == "onetime_remind":
                    job_obj = schedule.every().days.at(times).do(self.send_msg, roomid, wxid, content, days)
                    job_dict = {"id": id_, "job_obj": job_obj}
                    self.jobs.append(job_dict)
            except Exception as e:
                OutPut.outPut(f'[-]: 定时任务执行失败, 错误信息: {e}')
                OutPut.outPut(f'[-]: {traceback.format_exc()}')

    @global_lock
    def add_normal_remind_task(self, days, times, content, roomid, wxid):
        try:
            times = parse_chinese_time(times)
            if not parse_chinese_time(times):
                content = '时间格式错误，任务示例：\n“定时提醒 周一/星期一/每天 十点/一点十分/一时十分/1:10 摸鱼”'
                self.send_at_msg(roomid, wxid, content)
                return False
            schedule_obj = self.parse_task(days)
            if not schedule_obj:
                content = '日期格式错误，任务示例：\n“定时提醒 周一/星期一/每天 十点/一点十分/一时十分/1:10 摸鱼”'
                self.send_at_msg(roomid, wxid, content)
                return False
            job_obj = schedule_obj.at(times).do(self.send_msg, roomid, wxid, content)
            self.db_timing.insert_job(days, times, content, roomid, wxid, "normal_remind")
            id_ = self.db_timing.get_last_id()
            job_dict = {"id": id_, "job_obj": job_obj}
            self.jobs.append(job_dict)
            content = "定时提醒任务添加成功，可回复“查看提醒”进行查看！"
            self.send_at_msg(roomid, wxid, content)
            return True
        except Exception as e:
            OutPut.outPut(f'[-]: 定时提醒任务添加失败, 错误信息: {e}')
            OutPut.outPut(f'[-]: {traceback.format_exc()}')
            return False

    @global_lock
    def add_onetime_remind_task(self, days, times, content, roomid, wxid):
        try:
            times = parse_chinese_time(times)
            if not parse_chinese_time(times):
                content = '时间格式错误，任务示例：\n“单次提醒 明天/12.7/12月7日 十点/一点十分/一时十分/1:10 摸鱼”'
                self.send_at_msg(roomid, wxid, content)
                return False
            date_str = parse_chinese_date(days)
            if not date_str:
                content = '日期格式错误，，任务示例：\n“单次提醒 明天/12.7/12月7日 十点/一点十分/一时十分/1:10 摸鱼”'
                self.send_at_msg(roomid, wxid, content)
                return False
            job_obj = schedule.every().days.at(times).do(self.send_msg, roomid, wxid, content, date_str)
            self.db_timing.insert_job(date_str, times, content, roomid, wxid, "onetime_remind")
            id_ = self.db_timing.get_last_id()
            job_dict = {"id": id_, "job_obj": job_obj}
            self.jobs.append(job_dict)
            content = "单次提醒任务添加成功，可回复“查看提醒”进行查看！"
            self.send_at_msg(roomid, wxid, content)
            return True
        except Exception as e:
            OutPut.outPut(f'[-]: 定时提醒任务添加失败, 错误信息: {e}')
            OutPut.outPut(f'[-]: {traceback.format_exc()}')
            return False

    @global_lock
    def delete_job(self, id_, roomid, wxid):
        try:
            job = self.db_timing.get_job_by_id(id_)
            if not job:
                content = '定时提醒任务删除失败！不存在该任务'
                self.send_at_msg(roomid, wxid, content)
                return False
            if job.get('roomid') != roomid or job.get('wxid') != wxid:
                content = '定时提醒任务删除失败！非您或者本群的任务'
                self.send_at_msg(roomid, wxid, content)
                return False
            self.db_timing.delete_job_by_id(id_)
            for job_dict in self.jobs:
                if job_dict.get('id') == id_:
                    schedule.cancel_job(job_dict.get('job_obj'))
                    self.jobs.remove(job_dict)
                    content = f'您的定时提醒已删除：\n{job.get("days")} {job.get("times")} {job.get("content")}'
                    self.send_at_msg(roomid, wxid, content)
                    return True
            content = '定时提醒任务删除失败！'
            self.send_at_msg(roomid, wxid, content)
            return False
        except Exception as e:
            OutPut.outPut(f'[-]: 定时提醒任务删除失败, 错误信息: {e}')
            OutPut.outPut(f'[-]: {traceback.format_exc()}')
            return False

    def show_jobs(self, roomid, wxid):
        jobs = self.db_timing.get_jobs_by_roomid_and_wx_id(roomid, wxid)
        if not jobs:
            show_msg = '您还没有设置定时提醒哦！'
            self.send_at_msg(roomid, wxid, show_msg)
        job_list = []
        for job in jobs:
            job_str = f'ID: {job.get("id")}, 时间: {job.get("days")} {job.get("times")}, 内容: {job.get("content")}'
            job_list.append(job_str)

        show_msg = '您的定时提醒如下：\n' + '\n'.join(job_list)
        self.send_at_msg(roomid, wxid, show_msg)

    @staticmethod
    def parse_task(days_info):
        days_mapping = {
            ("周一", "星期一"): schedule.every().monday,
            ("周二", "星期二"): schedule.every().tuesday,
            ("周三", "星期三"): schedule.every().wednesday,
            ("周四", "星期四"): schedule.every().thursday,
            ("周五", "星期五"): schedule.every().friday,
            ("周六", "星期六"): schedule.every().saturday,
            ("周日", "星期日"): schedule.every().sunday,
            ("每天",): schedule.every().day
        }

        for key in days_mapping:
            if days_info in key:
                job_obj = days_mapping[key]
                return job_obj

        return None

    def send_msg(self, roomid, wxid, content, date_str=None):
        try:
            # 用于控制单次提醒
            if date_str:
                remind_datatime = datetime.strptime(date_str, "%Y-%m-%d")
                if datetime.now().date() != remind_datatime.date():
                    return
            timing_content = "这是您的定时提醒：\n {content}"
            self.send_at_msg(roomid, wxid, timing_content)
        except Exception as e:
            OutPut.outPut(f'[-]: 定时提醒发送失败, 错误信息: {e}')
            OutPut.outPut(f'[-]: {traceback.format_exc()}')

    def send_at_msg(self, roomid, wxid, content):
        at_msg = f"@{self.wcf.get_alias_in_chatroom(roomid=roomid, wxid=wxid)}\n{content}"
        self.wcf.send_text(msg=at_msg, receiver=roomid, aters=wxid)


if __name__ == '__main__':
    Pms = Push_Main_Server('1')
    print(Pms.push_morning_msg())
