#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
工具函数模块
提供读取认证信息、时间转换等通用功能
"""

import json
import datetime
import os
from pathlib import Path


def load_auth_info():
    """
    从data/id_info.json加载认证信息
    
    Returns:
        dict: 包含token和cookie的字典
    """
    id_info_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'data' / 'id_info.json'
    
    try:
        with open(id_info_path, 'r', encoding='utf-8') as f:
            id_info = json.load(f)
            return id_info
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"加载认证信息失败: {e}")
        return {"token": None, "cookie": None}


def load_wechat_accounts():
    """
    从data/name2fakeid.json加载公众号列表
    
    Returns:
        dict: 公众号名称到fakeid的映射字典
    """
    accounts_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'data' / 'name2fakeid.json'
    
    try:
        with open(accounts_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
            return accounts
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"加载公众号列表失败: {e}")
        return {}


def jstime_to_datetime(jstime):
    """
    将JavaScript时间戳（单位：秒）转换为datetime对象
    
    Args:
        jstime: JavaScript时间戳（单位：秒）
    
    Returns:
        datetime: datetime对象
    """
    return datetime.datetime.strptime("1970-01-01 08:00", "%Y-%m-%d %H:%M") + datetime.timedelta(minutes=jstime // 60)


def get_current_time():
    """
    获取当前时间的datetime对象
    
    Returns:
        datetime: 当前时间的datetime对象
    """
    return datetime.datetime.now()


# 常用的HTTP请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'Referer': 'https://mp.weixin.qq.com/'
} 