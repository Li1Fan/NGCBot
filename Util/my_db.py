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


if __name__ == '__main__':
    db = IdiomDB('/home/frz/github/NGCBot/Config/idiom.db')
    # print(db.get_info_by_word('喜上眉梢'))
    # print(db.get_last_by_word('喜上眉梢'))
    # print(db.get_words_by_first(''))
    print(db.get_words_by_word('喜上眉梢'))

    lst = ['a', 'an', 'ang', 'ao', 'ba', 'bai', 'ban', 'bang', 'bao', 'bei', 'ben', 'beng', 'bi', 'bian', 'biao', 'bie',
           'bin', 'bing', 'bo', 'bu', 'ca', 'cai', 'can', 'cang', 'cao', 'ce', 'cen', 'ceng', 'cha', 'chai', 'chan',
           'chang', 'chao', 'che', 'chen', 'cheng', 'chi', 'chong', 'chou', 'chu', 'chuai', 'chuan', 'chuang', 'chui',
           'chun', 'chuo', 'ci', 'cong', 'cu', 'cuan', 'cui', 'cun', 'cuo', 'da', 'dai', 'dan', 'dang', 'dao', 'de',
           'deng', 'di', 'dian', 'diao', 'die', 'ding', 'diu', 'dong', 'dou', 'du', 'duan', 'dui', 'dun', 'duo', 'e',
           'en', 'er', 'fa', 'fan', 'fang', 'fei', 'fen', 'feng', 'fo', 'fu', 'ga', 'gai', 'gan', 'gang', 'gao', 'ge',
           'gen', 'geng', 'gong', 'gou', 'gu', 'gua', 'guai', 'guan', 'guang', 'gui', 'gun', 'guo', 'hai', 'han',
           'hang', 'hao', 'he', 'hei', 'hen', 'heng', 'hong', 'hou', 'hu', 'hua', 'huai', 'huan', 'huang', 'hui', 'hun',
           'huo', 'ji', 'jia', 'jian', 'jiang', 'jiao', 'jie', 'jin', 'jing', 'jiong', 'jiu', 'ju', 'juan', 'jue',
           'jun', 'kai', 'kan', 'kang', 'kao', 'ke', 'ken', 'keng', 'kong', 'kou', 'ku', 'kua', 'kuai', 'kuan', 'kuang',
           'kui', 'kun', 'kuo', 'la', 'lai', 'lan', 'lang', 'lao', 'le', 'lei', 'leng', 'li', 'lian', 'liang', 'liao',
           'lie', 'lin', 'ling', 'liu', 'long', 'lou', 'lu', 'luan', 'lun', 'luo', 'lv', 'lve', 'ma', 'mai']
    # for i in lst:
    #     if not db.get_words_by_first(i):
    #         print(i, db.get_words_by_first(i))
