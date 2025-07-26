#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

try:
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='00077',
        password='760516',
        database='00077',
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    print("=== pre_common_member 表的所有字段 ===")
    cursor.execute("DESCRIBE pre_common_member")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f"{col[0]:25} {col[1]:30} {col[2]:8} {col[3]:8}")
    
    print(f"\n总共 {len(columns)} 个字段")
    
    # 查找包含post相关的字段
    print("\n=== 包含'post'的字段 ===")
    post_fields = [col[0] for col in columns if 'post' in col[0].lower()]
    for field in post_fields:
        print(f"- {field}")
    
    # 查找包含thread相关的字段  
    print("\n=== 包含'thread'的字段 ===")
    thread_fields = [col[0] for col in columns if 'thread' in col[0].lower()]
    for field in thread_fields:
        print(f"- {field}")
    
    # 检查用户ID=4的信息
    print("\n=== 用户ID=4的信息 ===")
    cursor.execute("SELECT uid, username FROM pre_common_member WHERE uid = 4")
    user = cursor.fetchone()
    if user:
        print(f"用户ID: {user[0]}, 用户名: {user[1]}")
    else:
        print("用户ID=4不存在")
    
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
