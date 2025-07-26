#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

print("测试00077用户连接...")
try:
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='00077',
        password='760516',
        database='00077',
        charset='utf8mb4'
    )
    print('✅ 00077连接成功')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM pre_forum_thread')
    threads = cursor.fetchone()[0]
    print(f'主题数: {threads}')
    
    conn.close()
    
except Exception as e:
    print(f'❌ 00077连接失败: {e}')
