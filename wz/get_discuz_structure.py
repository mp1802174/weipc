#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
import json

def get_discuz_structure():
    """获取Discuz表结构和示例数据"""
    
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
    
    result = {}
    
    # 获取主题表结构
    cursor.execute("DESCRIBE pre_forum_thread")
    result['thread_structure'] = []
    for row in cursor.fetchall():
        result['thread_structure'].append({
            'field': row[0],
            'type': row[1],
            'null': row[2],
            'key': row[3],
            'default': row[4],
            'extra': row[5]
        })
    
    # 获取帖子表结构
    cursor.execute("DESCRIBE pre_forum_post")
    result['post_structure'] = []
    for row in cursor.fetchall():
        result['post_structure'].append({
            'field': row[0],
            'type': row[1],
            'null': row[2],
            'key': row[3],
            'default': row[4],
            'extra': row[5]
        })
    
    # 获取版块信息
    cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
    forum_result = cursor.fetchone()
    if forum_result:
        result['target_forum'] = {
            'fid': forum_result[0],
            'name': forum_result[1],
            'threads': forum_result[2],
            'posts': forum_result[3]
        }
    
    # 获取用户信息
    cursor.execute("SELECT uid, username, posts FROM pre_common_member WHERE uid = 4")
    user_result = cursor.fetchone()
    if user_result:
        result['target_user'] = {
            'uid': user_result[0],
            'username': user_result[1],
            'posts': user_result[2]
        }
    
    # 获取主题表示例
    cursor.execute("SELECT tid, fid, subject, author, authorid, dateline, replies, views FROM pre_forum_thread LIMIT 2")
    result['thread_samples'] = []
    for row in cursor.fetchall():
        result['thread_samples'].append({
            'tid': row[0],
            'fid': row[1],
            'subject': row[2],
            'author': row[3],
            'authorid': row[4],
            'dateline': row[5],
            'replies': row[6],
            'views': row[7]
        })
    
    # 获取帖子表示例
    cursor.execute("SELECT pid, tid, first, subject, author, authorid, dateline, message FROM pre_forum_post WHERE first = 1 LIMIT 2")
    result['post_samples'] = []
    for row in cursor.fetchall():
        result['post_samples'].append({
            'pid': row[0],
            'tid': row[1],
            'first': row[2],
            'subject': row[3],
            'author': row[4],
            'authorid': row[5],
            'dateline': row[6],
            'message': row[7][:100] if row[7] else None  # 只取前100字符
        })
    
    # 获取当前最大ID
    cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
    max_tid = cursor.fetchone()[0]
    result['max_tid'] = max_tid or 0
    
    cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
    max_pid = cursor.fetchone()[0]
    result['max_pid'] = max_pid or 0
    
    conn.close()
    
    # 保存到文件
    with open('discuz_structure.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    
    return result

if __name__ == "__main__":
    try:
        result = get_discuz_structure()
        print("SUCCESS: Discuz structure saved to discuz_structure.json")
        print(f"Thread table fields: {len(result['thread_structure'])}")
        print(f"Post table fields: {len(result['post_structure'])}")
        print(f"Max TID: {result['max_tid']}")
        print(f"Max PID: {result['max_pid']}")
        if 'target_forum' in result:
            print(f"Target forum: {result['target_forum']['name']}")
        if 'target_user' in result:
            print(f"Target user: {result['target_user']['username']}")
    except Exception as e:
        print(f"ERROR: {e}")
