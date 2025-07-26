#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
import json

def analyze_discuz_tables():
    """分析Discuz表结构"""
    
    # 连接数据库
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='00077',
        password='760516',
        database='00077',
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    # 分析主题表结构
    cursor.execute("DESCRIBE pre_forum_thread")
    thread_structure = cursor.fetchall()
    
    # 分析帖子表结构
    cursor.execute("DESCRIBE pre_forum_post")
    post_structure = cursor.fetchall()
    
    # 获取示例数据
    cursor.execute("SELECT * FROM pre_forum_thread LIMIT 1")
    thread_sample = cursor.fetchone()
    
    cursor.execute("SELECT * FROM pre_forum_post WHERE first = 1 LIMIT 1")
    post_sample = cursor.fetchone()
    
    # 获取版块信息
    cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
    forum_info = cursor.fetchone()
    
    # 获取用户信息
    cursor.execute("SELECT uid, username, posts FROM pre_common_member WHERE uid = 4")
    user_info = cursor.fetchone()
    
    conn.close()
    
    # 保存分析结果
    analysis = {
        'thread_structure': thread_structure,
        'post_structure': post_structure,
        'thread_sample': thread_sample,
        'post_sample': post_sample,
        'forum_info': forum_info,
        'user_info': user_info
    }
    
    with open('discuz_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2, default=str)
    
    return analysis

if __name__ == "__main__":
    try:
        result = analyze_discuz_tables()
        print("Analysis completed and saved to discuz_analysis.json")
    except Exception as e:
        print(f"Error: {e}")
