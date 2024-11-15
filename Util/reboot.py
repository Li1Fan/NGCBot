import json
import os
import subprocess
import time

import psutil

# 读取配置
with open('reboot.json') as config_file:
    config = json.load(config_file)

open_program = config['open_program']
close_program = config['close_program']
command = config['command']
print("open_program:", open_program)
print("close_program:", close_program)
print("command:", command)
print(50 * "-")


def close_powershell():
    # 遍历所有正在运行的进程
    for process in psutil.process_iter(attrs=['pid', 'name']):
        try:
            # 查找 PowerShell 进程
            if process.info['name'] in close_program:
                print(f'Closing PowerShell with PID: {process.info["pid"]}')
                # 关闭 PowerShell 进程
                os.kill(process.info['pid'], 9)  # 9 是 SIGKILL 的信号
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue


def open_powershell():
    # 打开 PowerShell 并执行命令
    # 在新窗口中运行 xx.exe
    # os.system(f'start {open_program} -NoExit -Command "{command}"')
    subprocess.run(f'start {open_program} -NoExit -Command "{command}"', shell=True)


def reboot_powershell():
    close_powershell()
    time.sleep(10)
    open_powershell()


if __name__ == '__main__':
    reboot_powershell()
    # 打包命令  pyinstaller -w .\reboot.py --icon reboot.png
