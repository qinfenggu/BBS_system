import random


# 随机生成num位由数字与大小英文字母组成验证码
def get_random_captcha(num):
    checkcode = ''
    for i in range(num):  # 循环4次
        index = random.randrange(0, 3)  # 生成0-3中的一个数
        if index != i and index + 1 != i:
            checkcode += chr(random.randint(97, 122))  # 生成a-z中的一个小写字母
        elif index + 1 == i:
            checkcode += chr(random.randint(65, 90))  # 生成A-Z中的大写字母
        else:
            checkcode += str(random.randint(1, 9))  # 生成1-9的一个数字
    return checkcode


# 随机生成num为纯数字验证码
def get_random_note_captcha(num):
    checkcode = ''
    for i in range(num):  # 循环4次
            checkcode += str(random.randint(1, 9))  # 生成1-9的一个数字
    return checkcode




