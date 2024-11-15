import hashlib


def calculate_md5(file_path):
    """计算文件的 MD5 值"""
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


if __name__ == '__main__':
    print(calculate_md5(r'D:\PyPrj\GitHub\NGCBot\Pic\none.jpg'))
