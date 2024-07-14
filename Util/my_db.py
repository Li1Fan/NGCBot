from collections import OrderedDict

from Util.my_sqlite import MySQLite


class IdiomDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.db = MySQLite(self.db_path)

    def get_info_by_word(self, word: str) -> dict:
        """
        获取指定成语的信息
        """
        dev = self.db.select('idiom', where='word = "{}"'.format(word))
        if dev:
            dev_dict = {
                "id": dev[0][0],
                "derivation": dev[0][1],
                "example": dev[0][2],
                "explanation": dev[0][3],
                "pinyin": dev[0][4],
                "word": dev[0][5],
                "abbreviation": dev[0][6],
                "pinyin_r": dev[0][7],
                "first": dev[0][8],
                "last": dev[0][9],
            }
            return dev_dict
        return {}

    def get_words_by_first(self, last: str) -> list:
        """
        通过第一个拼音获取成语
        """
        dev = self.db.select('idiom', columns='word', where='first = "{}"'.format(last))
        if dev:
            return [d[0] for d in dev]
        return []

    def get_last_by_word(self, word: str) -> str:
        """
        通过成语获取最后一个拼音
        """
        dev = self.db.select('idiom', columns='last', where='word = "{}"'.format(word))
        if dev:
            return dev[0][0]
        return ''

    def get_words_by_word(self, word: str) -> list:
        """
        通过成语获取接龙的成语列表
        """
        last = self.get_last_by_word(word)
        return self.get_words_by_first(last)

    def insert_word(self, word: str, derivation: str, example: str, explanation: str, pinyin: str, abbreviation: str,
                    pinyin_r: str, first: str, last: str) -> None:
        """
        插入一个成语
        """
        self.db.insert('idiom', {
            'word': word,
            'derivation': derivation,
            'example': example,
            'explanation': explanation,
            'pinyin': pinyin,
            'abbreviation': abbreviation,
            'pinyin_r': pinyin_r,
            'first': first,
            'last': last
        })

    def get_common_words(self) -> list:
        """
        获取常用成语
        """
        dev = self.db.select('idiom_common', columns='idiom')
        if dev:
            return [d[0] for d in dev]
        return []

    def get_common_word_info_by_word(self, word: str) -> dict:
        """
        获取指定常用成语的信息
        """
        dev = self.db.select('idiom_common', where='idiom = "{}"'.format(word))
        if dev:
            return self.get_info_by_word(word)
        return {}


class EmojiDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.db = MySQLite(self.db_path)

    def get_info_by_id(self, id: int) -> dict:
        """
        通过id获取表情包
        """
        dev = self.db.select('idiom', where='id = "{}"'.format(id))
        if dev:
            dev_dict = {
                "id": dev[0][0],
                "idiom": dev[0][1],
                "emoji": dev[0][2]
            }
            return dev_dict
        return {}

    def get_info_by_idiom(self, idiom: str) -> dict:
        """
        通过成语获取表情包
        """
        dev = self.db.select('idiom', where='idiom = "{}"'.format(idiom))
        if dev:
            dev_dict = {
                "id": dev[0][0],
                "idiom": dev[0][1],
                "emoji": dev[0][2]
            }
            return dev_dict
        return {}

    def insert_idiom_common(self, idiom: str) -> None:
        """
        插入一个常用成语
        """
        self.db.insert('idiom_common', {
            'idiom': idiom
        })

    def get_common_idiom_info_by_id(self, id_: int) -> dict:
        """
        通过id获取常用成语表情包
        """
        dev = self.db.select('idiom_common', where='id = "{}"'.format(id_))
        if dev:
            return self.get_info_by_idiom(dev[0][1])
        return {}


# 定时消息，应包括定时提醒、定时任务、一次提醒？一次任务？
class TimingMsgDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.db = MySQLite(self.db_path)
        self.init_db()

    def init_db(self) -> None:
        columns = OrderedDict({'id': 'integer primary key autoincrement not null',
                               'days': 'text not null',
                               'times': 'text not null',
                               'content': 'text not null',
                               'roomid': 'text not null',
                               'wxid': 'text not null',
                               'type': 'text'})

        self.db.create_table('job', columns)

    def insert_job(self, days: str, times: str, content: str, roomid: str, wxid: str, type_: str = "") -> bool:
        ret = self.db.insert('job', {
            'days': days,
            'times': times,
            'content': content,
            'roomid': roomid,
            'wxid': wxid,
            'type': type_
        })
        return ret

    def delete_job_by_id(self, id_: int) -> bool:
        ret = self.db.delete('job', where='id = "{}"'.format(id_))
        return ret

    def delete_job_by_roomid_and_wx_id(self, roomid: str, wxid: str) -> bool:
        ret = self.db.delete('job', where='roomid = "{}" and wxid = "{}"'.format(roomid, wxid))
        return ret

    def get_all_jobs(self) -> list:
        dev = self.db.select('job')
        if dev:
            dev_list = []
            for d in dev:
                dev_dict = {
                    "id": d[0],
                    "days": d[1],
                    "times": d[2],
                    "content": d[3],
                    "roomid": d[4],
                    "wxid": d[5],
                    "type": d[6]
                }
                dev_list.append(dev_dict)
            return dev_list
        return []

    def get_job_by_id(self, id_: int) -> dict:
        dev = self.db.select('job', where='id = "{}"'.format(id_))
        if dev:
            dev_dict = {
                "id": dev[0][0],
                "days": dev[0][1],
                "times": dev[0][2],
                "content": dev[0][3],
                "roomid": dev[0][4],
                "wxid": dev[0][5],
                "type": dev[0][6]
            }
            return dev_dict
        return {}

    def get_jobs_by_roomid_and_wx_id(self, roomid: str, wxid: str) -> list:
        dev = self.db.select('job', where='roomid = "{}" and wxid = "{}"'.format(roomid, wxid))
        if dev:
            dev_list = []
            for d in dev:
                dev_dict = {
                    "id": d[0],
                    "days": d[1],
                    "times": d[2],
                    "content": d[3],
                    "roomid": d[4],
                    "wxid": d[5],
                    "type": d[6]
                }
                dev_list.append(dev_dict)
            return dev_list
        return []

    def get_last_id(self) -> int:
        dev = self.db.select('job', columns='id', order='id desc', limit=1)
        if dev:
            return dev[0][0]
        return 0


if __name__ == "__main__":
    job_db = TimingMsgDB('job.db')
    job_db.insert_job('周一', '13:00', '早安！打工人', '123456', '654321')
    print(job_db.get_job_by_id(1))
    print(job_db.get_jobs_by_roomid_and_wx_id('123456', '654321'))
    # print(job_db.delete_job_by_id(1))
    print(job_db.get_last_id())

    job_db.delete_job_by_roomid_and_wx_id('123456', '654321')
    print(job_db.get_jobs_by_roomid_and_wx_id('123456', '654321'))
    # db = IdiomDB('/home/frz/github/NGCBot/Config/idiom.db')
    # print(db.get_info_by_word('沧海横流'))
    # print(db.get_last_by_word('沧海横流'))
    # # print(db.get_words_by_first(''))
    # # print(db.get_words_by_word('喜上眉梢'))
    # # db.insert_word("沧海横流", "“沧海横流，玉石同碎。” 晋·袁宏《三国名臣序赞》", "无", "海水四处奔流，比喻政治混乱，社会动荡。",
    # #                "cāng hǎi héng liú", "chhl", "cang hai heng liu", "cang", "liu")
    #
    # print(db.get_common_word_info_by_word('人生如寄'))
    #
    # db_emoji = EmojiDB('/home/frz/github/NGCBot/Config/emoji.db')
    # print(db_emoji.get_info_by_id(1033))
    # print(db_emoji.get_common_idiom_info_by_id(1643))
    #
    # # i = 0
    # # for w in db.get_common_words():
    # #     if db_emoji.get_emoji_by_idiom(w):
    # #         print(w)
    # #         db_emoji.insert_idiom_common(w)
    # #         i += 1
    # # print(i)
