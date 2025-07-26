#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试数据库连接和表结构
"""

import mysql.connector

def test_connections():
    """测试两个数据库连接"""
    print("Testing database connections...")
    
    # 测试WZ数据库
    print("\n=== WZ Database (cj) ===")
    try:
        wz_conn = mysql.connector.connect(
            host='140.238.201.162',
            port=3306,
            user='cj',
            password='760516',
            database='cj',
            charset='utf8mb4'
        )
        cursor = wz_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wechat_articles")
        count = cursor.fetchone()[0]
        print(f"✅ WZ连接成功，wechat_articles有{count}条记录")
        
        # 检查是否有forum_published字段
        cursor.execute("SHOW COLUMNS FROM wechat_articles LIKE 'forum_published'")
        result = cursor.fetchone()
        if result:
            print("✅ forum_published字段已存在")
        else:
            print("❌ forum_published字段不存在，需要添加")
        
        wz_conn.close()
    except Exception as e:
        print(f"❌ WZ数据库连接失败: {e}")
    
    # 测试Discuz数据库
    print("\n=== Discuz Database (00077) ===")
    try:
        discuz_conn = mysql.connector.connect(
            host='140.238.201.162',
            port=3306,
            user='00077',
            password='760516',
            database='00077',
            charset='utf8mb4'
        )
        cursor = discuz_conn.cursor()
        
        # 检查关键表
        tables = ['pre_forum_thread', 'pre_forum_post', 'pre_forum_forum', 'pre_common_member']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count}条记录")
        
        # 检查目标版块和用户
        cursor.execute("SELECT name FROM pre_forum_forum WHERE fid = 2")
        forum = cursor.fetchone()
        if forum:
            print(f"✅ 目标版块(FID=2): {forum[0]}")
        else:
            print("❌ 版块FID=2不存在")
            
        cursor.execute("SELECT username FROM pre_common_member WHERE uid = 4")
        user = cursor.fetchone()
        if user:
            print(f"✅ 目标用户(UID=4): {user[0]}")
        else:
            print("❌ 用户UID=4不存在")
        
        # 获取当前最大ID
        cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
        max_tid = cursor.fetchone()[0] or 0
        cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
        max_pid = cursor.fetchone()[0] or 0
        print(f"📊 当前最大TID: {max_tid}, 最大PID: {max_pid}")
        
        discuz_conn.close()
    except Exception as e:
        print(f"❌ Discuz数据库连接失败: {e}")

if __name__ == "__main__":
    test_connections()
