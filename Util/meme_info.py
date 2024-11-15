# 表情映射字典 Commits on Oct 22, 2024
emoji_mapping_dict = {}
api_emoji_dict = {}
api_emoji_key = list(api_emoji_dict.keys())
api_emoji_value = api_emoji_key


def create_reverse_dict(d):
    return {v: k for k, v in d.items()}


emoji_mapping_dict_reverse = create_reverse_dict(emoji_mapping_dict)

emoji_key4jpg = ['play', 'pat', 'add_chaos', 'alike', 'always', 'anti_kidnap', 'anya_suki', 'applaud', 'back_to_work',
                 'beat_head',
                 'bite', 'blood_pressure', 'bocchi_draft', 'bubble_tea', 'charpic', 'chase_train', 'china_flag',
                 'clown', 'confuse', 'coupon', 'cover_face', 'crawl', 'cyan', 'decent_kiss', 'dianzhongdian',
                 'dinosaur', 'distracted', 'divorce', 'dog_dislike', 'dog_of_vtb', 'dont_go_near', 'eat',
                 'fight_with_sunuo', 'fill_head', 'flash_blind', 'follow', 'frieren_take', 'funny_mirror', 'garbage',
                 'genshin_eat', 'genshin_start', 'guichu', 'gun', 'hammer', 'hit_screen', 'hold_tight', 'hug_leg',
                 'hutao_bite', 'interview', 'jerry_stare', 'jiji_king', 'jiujiu', 'jump', 'kaleidoscope', 'karyl_point',
                 'keep_away', 'kick_ball', 'kirby_hammer', 'klee_eat', 'knock', 'konata_watch', 'learn',
                 'left_right_jump', 'let_me_in', 'lick_candy', 'lim_x_0', 'listen_music', 'little_angel', 'loading',
                 'look_flat', 'loop', 'lost_dog', 'love_you', 'mahiro_readbook', 'maimai_awaken', 'maimai_join',
                 'marriage', 'mihoyo', 'mourning', 'my_friend', 'my_wife', 'nahida_bite', 'name_generator',
                 'no_response', 'note_for_leave', 'oshi_no_ko', 'out', 'overtime', 'paint', 'painter', 'pass_the_buck',
                 'perfect', 'petpet', 'pinch', 'pixelate', 'play_game', 'play_together', 'police',
                 'police1', 'potato', 'pound', 'printing', 'prpr', 'punch', 'pyramid', 'raise_image', 'read_book',
                 'repeat', 'rip', 'rip_angrily', 'rise_dead', 'roll', 'rotate_3d', 'run_away', 'safe_sense',
                 'scratch_head', 'shiroko_pero', 'shock', 'sit_still', 'smash', 'step_on', 'stew', 'subject3', 'suck',
                 'swirl_turn', 'symmetric', 'taunt', 'teach', 'tease', 'telescope', 'think_what', 'this_chicken',
                 'throw', 'throw_gif', 'thump', 'thump_wildly', 'tightly', 'together', 'tom_tease', 'tomb_yeah',
                 'trance', 'turn', 'twist', 'universal', 'vibrate', 'wallpaper', 'walnut_pad', 'washer', 'wave',
                 'what_I_want_to_do', 'why_at_me', 'windmill_turn', 'wooden_fish', 'worship', 'you_should_call',
                 'time_to_go', 'fade_away', 'steam_message', 'clauvio_twist', 'flush', 'thermometer_gun',
                 'google_captcha', 'ban', 'clown_mask', 'upside_down', 'behead', 'small_dinosaur', 'capoo_stew',
                 'capoo_draw', 'capoo_rip', 'capoo_rub', 'capoo_strike', 'capoo_point']
emoji_key4jpg_del = ['acg_entrance', 'father_work', 'tankuku_raisesign', 'walnut_zoom', 'what_he_wants', 'addiction',
                     'look_this_icon', 'support', 'dont_touch', 'incivilization', 'need']

# 支持图片的表情
# emoji_key4jpg = list(set(emoji_key4jpg) - set(emoji_key4jpg_del))
emoji_key4jpg = [key for key in emoji_key4jpg if key not in set(emoji_key4jpg_del)]
emoji_value4jpg = [emoji_mapping_dict.get(key, key) for key in emoji_key4jpg] + api_emoji_value
emoji_value4jpg.sort(key=lambda x: len(x), reverse=False)
# 多图表情
emoji_key_double_jpg = ["call_110", "pepe_raise", "fencing", "beat_up", "hug", "kiss", "rub"]
emoji_value_double_jpg = [emoji_mapping_dict.get(key, key) for key in emoji_key_double_jpg]
emoji_value_double_jpg.sort(key=lambda x: len(x), reverse=False)
# 非图自定义文字表情
emoji_key_custom = ["good_news", "luxun_say", "raise_sign", "nekoha_holdsign", "nokia", "capoo_say", "fanatic",
                    "hold_grudge", "imprison", "murmur", "scratchcard", 'scroll', 'psyduck']
emoji_value_custom = [emoji_mapping_dict.get(key, key) for key in emoji_key_custom]
emoji_value_custom.sort(key=lambda x: len(x), reverse=False)
# 使用的图文表情
emoji_key4jpg4txt = ['anya_suki', 'beat_head', 'coupon', 'fill_head', 'follow', 'frieren_take', 'google_captcha',
                     'interview', 'my_friend', 'repeat', 'this_chicken', 'teach', "universal",
                     'together', 'pass_the_buck', 'play_game', 'steam_message', 'thermometer_gun', 'read_book',
                     'upside_down']
emoji_value4jpg4txt = [emoji_mapping_dict.get(key, key) for key in emoji_key4jpg4txt]
emoji_value4jpg4txt.sort(key=lambda x: len(x), reverse=False)
