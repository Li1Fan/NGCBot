import os

from OutPut import OutPut
from advanced_path import PRJ_PATH


class Cache_Main_Server:
    def __init__(self, wcf):
        self.wcf = wcf
        current_path = PRJ_PATH + '/Cache'
        self.video_cache = current_path + '/Video_Cache'
        self.fish_cache = current_path + '/Fish_Cache'
        self.pic_cache = current_path + '/Pic_Cache'
        self.music_cache = current_path + '/Music_Cache'
        self.recall_pic_cache = current_path + '/Recall_Pic_Cache'
        self.head_img_cache = current_path + '/Head_Img_Cache'
        self.meme_cache = current_path + '/Meme_Cache'

    # 初始化缓存文件夹
    def init_cache(self):
        OutPut.outPut(f'[*]: 正在初始化缓存文件夹！！！')
        if not os.path.exists(self.video_cache):
            try:
                os.mkdir(self.video_cache)
                os.mkdir(self.pic_cache)
                os.mkdir(self.fish_cache)
                os.mkdir(self.music_cache)
                os.mkdir(self.recall_pic_cache)
                os.mkdir(self.head_img_cache)
                os.mkdir(self.meme_cache)
                OutPut.outPut(f'[+]: 缓存文件夹初始化成功！！！')
            except Exception as e:
                msg = '[-]: 创建文件夹出错，错误信息：{}'.format(e)
                OutPut.outPut(msg)
        else:
            OutPut.outPut(f'[~]: 缓存文件夹已创建！！！')
            return

    # 清除缓存
    def delete_file(self):
        OutPut.outPut('[*]: 缓存清除功能工作中... ...')
        if os.path.exists(self.video_cache):
            try:
                file_lists = list()
                file_lists += [self.video_cache + '/' + file for file in os.listdir(self.video_cache)]
                file_lists += [self.fish_cache + '/' + file for file in os.listdir(self.fish_cache)]
                file_lists += [self.pic_cache + '/' + file for file in os.listdir(self.pic_cache)]
                file_lists += [self.music_cache + '/' + file for file in os.listdir(self.music_cache)]
                file_lists += [self.recall_pic_cache + '/' + file for file in os.listdir(self.recall_pic_cache)]
                file_lists += [self.head_img_cache + '/' + file for file in os.listdir(self.head_img_cache)]
                file_lists += [self.meme_cache + '/' + file for file in os.listdir(self.meme_cache)]
                for rm_file in file_lists:
                    os.remove(rm_file)
            except Exception as e:
                msg = "[-]: 清除缓存时出错，错误信息：{}".format(e)
                OutPut.outPut(msg)
                return msg
            msg = "缓存文件已清除!"
            return msg
        else:
            msg = "[-]: 缓存文件夹未创建,正在创建缓存文件夹... ..."
            OutPut.outPut(msg)
            self.init_cache()
