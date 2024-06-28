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


if __name__ == '__main__':
    db = IdiomDB('/home/frz/github/NGCBot/Config/idiom.db')
    print(db.get_info_by_word('沧海横流'))
    print(db.get_last_by_word('沧海横流'))
    # print(db.get_words_by_first(''))
    # print(db.get_words_by_word('喜上眉梢'))
    # db.insert_word("沧海横流", "“沧海横流，玉石同碎。” 晋·袁宏《三国名臣序赞》", "无", "海水四处奔流，比喻政治混乱，社会动荡。",
    #                "cāng hǎi héng liú", "chhl", "cang hai heng liu", "cang", "liu")

    print(db.get_common_word_info_by_word('人生如寄'))

    db_emoji = EmojiDB('/home/frz/github/NGCBot/Config/emoji.db')
    print(db_emoji.get_info_by_id(1033))
    print(db_emoji.get_common_idiom_info_by_id(1643))

    # i = 0
    # for w in db.get_common_words():
    #     if db_emoji.get_emoji_by_idiom(w):
    #         print(w)
    #         db_emoji.insert_idiom_common(w)
    #         i += 1
    # print(i)
