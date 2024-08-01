import json
import os
import random

import requests

from advanced_path import PRJ_PATH

# 所有表情选项
all_emojis = ["play_together", "bluearchive", "5000choyen", "play_game", "hold_tight", "my_opinion", "jump",
              "not_call_me", "shock", "windmill_turn", "hutao_bite", "always", "capoo_rip", "daynight", "tease",
              "flash_blind", "printing", "follow", "rip_angrily", "little_angel", "scratch_head", "thump_wildly",
              "psyduck", "walnut_pad", "perfect", "thump", "tomb_yeah", "chase_train", "what_I_want_to_do", "why_at_me",
              "kirby_hammer", "universal", "applaud", "ascension", "clown", "scratchcard", "look_this_icon",
              "left_right_jump", "make_friend", "capoo_strike", "high_EQ", "beat_head", "nekoha_holdsign", "trance",
              "think_what", "dont_go_near", "rotate_3d", "cyan", "murmur", "loading", "taunt", "imprison", "bad_news",
              "repeat", "roll", "add_chaos", "meteor", "wooden_fish", "turn", "dinosaur", "symmetric", "funny_mirror",
              "fanatic", "petpet", "mourning", "maimai_awaken", "douyin", "twist", "read_book", "knock", "washer",
              "bronya_holdsign", "charpic", "capoo_say", "eat", "nijika_holdsign", "need", "paint", "ask", "wujing",
              "blood_pressure", "punch", "love_you", "out", "nokia", "tankuku_raisesign", "bite", "this_chicken",
              "pass_the_buck", "shutup", "beat_up", "coupon", "run", "rip", "capoo_rub", "pat", "oshi_no_ko", "stew",
              "anya_suki", "my_wife", "pornhub", "garbage", "suck", "tightly", "safe_sense", "confuse", "mihoyo",
              "certificate", "addiction", "klee_eat", "keep_away", "dog_of_vtb", "distracted", "hold_grudge", "smash",
              "hammer", "raise_sign", "kick_ball", "look_flat", "worship", "captain", "decent_kiss", "wave", "osu",
              "incivilization", "alike", "marriage", "bocchi_draft", "divorce", "call_110", "walnut_zoom", "fencing",
              "wallpaper", "prpr", "capoo_draw", "pinch", "acg_entrance", "you_should_call", "learn", "rub", "painter",
              "potato", "why_have_hands", "throw", "run_away", "note_for_leave", "let_me_in", "interview",
              "firefly_holdsign", "dont_touch", "scroll", "wangjingze", "weisuoyuwei", "chanshenzi", "qiegewala",
              "shuifandui", "zengxiaoxian", "yalidaye", "nihaosaoa", "shishilani", "wunian", "maikease",
              "ace_attorney_dialog", "my_friend", "vibrate", "police", "police1", "dog_dislike", "sit_still",
              "rise_dead", "wish_fail", "karyl_point", "throw_gif", "name_generator", "fill_head", "kaleidoscope",
              "cover_face", "youtube", "hit_screen", "slap", "what_he_wants", "lost_dog", "subject3", "frieren_take",
              "listen_music", "luoyonghao_say", "guichu", "raise_image", "bubble_tea", "maimai_join", "father_work",
              "slogan", "always_like", "genshin_start", "anti_kidnap", "find_chips", "together", "luxun_say",
              "good_news", "tom_tease", "teach", "overtime", "caoshen_bite", "kiss", "pound", "dianzhongdian",
              "telescope", "play", "jiji_king", "wakeup", "swirl_turn", "jiujiu", "hug_leg", "step_on", "back_to_work",
              "china_flag", "fight_with_sunuo", "lim_x_0", "google", "no_response", "support", "crawl", "gun", "loop"]

# 所有支持图片参数的图片表情选项
all_jpg_emojis_with_jpg = ['hold_tight', 'addiction', 'you_should_call', 'dont_go_near', 'mourning', 'pinch',
                           'dinosaur', 'paint', 'walnut_pad', 'lim_x_0', 'rip', 'jiji_king', 'acg_entrance', 'potato',
                           'distracted', 'together', 'kaleidoscope', 'look_flat', 'anya_suki', 'perfect', 'father_work',
                           'cover_face', 'look_this_icon', 'oshi_no_ko', 'support', 'decent_kiss', 'painter', 'always',
                           'dont_touch', 'fill_head', 'loading', 'clown', 'tomb_yeah', 'name_generator', 'lost_dog',
                           'dog_of_vtb', 'frieren_take', 'read_book', 'throw', 'little_angel', 'maimai_awaken',
                           'trance', 'why_at_me', 'sit_still', 'what_I_want_to_do', 'raise_image', 'mihoyo',
                           'rip_angrily', 'china_flag', 'my_friend', 'teach', 'stew', 'anti_kidnap', 'divorce',
                           'this_chicken', 'think_what', 'follow', 'out', 'keep_away', 'prpr', 'gun', 'marriage',
                           'interview', 'bubble_tea', 'incivilization', 'fight_with_sunuo', 'what_he_wants',
                           'let_me_in', 'universal', 'alike', 'coupon', 'police', 'smash', 'dianzhongdian', 'cyan',
                           'genshin_start', 'blood_pressure', 'crawl', 'karyl_point', 'charpic', 'back_to_work',
                           'add_chaos', 'taunt', 'note_for_leave', 'play_game', 'symmetric', 'my_wife', 'maimai_join',
                           'need', 'overtime', 'safe_sense', 'no_response', 'learn', 'police1']

# 所有支持图片参数的表情选项
all_emojis_with_jpg = ['funny_mirror', 'maimai_awaken', 'hit_screen', 'windmill_turn', 'read_book', 'paint', 'support',
                       'capoo_rip', 'run_away', 'cover_face', 'bocchi_draft', 'sit_still', 'fill_head', 'symmetric',
                       'love_you', 'jiji_king', 'turn', 'potato', 'trance', 'confuse', 'father_work', 'kirby_hammer',
                       'thump_wildly', 'painter', 'capoo_rub', 'hammer', 'my_friend', 'fight_with_sunuo', 'printing',
                       'left_right_jump', 'smash', 'look_this_icon', 'throw_gif', 'genshin_start', 'caoshen_bite',
                       'wallpaper', 'dont_go_near', 'play', 'why_at_me', 'applaud', 'hutao_bite', 'play_together',
                       'always', 'addiction', 'subject3', 'play_game', 'charpic', 'mihoyo', 'frieren_take', 'dinosaur',
                       'lim_x_0', 'dog_of_vtb', 'kaleidoscope', 'telescope', 'jiujiu', 'back_to_work', 'karyl_point',
                       'garbage', 'chase_train', 'what_he_wants', 'anti_kidnap', 'hold_tight', 'decent_kiss', 'divorce',
                       'swirl_turn', 'capoo_strike', 'bubble_tea', 'police', 'thump', 'pass_the_buck', 'loop',
                       'scratch_head', 'dog_dislike', 'pound', 'shock', 'throw', 'interview', 'teach', 'this_chicken',
                       'rip', 'tom_tease', 'walnut_pad', 'perfect', 'oshi_no_ko', 'suck', 'distracted', 'rotate_3d',
                       'wooden_fish', 'twist', 'acg_entrance', 'mourning', 'bite', 'need', 'universal', 'walnut_zoom',
                       'name_generator', 'tease', 'punch', 'listen_music', 'pinch', 'keep_away', 'you_should_call',
                       'cyan', 'kick_ball', 'blood_pressure', 'wave', 'coupon', 'beat_head', 'add_chaos', 'crawl',
                       'my_wife', 'step_on', 'worship', 'marriage', 'gun', 'follow', 'stew', 'capoo_draw', 'pat',
                       'tightly', 'china_flag', 'no_response', 'clown', 'tomb_yeah', 'jump', 'together', 'learn',
                       'washer', 'loading', 'prpr', 'out', 'maimai_join', 'guichu', 'anya_suki', 'alike', 'let_me_in',
                       'petpet', 'klee_eat', 'tankuku_raisesign', 'rip_angrily', 'lost_dog', 'dianzhongdian',
                       'rise_dead', 'hug_leg', 'knock', 'safe_sense', 'raise_image', 'look_flat', 'police1',
                       'what_I_want_to_do', 'little_angel', 'taunt', 'flash_blind', 'think_what', 'incivilization',
                       'note_for_leave', 'vibrate', 'overtime', 'dont_touch', 'eat', 'repeat', 'roll']

# 所有表情选项--字典
all_emojis_dict = {'二次元入口': 'acg_entrance', '添乱': 'add_chaos', '给社会添乱': 'add_chaos', '上瘾': 'addiction',
                   '毒瘾发作': 'addiction', '一样': 'alike', '一直': 'always', '防诱拐': 'anti_kidnap', '阿尼亚喜欢': 'anya_suki',
                   '鼓掌': 'applaud', '继续干活': 'back_to_work', '打工人': 'back_to_work', '拍头': 'beat_head', '啃': 'bite',
                   '高血压': 'blood_pressure', '草神啃': 'caoshen_bite', '咖波画': 'capoo_draw', '咖波撕': 'capoo_rip',
                   '咖波蹭': 'capoo_rub', '咖波贴': 'capoo_rub', '咖波撞': 'capoo_strike', '咖波头槌': 'capoo_strike',
                   '字符画': 'charpic', '追列车': 'chase_train', '追火车': 'chase_train', '国旗': 'china_flag', '小丑': 'clown',
                   '迷惑': 'confuse', '兑换券': 'coupon', '捂脸': 'cover_face', '爬': 'crawl', '群青': 'cyan',
                   '像样的亲亲': 'decent_kiss', '入典': 'dianzhongdian', '典中典': 'dianzhongdian', '黑白草图': 'dianzhongdian',
                   '恐龙': 'dinosaur', '小恐龙': 'dinosaur', '注意力涣散': 'distracted', '离婚协议': 'divorce', '离婚申请': 'divorce',
                   '狗都不玩': 'dog_dislike', '管人痴': 'dog_of_vtb', '不要靠近': 'dont_go_near', '别碰': 'dont_touch', '吃': 'eat',
                   '闭嘴': 'father_work', '我爸爸': 'father_work', '我打宿傩': 'fight_with_sunuo', '我打宿傩吗': 'fight_with_sunuo',
                   '满脑子': 'fill_head', '闪瞎': 'flash_blind', '关注': 'follow', '芙莉莲拿': 'frieren_take',
                   '哈哈镜': 'funny_mirror', '垃圾': 'garbage', '垃圾桶': 'garbage', '原神启动': 'genshin_start', '鬼畜': 'guichu',
                   '手枪': 'gun', '锤': 'hammer', '打穿': 'hit_screen', '打穿屏幕': 'hit_screen', '抱紧': 'hold_tight',
                   '抱大腿': 'hug_leg', '胡桃啃': 'hutao_bite', '不文明': 'incivilization', '采访': 'interview',
                   '急急国王': 'jiji_king', '啾啾': 'jiujiu', '跳': 'jump', '万花筒': 'kaleidoscope', '万花镜': 'kaleidoscope',
                   '凯露指': 'karyl_point', '远离': 'keep_away', '踢球': 'kick_ball', '卡比锤': 'kirby_hammer',
                   '卡比重锤': 'kirby_hammer', '可莉吃': 'klee_eat', '敲': 'knock', '偷学': 'learn', '左右横跳': 'left_right_jump',
                   '让我进去': 'let_me_in', '等价无穷小': 'lim_x_0', '听音乐': 'listen_music', '小天使': 'little_angel',
                   '加载中': 'loading', '看扁': 'look_flat', '看图标': 'look_this_icon', '循环': 'loop', '寻狗启事': 'lost_dog',
                   '永远爱你': 'love_you', '旅行伙伴觉醒': 'maimai_awaken', '旅行伙伴加入': 'maimai_join', '结婚申请': 'marriage',
                   '结婚登记': 'marriage', '米哈游': 'mihoyo', '上香': 'mourning', '我朋友说': 'my_friend', '我老婆': 'my_wife',
                   '这是我老婆': 'my_wife', '亚文化取名机': 'name_generator', '亚名': 'name_generator', '需要': 'need',
                   '你可能需要': 'need', '无响应': 'no_response', '请假条': 'note_for_leave', '我推的网友': 'oshi_no_ko', 'out': 'out',
                   '加班': 'overtime', '这像画吗': 'paint', '小画家': 'painter', '推锅': 'pass_the_buck', '甩锅': 'pass_the_buck',
                   '拍': 'pat', '完美': 'perfect', '摸': 'petpet', '摸摸': 'petpet', '摸头': 'petpet', 'rua': 'petpet',
                   '捏': 'pinch', '捏脸': 'pinch', '玩': 'play', '顶': 'play', '玩游戏': 'play_game', '一起玩': 'play_together',
                   '出警': 'police', '警察': 'police1'}

# 所有支持图片参数的表情选项--字典
all_emojis_dict_with_jpg = {'二次元入口': 'acg_entrance', '添乱': 'add_chaos', '给社会添乱': 'add_chaos', '上瘾': 'addiction',
                            '毒瘾发作': 'addiction', '一样': 'alike', '一直': 'always', '防诱拐': 'anti_kidnap',
                            '阿尼亚喜欢': 'anya_suki', '鼓掌': 'applaud', '继续干活': 'back_to_work', '打工人': 'back_to_work',
                            '拍头': 'beat_head', '啃': 'bite', '高血压': 'blood_pressure', '草神啃': 'caoshen_bite',
                            '咖波画': 'capoo_draw', '咖波撕': 'capoo_rip', '咖波蹭': 'capoo_rub', '咖波贴': 'capoo_rub',
                            '咖波撞': 'capoo_strike', '咖波头槌': 'capoo_strike', '字符画': 'charpic', '追列车': 'chase_train',
                            '追火车': 'chase_train', '国旗': 'china_flag', '小丑': 'clown', '迷惑': 'confuse', '兑换券': 'coupon',
                            '捂脸': 'cover_face', '爬': 'crawl', '群青': 'cyan', '像样的亲亲': 'decent_kiss',
                            '入典': 'dianzhongdian', '典中典': 'dianzhongdian', '黑白草图': 'dianzhongdian', '恐龙': 'dinosaur',
                            '小恐龙': 'dinosaur', '注意力涣散': 'distracted', '离婚协议': 'divorce', '离婚申请': 'divorce',
                            '狗都不玩': 'dog_dislike', '管人痴': 'dog_of_vtb', '不要靠近': 'dont_go_near', '别碰': 'dont_touch',
                            '吃': 'eat', '闭嘴': 'father_work', '我爸爸': 'father_work', '我打宿傩': 'fight_with_sunuo',
                            '我打宿傩吗': 'fight_with_sunuo', '满脑子': 'fill_head', '闪瞎': 'flash_blind', '关注': 'follow',
                            '芙莉莲拿': 'frieren_take', '哈哈镜': 'funny_mirror', '垃圾': 'garbage', '垃圾桶': 'garbage',
                            '原神启动': 'genshin_start', '鬼畜': 'guichu', '手枪': 'gun', '锤': 'hammer', '打穿': 'hit_screen',
                            '打穿屏幕': 'hit_screen', '抱紧': 'hold_tight', '抱大腿': 'hug_leg', '胡桃啃': 'hutao_bite',
                            '不文明': 'incivilization', '采访': 'interview', '急急国王': 'jiji_king', '啾啾': 'jiujiu',
                            '跳': 'jump', '万花筒': 'kaleidoscope', '万花镜': 'kaleidoscope', '凯露指': 'karyl_point',
                            '远离': 'keep_away', '踢球': 'kick_ball', '卡比锤': 'kirby_hammer', '卡比重锤': 'kirby_hammer',
                            '可莉吃': 'klee_eat', '敲': 'knock', '偷学': 'learn', '左右横跳': 'left_right_jump',
                            '让我进去': 'let_me_in', '等价无穷小': 'lim_x_0', '听音乐': 'listen_music', '小天使': 'little_angel',
                            '加载中': 'loading', '看扁': 'look_flat', '看图标': 'look_this_icon', '循环': 'loop',
                            '寻狗启事': 'lost_dog', '永远爱你': 'love_you', '旅行伙伴觉醒': 'maimai_awaken', '旅行伙伴加入': 'maimai_join',
                            '结婚申请': 'marriage', '结婚登记': 'marriage', '米哈游': 'mihoyo', '上香': 'mourning',
                            '我朋友说': 'my_friend', '我老婆': 'my_wife', '这是我老婆': 'my_wife', '亚文化取名机': 'name_generator',
                            '亚名': 'name_generator', '需要': 'need', '你可能需要': 'need', '无响应': 'no_response',
                            '请假条': 'note_for_leave', '我推的网友': 'oshi_no_ko', 'out': 'out', '加班': 'overtime',
                            '这像画吗': 'paint', '小画家': 'painter', '推锅': 'pass_the_buck', '甩锅': 'pass_the_buck', '拍': 'pat',
                            '完美': 'perfect', '摸': 'petpet', '摸摸': 'petpet', '摸头': 'petpet', 'rua': 'petpet',
                            '捏': 'pinch', '捏脸': 'pinch', '玩': 'play', '顶': 'play', '玩游戏': 'play_game',
                            '一起玩': 'play_together', '出警': 'police', '警察': 'police1'}

all_emojis_dict_with_jpg_keys = list(all_emojis_dict_with_jpg.keys())


def generate_meme(filename, emoji, texts=None):
    try:
        if texts is None:
            texts = []

        files = [("images", open(filename, "rb"))]
        args = {"circle": True}
        data = {"texts": texts, "args": json.dumps(args)}

        url = f"http://192.168.222.108:2233/memes/{emoji}/"
        resp = requests.post(url, files=files, data=data)
        if resp.status_code != 200:
            return

        img_dir = PRJ_PATH + '/Cache/Meme_Cache'
        os.makedirs(img_dir, exist_ok=True)

        # 根据 Content-Type 确定文件扩展名
        content_type = resp.headers.get('Content-Type', '')
        if 'image/gif' in content_type:
            result_filename = f"{img_dir}/{emoji}.gif"
        else:
            result_filename = f"{img_dir}/{emoji}.jpg"

        with open(result_filename, "wb") as f:
            f.write(resp.content)

        return result_filename

    except Exception as e:
        print(e)


def generate_random_jpg_by_jpg(filename):
    emoji = random.choice(all_jpg_emojis_with_jpg)
    meme_file = generate_meme(filename, emoji)
    if not meme_file:
        return generate_random_jpg_by_jpg(filename)
    return meme_file


def generate_random_meme_by_jpg(filename):
    emoji = random.choice(all_emojis_with_jpg)
    meme_file = generate_meme(filename, emoji)
    if not meme_file:
        return generate_random_meme_by_jpg(filename)
    return meme_file


def test():
    dit = {}
    for key, value in all_emojis_dict.items():
        if value in all_emojis_with_jpg:
            print(key, value)
            dit[key] = value
    print(dit)


if __name__ == "__main__":
    # filename = "../head.jpg"
    # print(generate_random_jpg_by_jpg(filename))
    # test()
    print(' '.join(all_emojis_dict_with_jpg_keys))
