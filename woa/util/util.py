#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @Author      : Cao Zejun
# @Time        : 2024/8/5 22:06
# @File        : util.py
# @Software    : Pycharm
# @description : 工具函数，存储一些通用的函数

from pathlib import Path
import shutil

from tqdm import tqdm
import json
import requests
from lxml import etree


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
}


# 检查文章是否正常运行(未被作者删除)
def message_is_delete(url='', response=None):
    if not response:
        response = requests.get(url=url, headers=headers).text
    tree = etree.HTML(response)
    warn = tree.xpath('//div[@class="weui-msg__title warn"]/text()')
    if len(warn) > 0 and warn[0] == '该内容已被发布者删除':
        return True
    return False

# 自检函数，更新message_info.json文件
def update_message_info():
    message_info = handle_json('message_info')
    delete_messages = handle_json('delete_message')
    delete_messages_set = set(delete_messages['is_delete'])

    try:
        for k, v in tqdm(message_info.items(), total=len(message_info)):
            for m in v['blogs']:
                if m['id'] in delete_messages_set:
                    continue
                if message_is_delete(m['link']):
                    delete_messages['is_delete'].append(m['id'])
    except:
        pass

    handle_json('message_info', message_info)

def handle_json(file_name, data=None):
    if not file_name.endswith('.json'):
        file_name = Path(__file__).parent.parent / 'data' / f'{file_name}.json'

    if not data:
        if not file_name.exists():
            return {}
        with open(file_name, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 安全写入，防止在写入过程中中断程序导致数据丢失
        with open('tmp.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        shutil.move('tmp.json', file_name)


def check_text_ratio(text):
    """检测文本中英文和符号的占比
    Args:
        text: 输入文本字符串
    Returns: 英文字符占比和符号占比
    """
    # 统计字符数
    total_chars = len(text)
    if total_chars == 0:
        return 0, 0

    # 统计英文字符
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())

    # 统计符号 (不包括空格)
    symbols = sum(1 for c in text if not c.isalnum() and not c.isspace())

    # 计算占比
    english_ratio = english_chars / total_chars
    symbol_ratio = symbols / total_chars

    return english_ratio, symbol_ratio


if __name__ == '__main__':
    update_message_info()
    # delete_messages = {
    #     'is_delete': []
    # }
    # with open('./data/delete_message.json', 'w', encoding='utf-8') as f:
    #     json.dump(delete_messages, f, indent=4, ensure_ascii=False)