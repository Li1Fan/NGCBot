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
all_emojis_dict = {'5000兆': '5000choyen', '逆转裁判气泡': 'ace_attorney_dialog', '二次元入口': 'acg_entrance',
                   '添乱': 'add_chaos', '给社会添乱': 'add_chaos', '上瘾': 'addiction', '毒瘾发作': 'addiction',
                   '一样': 'alike', '一直': 'always', '我永远喜欢': 'always_like', '防诱拐': 'anti_kidnap',
                   '阿尼亚喜欢': 'anya_suki', '鼓掌': 'applaud', '升天': 'ascension', '问问': 'ask',
                   '继续干活': 'back_to_work', '打工人': 'back_to_work', '悲报': 'bad_news', '拍头': 'beat_head',
                   '揍': 'beat_up', '啃': 'bite', '高血压': 'blood_pressure', '蔚蓝档案标题': 'bluearchive',
                   'batitle': 'bluearchive', '波奇手稿': 'bocchi_draft', '布洛妮娅举牌': 'bronya_holdsign',
                   '大鸭鸭举牌': 'bronya_holdsign', '奶茶': 'bubble_tea', '遇到困难请拨打': 'call_110',
                   '草神啃': 'caoshen_bite', '咖波画': 'capoo_draw', '咖波撕': 'capoo_rip', '咖波蹭': 'capoo_rub',
                   '咖波贴': 'capoo_rub', '咖波说': 'capoo_say', '咖波撞': 'capoo_strike', '咖波头槌': 'capoo_strike',
                   '舰长': 'captain', '奖状': 'certificate', '证书': 'certificate', '馋身子': 'chanshenzi',
                   '字符画': 'charpic', '追列车': 'chase_train', '追火车': 'chase_train', '国旗': 'china_flag',
                   '小丑': 'clown', '迷惑': 'confuse', '兑换券': 'coupon', '捂脸': 'cover_face', '爬': 'crawl',
                   '群青': 'cyan', '白天黑夜': 'daynight', '白天晚上': 'daynight', '像样的亲亲': 'decent_kiss',
                   '入典': 'dianzhongdian', '典中典': 'dianzhongdian', '黑白草图': 'dianzhongdian', '恐龙': 'dinosaur',
                   '小恐龙': 'dinosaur', '注意力涣散': 'distracted', '离婚协议': 'divorce', '离婚申请': 'divorce',
                   '狗都不玩': 'dog_dislike', '管人痴': 'dog_of_vtb', '不要靠近': 'dont_go_near', '别碰': 'dont_touch',
                   'douyin': 'douyin', '吃': 'eat', '狂爱': 'fanatic', '狂粉': 'fanatic', '闭嘴': 'father_work',
                   '我爸爸': 'father_work', '击剑': 'fencing', '🤺': 'fencing', '我打宿傩': 'fight_with_sunuo',
                   '我打宿傩吗': 'fight_with_sunuo', '满脑子': 'fill_head', '整点薯条': 'find_chips',
                   '流萤举牌': 'firefly_holdsign', '闪瞎': 'flash_blind', '关注': 'follow', '芙莉莲拿': 'frieren_take',
                   '哈哈镜': 'funny_mirror', '垃圾': 'garbage', '垃圾桶': 'garbage', '原神启动': 'genshin_start',
                   '喜报': 'good_news', 'google': 'google', '鬼畜': 'guichu', '手枪': 'gun', '锤': 'hammer',
                   '低情商xx高情商xx': 'high_EQ', '打穿': 'hit_screen', '打穿屏幕': 'hit_screen', '记仇': 'hold_grudge',
                   '抱紧': 'hold_tight', '抱大腿': 'hug_leg', '胡桃啃': 'hutao_bite', '坐牢': 'imprison',
                   '不文明': 'incivilization', '采访': 'interview', '急急国王': 'jiji_king', '啾啾': 'jiujiu',
                   '跳': 'jump', '万花筒': 'kaleidoscope', '万花镜': 'kaleidoscope', '凯露指': 'karyl_point',
                   '远离': 'keep_away', '踢球': 'kick_ball', '卡比锤': 'kirby_hammer', '卡比重锤': 'kirby_hammer',
                   '亲': 'kiss', '亲亲': 'kiss', '可莉吃': 'klee_eat', '敲': 'knock', '偷学': 'learn',
                   '左右横跳': 'left_right_jump', '让我进去': 'let_me_in', '等价无穷小': 'lim_x_0',
                   '听音乐': 'listen_music', '小天使': 'little_angel', '加载中': 'loading', '看扁': 'look_flat',
                   '看图标': 'look_this_icon', '循环': 'loop', '寻狗启事': 'lost_dog', '永远爱你': 'love_you',
                   '罗永浩说': 'luoyonghao_say', '鲁迅说': 'luxun_say', '鲁迅说过': 'luxun_say',
                   '麦克阿瑟说': 'maikease', '旅行伙伴觉醒': 'maimai_awaken', '旅行伙伴加入': 'maimai_join',
                   '交个朋友': 'make_friend', '结婚申请': 'marriage', '结婚登记': 'marriage', '流星': 'meteor',
                   '米哈游': 'mihoyo', '上香': 'mourning', '低语': 'murmur', '我朋友说': 'my_friend',
                   '我的意见如下': 'my_opinion', '我的意见是': 'my_opinion', '我老婆': 'my_wife',
                   '这是我老婆': 'my_wife', '亚文化取名机': 'name_generator', '亚名': 'name_generator', '需要': 'need',
                   '你可能需要': 'need', '猫羽雫举牌': 'nekoha_holdsign', '猫猫举牌': 'nekoha_holdsign',
                   '你好骚啊': 'nihaosaoa', '伊地知虹夏举牌': 'nijika_holdsign', '虹夏举牌': 'nijika_holdsign',
                   '无响应': 'no_response', '诺基亚': 'nokia', '有内鬼': 'nokia', '不喊我': 'not_call_me',
                   '请假条': 'note_for_leave', '我推的网友': 'oshi_no_ko', 'osu': 'osu', 'out': 'out',
                   '加班': 'overtime', '这像画吗': 'paint', '小画家': 'painter', '推锅': 'pass_the_buck',
                   '甩锅': 'pass_the_buck', '拍': 'pat', '完美': 'perfect', '摸': 'petpet', '摸摸': 'petpet',
                   '摸头': 'petpet', 'rua': 'petpet', '捏': 'pinch', '捏脸': 'pinch', '顶': 'play', '玩': 'play',
                   '玩游戏': 'play_game', '一起玩': 'play_together', '出警': 'police', '警察': 'police1',
                   'ph': 'pornhub', 'pornhub': 'pornhub', '土豆': 'potato', '捣': 'pound', '打印': 'printing',
                   '舔': 'prpr', '舔屏': 'prpr', 'prpr': 'prpr', '可达鸭': 'psyduck', '打拳': 'punch',
                   '切格瓦拉': 'qiegewala', '举': 'raise_image', '举牌': 'raise_sign', '看书': 'read_book',
                   '复读': 'repeat', '撕': 'rip', '怒撕': 'rip_angrily', '诈尸': 'rise_dead', '秽土转生': 'rise_dead',
                   '滚': 'roll', '三维旋转': 'rotate_3d', '贴': 'rub', '贴贴': 'rub', '蹭': 'rub', '蹭蹭': 'rub',
                   '快跑': 'run', '快逃': 'run_away', '安全感': 'safe_sense', '挠头': 'scratch_head',
                   '刮刮乐': 'scratchcard', '滚屏': 'scroll', '食屎啦你': 'shishilani', '震惊': 'shock',
                   '谁反对': 'shuifandui', '别说了': 'shutup', '坐得住': 'sit_still', '坐的住': 'sit_still',
                   '一巴掌': 'slap', '口号': 'slogan', '砸': 'smash', '踩': 'step_on', '炖': 'stew',
                   '科目三': 'subject3', '吸': 'suck', '嗦': 'suck', '精神支柱': 'support', '回旋转': 'swirl_turn',
                   '旋风转': 'swirl_turn', '对称': 'symmetric', '唐可可举牌': 'tankuku_raisesign', '嘲讽': 'taunt',
                   '讲课': 'teach', '敲黑板': 'teach', '拿捏': 'tease', '戏弄': 'tease', '望远镜': 'telescope',
                   '想什么': 'think_what', '这是鸡': 'this_chicken', '🐔': 'this_chicken', '丢': 'throw', '扔': 'throw',
                   '抛': 'throw_gif', '掷': 'throw_gif', '捶': 'thump', '捶爆': 'thump_wildly', '爆捶': 'thump_wildly',
                   '紧贴': 'tightly', '紧紧贴着': 'tightly', '一起': 'together', '汤姆嘲笑': 'tom_tease',
                   '上坟': 'tomb_yeah', '坟前比耶': 'tomb_yeah', '恍惚': 'trance', '转': 'turn', '搓': 'twist',
                   '万能表情': 'universal', '空白表情': 'universal', '震动': 'vibrate', 'xx起来了': 'wakeup',
                   '墙纸': 'wallpaper', '胡桃平板': 'walnut_pad', '胡桃放大': 'walnut_zoom', '王境泽': 'wangjingze',
                   '洗衣机': 'washer', '波纹': 'wave', '为所欲为': 'weisuoyuwei', '我想上的': 'what_I_want_to_do',
                   '最想要的东西': 'what_he_wants', '为什么@我': 'why_at_me', '为什么要有手': 'why_have_hands',
                   '风车转': 'windmill_turn', '许愿失败': 'wish_fail', '木鱼': 'wooden_fish', '膜': 'worship',
                   '膜拜': 'worship', '吴京xx中国xx': 'wujing', '五年怎么过的': 'wunian', '压力大爷': 'yalidaye',
                   '致电': 'you_should_call', '你应该致电': 'you_should_call', 'yt': 'youtube', 'youtube': 'youtube',
                   '曾小贤': 'zengxiaoxian'}

# 所有支持图片参数的表情选项--字典
all_emojis_dict_with_jpg = {'二次元入口': 'acg_entrance', '添乱': 'add_chaos', '给社会添乱': 'add_chaos',
                            '上瘾': 'addiction', '毒瘾发作': 'addiction', '一样': 'alike', '一直': 'always',
                            '防诱拐': 'anti_kidnap', '阿尼亚喜欢': 'anya_suki', '鼓掌': 'applaud',
                            '继续干活': 'back_to_work', '打工人': 'back_to_work', '拍头': 'beat_head', '啃': 'bite',
                            '高血压': 'blood_pressure', '波奇手稿': 'bocchi_draft', '奶茶': 'bubble_tea',
                            '草神啃': 'caoshen_bite', '咖波画': 'capoo_draw', '咖波撕': 'capoo_rip',
                            '咖波蹭': 'capoo_rub', '咖波贴': 'capoo_rub', '咖波撞': 'capoo_strike',
                            '咖波头槌': 'capoo_strike', '字符画': 'charpic', '追列车': 'chase_train',
                            '追火车': 'chase_train', '国旗': 'china_flag', '小丑': 'clown', '迷惑': 'confuse',
                            '兑换券': 'coupon', '捂脸': 'cover_face', '爬': 'crawl', '群青': 'cyan',
                            '像样的亲亲': 'decent_kiss', '入典': 'dianzhongdian', '典中典': 'dianzhongdian',
                            '黑白草图': 'dianzhongdian', '恐龙': 'dinosaur', '小恐龙': 'dinosaur',
                            '注意力涣散': 'distracted', '离婚协议': 'divorce', '离婚申请': 'divorce',
                            '狗都不玩': 'dog_dislike', '管人痴': 'dog_of_vtb', '不要靠近': 'dont_go_near',
                            '别碰': 'dont_touch', '吃': 'eat', '闭嘴': 'father_work', '我爸爸': 'father_work',
                            '我打宿傩': 'fight_with_sunuo', '我打宿傩吗': 'fight_with_sunuo', '满脑子': 'fill_head',
                            '闪瞎': 'flash_blind', '关注': 'follow', '芙莉莲拿': 'frieren_take',
                            '哈哈镜': 'funny_mirror', '垃圾': 'garbage', '垃圾桶': 'garbage',
                            '原神启动': 'genshin_start', '鬼畜': 'guichu', '手枪': 'gun', '锤': 'hammer',
                            '打穿': 'hit_screen', '打穿屏幕': 'hit_screen', '抱紧': 'hold_tight', '抱大腿': 'hug_leg',
                            '胡桃啃': 'hutao_bite', '不文明': 'incivilization', '采访': 'interview',
                            '急急国王': 'jiji_king', '啾啾': 'jiujiu', '跳': 'jump', '万花筒': 'kaleidoscope',
                            '万花镜': 'kaleidoscope', '凯露指': 'karyl_point', '远离': 'keep_away', '踢球': 'kick_ball',
                            '卡比锤': 'kirby_hammer', '卡比重锤': 'kirby_hammer', '可莉吃': 'klee_eat', '敲': 'knock',
                            '偷学': 'learn', '左右横跳': 'left_right_jump', '让我进去': 'let_me_in',
                            '等价无穷小': 'lim_x_0', '听音乐': 'listen_music', '小天使': 'little_angel',
                            '加载中': 'loading', '看扁': 'look_flat', '看图标': 'look_this_icon', '循环': 'loop',
                            '寻狗启事': 'lost_dog', '永远爱你': 'love_you', '旅行伙伴觉醒': 'maimai_awaken',
                            '旅行伙伴加入': 'maimai_join', '结婚申请': 'marriage', '结婚登记': 'marriage',
                            '米哈游': 'mihoyo', '上香': 'mourning', '我朋友说': 'my_friend', '我老婆': 'my_wife',
                            '这是我老婆': 'my_wife', '亚文化取名机': 'name_generator', '亚名': 'name_generator',
                            '需要': 'need', '你可能需要': 'need', '无响应': 'no_response', '请假条': 'note_for_leave',
                            '我推的网友': 'oshi_no_ko', 'out': 'out', '加班': 'overtime', '这像画吗': 'paint',
                            '小画家': 'painter', '推锅': 'pass_the_buck', '甩锅': 'pass_the_buck', '拍': 'pat',
                            '完美': 'perfect', '摸': 'petpet', '摸摸': 'petpet', '摸头': 'petpet', 'rua': 'petpet',
                            '捏': 'pinch', '捏脸': 'pinch', '顶': 'play', '玩': 'play', '玩游戏': 'play_game',
                            '一起玩': 'play_together', '出警': 'police', '警察': 'police1', '土豆': 'potato',
                            '捣': 'pound', '打印': 'printing', '舔': 'prpr', '舔屏': 'prpr', 'prpr': 'prpr',
                            '打拳': 'punch', '举': 'raise_image', '看书': 'read_book', '复读': 'repeat', '撕': 'rip',
                            '怒撕': 'rip_angrily', '诈尸': 'rise_dead', '秽土转生': 'rise_dead', '滚': 'roll',
                            '三维旋转': 'rotate_3d', '快逃': 'run_away', '安全感': 'safe_sense', '挠头': 'scratch_head',
                            '震惊': 'shock', '坐得住': 'sit_still', '坐的住': 'sit_still', '砸': 'smash',
                            '踩': 'step_on', '炖': 'stew', '科目三': 'subject3', '吸': 'suck', '嗦': 'suck',
                            '精神支柱': 'support', '回旋转': 'swirl_turn', '旋风转': 'swirl_turn', '对称': 'symmetric',
                            '唐可可举牌': 'tankuku_raisesign', '嘲讽': 'taunt', '讲课': 'teach', '敲黑板': 'teach',
                            '拿捏': 'tease', '戏弄': 'tease', '望远镜': 'telescope', '想什么': 'think_what',
                            '这是鸡': 'this_chicken', '🐔': 'this_chicken', '丢': 'throw', '扔': 'throw',
                            '抛': 'throw_gif', '掷': 'throw_gif', '捶': 'thump', '捶爆': 'thump_wildly',
                            '爆捶': 'thump_wildly', '紧贴': 'tightly', '紧紧贴着': 'tightly', '一起': 'together',
                            '汤姆嘲笑': 'tom_tease', '上坟': 'tomb_yeah', '坟前比耶': 'tomb_yeah', '恍惚': 'trance',
                            '转': 'turn', '搓': 'twist', '万能表情': 'universal', '空白表情': 'universal',
                            '震动': 'vibrate', '墙纸': 'wallpaper', '胡桃平板': 'walnut_pad', '胡桃放大': 'walnut_zoom',
                            '洗衣机': 'washer', '波纹': 'wave', '我想上的': 'what_I_want_to_do',
                            '最想要的东西': 'what_he_wants', '为什么@我': 'why_at_me', '风车转': 'windmill_turn',
                            '木鱼': 'wooden_fish', '膜': 'worship', '膜拜': 'worship', '致电': 'you_should_call',
                            '你应该致电': 'you_should_call'}

all_emojis_dict_with_jpg_keys = list(all_emojis_dict_with_jpg.keys())

# 以下记录图片过大的表情，超过1.3M
emojis_keys_over_size = ["波奇手稿", "迷惑", "草神啃", "复读", "木鱼", "科目三", "狗都不玩", "快逃", "胡桃放大",
                         "一起玩", "唐可可举牌", "打印", "卡比重锤", ]
emojis_values_over_size = ["bocchi_draft", "confuse", "caoshen_bite", "repeat", "wooden_fish", "subject3",
                           "dog_dislike", "run_away", "walnut_zoom", "play_together", "tankuku_raisesign",
                           "printing", "kirby_hammer"]


# all_emojis_dict_with_jpg_keys = list(set(all_emojis_dict_with_jpg_keys) - set(emojis_keys_over_size))


def generate_meme(filename, emoji, texts=None, filename2=None):
    try:
        if texts is None:
            texts = []

        files = [("images", open(filename, "rb"))]
        if filename2:
            files.append(("images", open(filename2, "rb")))
        args = {"circle": True}
        data = {"texts": texts, "args": json.dumps(args)}

        wxid = os.path.basename(filename).split(".")[0]
        if filename2:
            wxid2 = os.path.basename(filename2).split(".")[0]
            wxid = f"{wxid}_{wxid2}"

        img_dir = PRJ_PATH + '/Cache/Meme_Cache'
        os.makedirs(img_dir, exist_ok=True)

        if os.path.exists(f"{img_dir}/{wxid}_{emoji}.gif"):
            return f"{img_dir}/{wxid}_{emoji}.gif"
        if os.path.exists(f"{img_dir}/{wxid}_{emoji}.jpg"):
            return f"{img_dir}/{wxid}_{emoji}.jpg"

        url = f"http://127.0.0.1:2233/memes/{emoji}/"
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

        print(f"生成表情成功：{result_filename}")
        return result_filename

    except Exception as e:
        print(e)


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
    # filename = r"D:\PyPrj\GitHub\NGCBot\head.jpg"
    # print(generate_random_meme_by_jpg(filename))
    # test()
    # print(all_emojis_dict_with_jpg_keys)
    # print(len(all_emojis_dict_with_jpg_keys))
    print(len(all_emojis))
    print(len(all_emojis_with_jpg))
    print(len(all_emojis_dict))
    print(len(all_emojis_dict_with_jpg))
