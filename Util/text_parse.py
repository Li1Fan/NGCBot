from datetime import datetime, timedelta


def parse_str(time_str):
    digits_mapping = {
        "零": "0",
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
        "十": ""
    }

    if time_str == "十":
        return "10"
    if time_str.startswith("十"):
        time_str = "1" + time_str[1:]
    if time_str.endswith("十"):
        time_str = time_str[:-1] + "0"

    for char in time_str:
        if char in digits_mapping:
            time_str = time_str.replace(char, digits_mapping[char])

    return time_str


def parse_chinese_time(chinese_time):
    try:
        try:
            hour_str, minute_str = chinese_time.split("点", 1)
        except ValueError:
            try:
                hour_str, minute_str = chinese_time.split("时", 1)
            except ValueError:
                try:
                    hour_str, minute_str = chinese_time.split(":", 1)
                except ValueError:
                    hour_str, minute_str = chinese_time.split(".", 1)
        if hour_str == "":
            return None
        hour = parse_str(hour_str)
        minute = parse_str(minute_str) if minute_str != "" else "0"
        minute = minute.replace("分", "")
        minute = minute.replace(".", "")
        # print(f"hour: {hour}, minute: {minute}")

        time_obj = datetime.strptime(f"{hour}:{minute}", "%H:%M")
        # print(time_obj, type(time_obj))

        return str(hour).zfill(2) + ":" + str(minute).zfill(2)

    except Exception as e:
        print(e)
        return None


def parse_chinese_date(date_str):
    try:
        if "月" in date_str:
            month_str, day_str = date_str.split("月", 1)
            month_str = month_str.replace("月", "")
            day_str = day_str.replace("日", "")
            month = parse_str(month_str)
            day = parse_str(day_str)
            # print(f"month: {month}, day: {day}")

            year = datetime.now().year
            date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            # print(date_obj, type(date_obj))
            return date_obj.strftime("%Y-%m-%d")
        if "." in date_str:
            month_str, day_str = date_str.split(".", 1)
            month = parse_str(month_str)
            day = parse_str(day_str).replace(".", "")
            # print(f"month: {month}, day: {day}")

            year = datetime.now().year
            date_obj = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d")
            # print(date_obj, type(date_obj))
            return date_obj.strftime("%Y-%m-%d")
        if date_str == "今天":
            return datetime.now().strftime("%Y-%m-%d")
        if date_str == "明天":
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        if date_str == "后天":
            return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        if date_str == "大后天":
            return (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        # 匹配N天后
        if "天后" in date_str:
            num = date_str.replace("天后", "")
            num = int(parse_str(num))
            return (datetime.now() + timedelta(days=num)).strftime("%Y-%m-%d")
    except Exception as e:
        print(e)
        return None


if __name__ == '__main__':
    # 示例输入
    chinese_time = "1:11"
    time_str = parse_chinese_time(chinese_time)
    print(time_str)  # 输出：00:11

    data_ = "三天后"
    print(parse_chinese_date(data_))
