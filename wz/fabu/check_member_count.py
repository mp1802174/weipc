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
    
    # 检查是否有member_count表
    print("=== 检查用户统计相关表 ===")
    cursor.execute("SHOW TABLES LIKE '%member%'")
    member_tables = cursor.fetchall()
    
    for table in member_tables:
        print(f"- {table[0]}")
    
    # 检查pre_common_member_count表
    if any('pre_common_member_count' in str(table) for table in member_tables):
        print("\n=== pre_common_member_count 表结构 ===")
        cursor.execute("DESCRIBE pre_common_member_count")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"{col[0]:25} {col[1]:30}")
        
        # 检查用户ID=4的统计信息
        print("\n=== 用户ID=4的统计信息 ===")
        cursor.execute("SELECT * FROM pre_common_member_count WHERE uid = 4")
        count_info = cursor.fetchone()
        if count_info:
            print(f"统计信息: {count_info}")
        else:
            print("用户ID=4的统计信息不存在")
    
    # 检查其他可能的统计表
    print("\n=== 检查其他统计表 ===")
    cursor.execute("SHOW TABLES LIKE '%count%'")
    count_tables = cursor.fetchall()
    
    for table in count_tables:
        print(f"- {table[0]}")
    
    conn.close()
    
except Exception as e:
    print(f"错误: {e}")
