#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

try:
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='cj',
        password='760516',
        database='cj',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # 检查总数
    cursor.execute('SELECT COUNT(*) FROM wechat_articles')
    total = cursor.fetchone()[0]
    print(f'总文章数: {total}')
    
    # 检查舞林攻略指南
    cursor.execute('SELECT COUNT(*) FROM wechat_articles WHERE account_name = %s', ('舞林攻略指南',))
    count = cursor.fetchone()[0]
    print(f'舞林攻略指南文章数: {count}')
    
    # 最新文章
    cursor.execute('SELECT title, account_name FROM wechat_articles ORDER BY id DESC LIMIT 5')
    articles = cursor.fetchall()
    print('最新5篇文章:')
    for i, (title, account) in enumerate(articles, 1):
        print(f'  {i}. {account} - {title}')
    
    conn.close()
    
except Exception as e:
    print(f'错误: {e}')
