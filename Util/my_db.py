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
        获取指定成语的信息
        """
        dev = self.db.select('idiom', columns='word', where='first = "{}"'.format(last))
        if dev:
            return [d[0] for d in dev]
        return []


if __name__ == '__main__':
    db = IdiomDB('/home/frz/github/NGCBot/Config/idiom.db')
    print(db.get_info_by_word('喜上眉梢'))
    print(db.get_words_by_first('xiao'))
