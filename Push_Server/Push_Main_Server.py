import os
import time
from datetime import datetime

import chinese_calendar
import schedule
import yaml

from Api_Server.Api_Main_Server import Api_Main_Server
from Cache.Cache_Main_Server import Cache_Main_Server
from Db_Server.Db_Main_Server import Db_Main_Server
from Db_Server.Db_Point_Server import Db_Point_Server
from OutPut import OutPut


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
    def push_morning_msg(self):
        OutPut.outPut('[*]: 定时早安寄语推送中... ...')
        msg = self.Ams.get_morning()
        msg = "早安！打工人\n" + msg
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=msg, receiver=room_id)
        OutPut.outPut('[+]: 定时早安寄语推送成功！！！')

    # 60s推送
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
    def push_off_work(self):
        OutPut.outPut('[*]: 定时下班消息推送中... ...')
        off_Work_msg = self.Off_Work_msg.replace('\\n', '\n')
        room_dicts = self.Dms.show_push_rooms()
        for room_id in room_dicts.keys():
            self.wcf.send_text(msg=off_Work_msg, receiver=room_id)
        OutPut.outPut('[+]: 定时下班消息推送成功！！！')

    # 摸鱼日记推送
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

    # 每周四KFC文案推送
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

        # 创建两个schedule对象，分别用于工作日和非工作日
        # TODO:推送在周一零点时出现过异常，待排查
        workday_schedule = schedule.Scheduler()
        non_workday_schedule = schedule.Scheduler()

        workday_schedule.every().day.at(self.Morning_Push_Time).do(self.push_morning_msg)
        workday_schedule.every().day.at(self.Morning_Page_Time).do(self.push_60s)
        workday_schedule.every().day.at(self.Fish_Time).do(self.push_fish)
        workday_schedule.every().thursday.at(self.Kfc_Time).do(self.push_kfc)
        workday_schedule.every().day.at(self.Off_Work_Time).do(self.push_off_work)
        workday_schedule.every().day.at('00:00').do(self.clear_sign)
        workday_schedule.every().day.at('03:00').do(self.clear_cache)

        non_workday_schedule.every().day.at('00:00').do(self.clear_sign)
        non_workday_schedule.every().day.at('03:00').do(self.clear_cache)

        OutPut.outPut(f'[+]: 已开启定时推送服务！！！')

        while True:
            # 获取当前日期
            current_date = datetime.now().date()

            # 根据日期判断是否为工作日
            if chinese_calendar.is_workday(current_date):
                workday_schedule.run_pending()
            else:
                non_workday_schedule.run_pending()
            time.sleep(30)


if __name__ == '__main__':
    Pms = Push_Main_Server('1')
    print(Pms.Off_Work_msg.replace('\\n', '\n'))
