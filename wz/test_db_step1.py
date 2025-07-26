#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

print("测试root用户连接...")
try:
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='root',
        password='760516',
        database='00077',
        charset='utf8mb4'
    )
    print('✅ ROOT连接成功')
    cursor = conn.cursor()
    
    # 检查基本信息
    cursor.execute('SELECT DATABASE()')
    db = cursor.fetchone()[0]
    print(f'当前数据库: {db}')
    
    cursor.execute('SELECT VERSION()')
    version = cursor.fetchone()[0]
    print(f'MySQL版本: {version}')
    
    # 检查表
    cursor.execute('SELECT COUNT(*) FROM pre_forum_thread')
    threads = cursor.fetchone()[0]
    print(f'主题数: {threads}')
    
    cursor.execute('SELECT COUNT(*) FROM pre_forum_post')
    posts = cursor.fetchone()[0]
    print(f'帖子数: {posts}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ ROOT连接失败: {e}')
