#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

# Discuz数据库连接
discuz_conn = mysql.connector.connect(
    host='140.238.201.162',
    port=3306,
    user='00077',
    password='760516',
    database='00077',
    charset='utf8mb4'
)

cursor = discuz_conn.cursor()

print("=== pre_forum_thread 表结构 ===")
cursor.execute("DESCRIBE pre_forum_thread")
for row in cursor.fetchall():
    print(f"{row[0]:20} {row[1]:30}")

print("\n=== pre_forum_post 表结构 ===")
cursor.execute("DESCRIBE pre_forum_post")
for row in cursor.fetchall():
    print(f"{row[0]:20} {row[1]:30}")

print("\n=== 当前最大ID ===")
cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
max_tid = cursor.fetchone()[0] or 0
print(f"最大TID: {max_tid}")

cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
max_pid = cursor.fetchone()[0] or 0
print(f"最大PID: {max_pid}")

print("\n=== 目标版块信息 ===")
cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
forum_info = cursor.fetchone()
if forum_info:
    print(f"版块ID: {forum_info[0]}, 名称: {forum_info[1]}, 主题数: {forum_info[2]}, 帖子数: {forum_info[3]}")

print("\n=== 目标用户信息 ===")
cursor.execute("SELECT uid, username FROM pre_common_member WHERE uid = 4")
user_info = cursor.fetchone()
if user_info:
    print(f"用户ID: {user_info[0]}, 用户名: {user_info[1]}")

discuz_conn.close()

# WZ数据库连接
print("\n=== WZ数据库检查 ===")
wz_conn = mysql.connector.connect(
    host='140.238.201.162',
    port=3306,
    user='cj',
    password='760516',
    database='cj',
    charset='utf8mb4'
)

cursor = wz_conn.cursor()

# 检查forum_published字段
cursor.execute("SHOW COLUMNS FROM wechat_articles LIKE 'forum_published'")
result = cursor.fetchone()
if result:
    print("✅ forum_published字段已存在")
else:
    print("❌ forum_published字段不存在")

# 统计文章数量
cursor.execute("SELECT COUNT(*) FROM wechat_articles")
total_articles = cursor.fetchone()[0]
print(f"总文章数: {total_articles}")

wz_conn.close()
print("分析完成！")
