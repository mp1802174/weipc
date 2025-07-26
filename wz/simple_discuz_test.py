#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector

try:
    # 连接Discuz数据库
    conn = mysql.connector.connect(
        host='140.238.201.162',
        port=3306,
        user='00077',
        password='760516',
        database='00077',
        charset='utf8mb4'
    )
    
    print("✅ Discuz数据库连接成功!")
    
    cursor = conn.cursor()
    
    # 测试查询版块表
    print("\n📋 测试版块表...")
    cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
    result = cursor.fetchone()
    if result:
        fid, name, threads, posts = result
        print(f"版块ID=2: {name} (主题:{threads}, 帖子:{posts})")
    else:
        print("版块ID=2不存在")
    
    # 测试查询用户表
    print("\n👤 测试用户表...")
    cursor.execute("SELECT uid, username, posts FROM pre_common_member WHERE uid = 4")
    result = cursor.fetchone()
    if result:
        uid, username, posts = result
        print(f"用户ID=4: {username} (发帖:{posts})")
    else:
        print("用户ID=4不存在")
    
    # 测试查询主题表
    print("\n📝 测试主题表...")
    cursor.execute("SELECT COUNT(*) FROM pre_forum_thread")
    count = cursor.fetchone()[0]
    print(f"主题表记录数: {count}")
    
    # 测试查询帖子表
    print("\n💬 测试帖子表...")
    cursor.execute("SELECT COUNT(*) FROM pre_forum_post")
    count = cursor.fetchone()[0]
    print(f"帖子表记录数: {count}")
    
    conn.close()
    print("\n🎉 所有测试通过!")
    
except mysql.connector.Error as e:
    print(f"❌ 数据库错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
