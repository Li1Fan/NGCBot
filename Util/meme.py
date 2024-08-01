import json
import os
import random

import requests

from advanced_path import PRJ_PATH

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

all_emojis_jpg = ['hold_tight', 'addiction', 'you_should_call', 'dont_go_near', 'mourning', 'pinch', 'dinosaur',
                  'paint', 'walnut_pad', 'lim_x_0', 'rip', 'jiji_king', 'acg_entrance', 'potato', 'distracted',
                  'together', 'kaleidoscope', 'look_flat', 'anya_suki', 'perfect', 'father_work', 'cover_face',
                  'look_this_icon', 'oshi_no_ko', 'support', 'decent_kiss', 'painter', 'always', 'dont_touch',
                  'fill_head', 'loading', 'clown', 'tomb_yeah', 'name_generator', 'lost_dog', 'dog_of_vtb',
                  'frieren_take', 'read_book', 'throw', 'little_angel', 'maimai_awaken', 'trance', 'why_at_me',
                  'sit_still', 'what_I_want_to_do', 'raise_image', 'mihoyo', 'rip_angrily', 'china_flag', 'my_friend',
                  'teach', 'stew', 'anti_kidnap', 'divorce', 'this_chicken', 'think_what', 'follow', 'out', 'keep_away',
                  'prpr', 'gun', 'marriage', 'interview', 'bubble_tea', 'incivilization', 'fight_with_sunuo',
                  'what_he_wants', 'let_me_in', 'universal', 'alike', 'coupon', 'police', 'smash', 'dianzhongdian',
                  'cyan', 'genshin_start', 'blood_pressure', 'crawl', 'karyl_point', 'charpic', 'back_to_work',
                  'add_chaos', 'taunt', 'note_for_leave', 'play_game', 'symmetric', 'my_wife', 'maimai_join', 'need',
                  'overtime', 'safe_sense', 'no_response', 'learn', 'police1']


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


def generate_meme_png(filename):
    emoji = random.choice(all_emojis_jpg)
    meme_file = generate_meme(filename, emoji)
    if not meme_file:
        return generate_meme_png(filename)
    return meme_file


if __name__ == "__main__":
    filename = "../head.jpg"
    print(generate_meme_png(filename))
