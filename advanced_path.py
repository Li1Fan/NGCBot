"""
利用环境变量保存项目路径，方便在项目中引用
"""
import os
import sys


def setup_prj_path():
    """
    检查程序是否作为单个可执行文件运行（例如通过PyInstaller打包成一个独立的可执行文件）
    如果是单个可执行文件，获取可执行文件所在的目录，并将其设置为当前工作目录
    如果不是单个可执行文件，获取当前脚本文件所在的目录，并将其设置为当前工作目录
    """
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    # 设置环境变量
    os.environ['NGCBot_PATH'] = os.getcwd()


setup_prj_path()
PRJ_PATH = os.environ.get('NGCBot_PATH')
