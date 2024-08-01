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
all_emojis_dict = {'youtube': 'youtube', 'yt': 'youtube', '曾小贤': 'zengxiaoxian', '压力大爷': 'yalidaye',
                   '五年怎么过的': 'wunian', '吴京xx中国xx': 'wujing', '膜拜': 'worship', '膜': 'worship',
                   '木鱼': 'wooden_fish', '许愿失败': 'wish_fail', '风车转': 'windmill_turn',
                   '为什么要有手': 'why_have_hands', '为什么@我': 'why_at_me', '最想要的东西': 'what_he_wants',
                   '我想上的': 'what_I_want_to_do', '为所欲为': 'weisuoyuwei', '波纹': 'wave', '洗衣机': 'washer',
                   '王境泽': 'wangjingze', '胡桃放大': 'walnut_zoom', '胡桃平板': 'walnut_pad', '墙纸': 'wallpaper',
                   'xx起来了': 'wakeup', '震动': 'vibrate', '万能表情': 'universal', '空白表情': 'universal',
                   '搓': 'twist', '转': 'turn', '恍惚': 'trance', '上坟': 'tomb_yeah', '坟前比耶': 'tomb_yeah',
                   '汤姆嘲笑': 'tom_tease', '一起': 'together', '紧紧贴着': 'tightly', '紧贴': 'tightly',
                   '捶爆': 'thump_wildly', '爆捶': 'thump_wildly', '捶': 'thump', '掷': 'throw_gif', '抛': 'throw_gif',
                   '丢': 'throw', '扔': 'throw', '这是鸡': 'this_chicken', '🐔': 'this_chicken', '想什么': 'think_what',
                   '望远镜': 'telescope', '戏弄': 'tease', '拿捏': 'tease', '讲课': 'teach', '敲黑板': 'teach',
                   '嘲讽': 'taunt', '唐可可举牌': 'tankuku_raisesign', '对称': 'symmetric', '回旋转': 'swirl_turn',
                   '旋风转': 'swirl_turn', '精神支柱': 'support', '吸': 'suck', '嗦': 'suck', '科目三': 'subject3',
                   '炖': 'stew', '踩': 'step_on', '砸': 'smash', '口号': 'slogan', '一巴掌': 'slap',
                   '坐得住': 'sit_still', '坐的住': 'sit_still', '别说了': 'shutup', '谁反对': 'shuifandui',
                   '震惊': 'shock', '食屎啦你': 'shishilani', '滚屏': 'scroll', '刮刮乐': 'scratchcard',
                   '挠头': 'scratch_head', '安全感': 'safe_sense', '快逃': 'run_away', '快跑': 'run', '贴贴': 'rub',
                   '贴': 'rub', '蹭蹭': 'rub', '蹭': 'rub', '三维旋转': 'rotate_3d', '滚': 'roll', '诈尸': 'rise_dead',
                   '秽土转生': 'rise_dead', '怒撕': 'rip_angrily', '撕': 'rip', '复读': 'repeat', '看书': 'read_book',
                   '举牌': 'raise_sign', '举': 'raise_image', '切格瓦拉': 'qiegewala', '打拳': 'punch',
                   '可达鸭': 'psyduck', '舔屏': 'prpr', '舔': 'prpr', 'prpr': 'prpr', '打印': 'printing', '捣': 'pound',
                   '土豆': 'potato', 'ph': 'pornhub', 'pornhub': 'pornhub', '警察': 'police1', '出警': 'police',
                   '一起玩': 'play_together', '玩游戏': 'play_game', '玩': 'play', '顶': 'play', '捏脸': 'pinch',
                   '捏': 'pinch', '摸头': 'petpet', '摸摸': 'petpet', '摸': 'petpet', 'rua': 'petpet',
                   '完美': 'perfect', '拍': 'pat', '推锅': 'pass_the_buck', '甩锅': 'pass_the_buck',
                   '小画家': 'painter', '这像画吗': 'paint', '加班': 'overtime', 'out': 'out', 'osu': 'osu',
                   '我推的网友': 'oshi_no_ko', '请假条': 'note_for_leave', '不喊我': 'not_call_me', '诺基亚': 'nokia',
                   '有内鬼': 'nokia', '无响应': 'no_response', '虹夏举牌': 'nijika_holdsign',
                   '伊地知虹夏举牌': 'nijika_holdsign', '你好骚啊': 'nihaosaoa', '猫猫举牌': 'nekoha_holdsign',
                   '猫羽雫举牌': 'nekoha_holdsign', '你可能需要': 'need', '需要': 'need', '亚名': 'name_generator',
                   '亚文化取名机': 'name_generator', '这是我老婆': 'my_wife', '我老婆': 'my_wife',
                   '我的意见是': 'my_opinion', '我的意见如下': 'my_opinion', '我朋友说': 'my_friend', '低语': 'murmur',
                   '上香': 'mourning', '米哈游': 'mihoyo', '流星': 'meteor', '结婚申请': 'marriage',
                   '结婚登记': 'marriage', '交个朋友': 'make_friend', '旅行伙伴加入': 'maimai_join',
                   '旅行伙伴觉醒': 'maimai_awaken', '麦克阿瑟说': 'maikease', '鲁迅说过': 'luxun_say',
                   '鲁迅说': 'luxun_say', '罗永浩说': 'luoyonghao_say', '永远爱你': 'love_you', '寻狗启事': 'lost_dog',
                   '循环': 'loop', '看图标': 'look_this_icon', '看扁': 'look_flat', '加载中': 'loading',
                   '小天使': 'little_angel', '听音乐': 'listen_music', '等价无穷小': 'lim_x_0', '让我进去': 'let_me_in',
                   '左右横跳': 'left_right_jump', '偷学': 'learn', '敲': 'knock', '可莉吃': 'klee_eat', '亲亲': 'kiss',
                   '亲': 'kiss', '卡比重锤': 'kirby_hammer', '卡比锤': 'kirby_hammer', '踢球': 'kick_ball',
                   '远离': 'keep_away', '凯露指': 'karyl_point', '万花镜': 'kaleidoscope', '万花筒': 'kaleidoscope',
                   '啾啾': 'jiujiu', '急急国王': 'jiji_king', '采访': 'interview', '不文明': 'incivilization',
                   '坐牢': 'imprison', '胡桃啃': 'hutao_bite', '抱大腿': 'hug_leg', '抱紧': 'hold_tight',
                   '记仇': 'hold_grudge', '打穿屏幕': 'hit_screen', '打穿': 'hit_screen', '低情商xx高情商xx': 'high_EQ',
                   '锤': 'hammer', '手枪': 'gun', '鬼畜': 'guichu', 'google': 'google', '喜报': 'good_news',
                   '原神启动': 'genshin_start', '垃圾桶': 'garbage', '垃圾': 'garbage', '哈哈镜': 'funny_mirror',
                   '芙莉莲拿': 'frieren_take', '关注': 'follow', '闪瞎': 'flash_blind', '流萤举牌': 'firefly_holdsign',
                   '整点薯条': 'find_chips', '满脑子': 'fill_head', '我打宿傩吗': 'fight_with_sunuo',
                   '我打宿傩': 'fight_with_sunuo', '🤺': 'fencing', '击剑': 'fencing', '闭嘴': 'father_work',
                   '我爸爸': 'father_work', '狂爱': 'fanatic', '狂粉': 'fanatic', '吃': 'eat', 'douyin': 'douyin',
                   '别碰': 'dont_touch', '不要靠近': 'dont_go_near', '管人痴': 'dog_of_vtb', '狗都不玩': 'dog_dislike',
                   '离婚申请': 'divorce', '离婚协议': 'divorce', '注意力涣散': 'distracted', '小恐龙': 'dinosaur',
                   '恐龙': 'dinosaur', '黑白草图': 'dianzhongdian', '典中典': 'dianzhongdian', '入典': 'dianzhongdian',
                   '像样的亲亲': 'decent_kiss', '白天晚上': 'daynight', '白天黑夜': 'daynight', '群青': 'cyan',
                   '字符画': 'charpic', '馋身子': 'chanshenzi', '奖状': 'certificate', '证书': 'certificate',
                   '舰长': 'captain', '咖波撞': 'capoo_strike', '咖波头槌': 'capoo_strike', '咖波说': 'capoo_say',
                   '咖波蹭': 'capoo_rub', '咖波贴': 'capoo_rub', '咖波撕': 'capoo_rip', '咖波画': 'capoo_draw',
                   '草神啃': 'caoshen_bite', '遇到困难请拨打': 'call_110', '奶茶': 'bubble_tea',
                   '布洛妮娅举牌': 'bronya_holdsign', '大鸭鸭举牌': 'bronya_holdsign', '波奇手稿': 'bocchi_draft',
                   '蔚蓝档案标题': 'bluearchive', 'batitle': 'bluearchive', '高血压': 'blood_pressure', '啃': 'bite',
                   '揍': 'beat_up', '拍头': 'beat_head', '悲报': 'bad_news', '打工人': 'back_to_work',
                   '继续干活': 'back_to_work', '问问': 'ask', '阿尼亚喜欢': 'anya_suki', '防诱拐': 'anti_kidnap',
                   '我永远喜欢': 'always_like', '一直': 'always', '一样': 'alike', '上瘾': 'addiction',
                   '毒瘾发作': 'addiction', '添乱': 'add_chaos', '给社会添乱': 'add_chaos',
                   '二次元入口': 'acg_entrance', '逆转裁判气泡': 'ace_attorney_dialog', '5000choyen': '5000兆'}

# 所有支持图片参数的表情选项--字典
all_emojis_dict_with_jpg = {'膜拜': 'worship', '膜': 'worship', '木鱼': 'wooden_fish', '风车转': 'windmill_turn',
                            '为什么@我': 'why_at_me', '最想要的东西': 'what_he_wants', '我想上的': 'what_I_want_to_do',
                            '波纹': 'wave', '洗衣机': 'washer', '胡桃放大': 'walnut_zoom', '胡桃平板': 'walnut_pad',
                            '墙纸': 'wallpaper', '震动': 'vibrate', '万能表情': 'universal', '空白表情': 'universal',
                            '搓': 'twist', '转': 'turn', '恍惚': 'trance', '上坟': 'tomb_yeah', '坟前比耶': 'tomb_yeah',
                            '汤姆嘲笑': 'tom_tease', '一起': 'together', '紧紧贴着': 'tightly', '紧贴': 'tightly',
                            '捶爆': 'thump_wildly', '爆捶': 'thump_wildly', '捶': 'thump', '掷': 'throw_gif',
                            '抛': 'throw_gif', '丢': 'throw', '扔': 'throw', '这是鸡': 'this_chicken',
                            '🐔': 'this_chicken', '想什么': 'think_what', '望远镜': 'telescope', '戏弄': 'tease',
                            '拿捏': 'tease', '讲课': 'teach', '敲黑板': 'teach', '嘲讽': 'taunt',
                            '唐可可举牌': 'tankuku_raisesign', '对称': 'symmetric', '回旋转': 'swirl_turn',
                            '旋风转': 'swirl_turn', '精神支柱': 'support', '吸': 'suck', '嗦': 'suck',
                            '科目三': 'subject3', '炖': 'stew', '踩': 'step_on', '砸': 'smash', '坐得住': 'sit_still',
                            '坐的住': 'sit_still', '震惊': 'shock', '挠头': 'scratch_head', '安全感': 'safe_sense',
                            '快逃': 'run_away', '三维旋转': 'rotate_3d', '滚': 'roll', '诈尸': 'rise_dead',
                            '秽土转生': 'rise_dead', '怒撕': 'rip_angrily', '撕': 'rip', '复读': 'repeat',
                            '看书': 'read_book', '举': 'raise_image', '打拳': 'punch', '舔屏': 'prpr', '舔': 'prpr',
                            'prpr': 'prpr', '打印': 'printing', '捣': 'pound', '土豆': 'potato', '警察': 'police1',
                            '出警': 'police', '一起玩': 'play_together', '玩游戏': 'play_game', '玩': 'play',
                            '顶': 'play', '捏脸': 'pinch', '捏': 'pinch', '摸头': 'petpet', '摸摸': 'petpet',
                            '摸': 'petpet', 'rua': 'petpet', '完美': 'perfect', '拍': 'pat', '推锅': 'pass_the_buck',
                            '甩锅': 'pass_the_buck', '小画家': 'painter', '这像画吗': 'paint', '加班': 'overtime',
                            'out': 'out', '我推的网友': 'oshi_no_ko', '请假条': 'note_for_leave',
                            '无响应': 'no_response', '你可能需要': 'need', '需要': 'need', '亚名': 'name_generator',
                            '亚文化取名机': 'name_generator', '这是我老婆': 'my_wife', '我老婆': 'my_wife',
                            '我朋友说': 'my_friend', '上香': 'mourning', '米哈游': 'mihoyo', '结婚申请': 'marriage',
                            '结婚登记': 'marriage', '旅行伙伴加入': 'maimai_join', '旅行伙伴觉醒': 'maimai_awaken',
                            '永远爱你': 'love_you', '寻狗启事': 'lost_dog', '循环': 'loop', '看图标': 'look_this_icon',
                            '看扁': 'look_flat', '加载中': 'loading', '小天使': 'little_angel',
                            '听音乐': 'listen_music', '等价无穷小': 'lim_x_0', '让我进去': 'let_me_in',
                            '左右横跳': 'left_right_jump', '偷学': 'learn', '敲': 'knock', '可莉吃': 'klee_eat',
                            '卡比重锤': 'kirby_hammer', '卡比锤': 'kirby_hammer', '踢球': 'kick_ball',
                            '远离': 'keep_away', '凯露指': 'karyl_point', '万花镜': 'kaleidoscope',
                            '万花筒': 'kaleidoscope', '啾啾': 'jiujiu', '急急国王': 'jiji_king', '采访': 'interview',
                            '不文明': 'incivilization', '胡桃啃': 'hutao_bite', '抱大腿': 'hug_leg',
                            '抱紧': 'hold_tight', '打穿屏幕': 'hit_screen', '打穿': 'hit_screen', '锤': 'hammer',
                            '手枪': 'gun', '鬼畜': 'guichu', '原神启动': 'genshin_start', '垃圾桶': 'garbage',
                            '垃圾': 'garbage', '哈哈镜': 'funny_mirror', '芙莉莲拿': 'frieren_take', '关注': 'follow',
                            '闪瞎': 'flash_blind', '满脑子': 'fill_head', '我打宿傩吗': 'fight_with_sunuo',
                            '我打宿傩': 'fight_with_sunuo', '闭嘴': 'father_work', '我爸爸': 'father_work', '吃': 'eat',
                            '别碰': 'dont_touch', '不要靠近': 'dont_go_near', '管人痴': 'dog_of_vtb',
                            '狗都不玩': 'dog_dislike', '离婚申请': 'divorce', '离婚协议': 'divorce',
                            '注意力涣散': 'distracted', '小恐龙': 'dinosaur', '恐龙': 'dinosaur',
                            '黑白草图': 'dianzhongdian', '典中典': 'dianzhongdian', '入典': 'dianzhongdian',
                            '像样的亲亲': 'decent_kiss', '群青': 'cyan', '字符画': 'charpic', '咖波撞': 'capoo_strike',
                            '咖波头槌': 'capoo_strike', '咖波蹭': 'capoo_rub', '咖波贴': 'capoo_rub',
                            '咖波撕': 'capoo_rip', '咖波画': 'capoo_draw', '草神啃': 'caoshen_bite',
                            '奶茶': 'bubble_tea', '波奇手稿': 'bocchi_draft', '高血压': 'blood_pressure', '啃': 'bite',
                            '拍头': 'beat_head', '打工人': 'back_to_work', '继续干活': 'back_to_work',
                            '阿尼亚喜欢': 'anya_suki', '防诱拐': 'anti_kidnap', '一直': 'always', '一样': 'alike',
                            '上瘾': 'addiction', '毒瘾发作': 'addiction', '添乱': 'add_chaos',
                            '给社会添乱': 'add_chaos', '二次元入口': 'acg_entrance'}

all_emojis_dict_with_jpg_keys = list(all_emojis_dict_with_jpg.keys())
all_emojis_dict_with_jpg_keys.reverse()


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

        # 根据 Content-Type 确定文件扩展名
        content_type = resp.headers.get('Content-Type', '')
        if 'image/gif' in content_type:
            result_filename = f"{img_dir}/{wxid}_{emoji}.gif"
        else:
            result_filename = f"{img_dir}/{wxid}_{emoji}.jpg"

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
    print(all_emojis_dict_with_jpg_keys)
