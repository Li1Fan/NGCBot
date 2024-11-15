from cprint import cprint

from Bot_Server.Main_Server import Main_Server
from advanced_path import PRJ_PATH

Bot_Logo = """
███▄▄▄▄      ▄██████▄   ▄████████ ▀█████████▄   ▄██████▄      ███     
███▀▀▀██▄   ███    ███ ███    ███   ███    ███ ███    ███ ▀█████████▄ 
███   ███   ███    █▀  ███    █▀    ███    ███ ███    ███    ▀███▀▀██ 
███   ███  ▄███        ███         ▄███▄▄▄██▀  ███    ███     ███   ▀ 
███   ███ ▀▀███ ████▄  ███        ▀▀███▀▀▀██▄  ███    ███     ███     
███   ███   ███    ███ ███    █▄    ███    ██▄ ███    ███     ███     
███   ███   ███    ███ ███    ███   ███    ███ ███    ███     ███     
 ▀█   █▀    ████████▀  ████████▀  ▄█████████▀   ▀██████▀     ▄████▀   
                     Version: V2.0 龙年贺岁版
                     Author: NGC660安全实验室(云山/eXM)                                                 

"""

if __name__ == '__main__':
    cprint.info(Bot_Logo.strip())
    cprint.info(f'当前工作目录: {PRJ_PATH}')
    Ms = Main_Server()
