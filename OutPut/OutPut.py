import time

from cprint import cprint

from Util.log import log


def outPut(msg: str):
    # 获取现在的时间
    now_time = time.strftime("%Y-%m-%d %X")
    # 正常信息输出
    if '[*]' in msg:
        cprint.info(f'[{now_time}]: {msg}')
        log.debug(msg)
    # 成功信息输出
    elif '[+]' in msg:
        cprint.ok(f'[{now_time}]: {msg}')
        log.info(msg)
    elif '[-]' in msg:
        cprint.err(f'[{now_time}]: {msg}')
        log.error(msg)
    elif '[~]' in msg:
        cprint.warn(f'[{now_time}]: {msg}')
        log.warning(msg)
    else:
        cprint(f'[{now_time}]: {msg}')
        log.info(msg)
