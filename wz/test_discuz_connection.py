#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Discuz数据库连接
"""

import mysql.connector
import sys

def test_discuz_connection():
    """测试Discuz数据库连接"""
    print("🔍 测试Discuz数据库连接")
    print("=" * 50)
    
    # 连接参数
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': '00077',
        'password': '760516',
        'database': '00077',
        'charset': 'utf8mb4'
    }
    
    print(f"📡 连接信息:")
    print(f"   主机: {config['host']}:{config['port']}")
    print(f"   用户: {config['user']}")
    print(f"   数据库: {config['database']}")
    
    try:
        print("\n🔗 尝试连接...")
        conn = mysql.connector.connect(**config)
        print("✅ 连接成功!")

        cursor = conn.cursor()

        # 检查数据库
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        print(f"   当前数据库: {db_name}")

        # 检查表是否存在
        print("\n📋 检查关键表...")
        tables_to_check = ['pre_forum_thread', 'pre_forum_post', 'pre_forum_forum', 'pre_common_member']

        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} 条记录")
            except mysql.connector.Error as e:
                print(f"   ❌ {table}: 不存在或无权限 - {e}")

        # 检查版块ID=2是否存在
        print("\n🎯 检查目标版块...")
        try:
            cursor.execute("SELECT name, threads, posts FROM pre_forum_forum WHERE fid = 2")
            result = cursor.fetchone()
            if result:
                name, threads, posts = result
                print(f"   ✅ 版块ID=2: {name} (主题:{threads}, 帖子:{posts})")
            else:
                print("   ❌ 版块ID=2: 不存在")
        except mysql.connector.Error as e:
            print(f"   ❌ 版块查询失败: {e}")

        # 检查用户ID=4是否存在
        print("\n👤 检查目标用户...")
        try:
            cursor.execute("SELECT username, posts FROM pre_common_member WHERE uid = 4")
            result = cursor.fetchone()
            if result:
                username, posts = result
                print(f"   ✅ 用户ID=4: {username} (发帖:{posts})")
            else:
                print("   ❌ 用户ID=4: 不存在")
        except mysql.connector.Error as e:
            print(f"   ❌ 用户查询失败: {e}")

        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ 连接失败: {e}")
        print(f"   错误代码: {e.errno}")
        print(f"   错误信息: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_wz_connection():
    """对比测试WZ数据库连接"""
    print("\n🔍 对比测试WZ数据库连接")
    print("=" * 50)
    
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': 'cj',
        'password': '760516',
        'database': 'cj',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        print("✅ WZ数据库连接成功!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM wechat_articles")
        count = cursor.fetchone()[0]
        print(f"   wechat_articles: {count} 条记录")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ WZ数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 数据库连接测试")
    print("=" * 80)
    
    # 测试Discuz连接
    discuz_ok = test_discuz_connection()
    
    # 测试WZ连接
    wz_ok = test_wz_connection()
    
    print(f"\n{'='*80}")
    print("📋 测试结果:")
    print(f"   Discuz数据库: {'✅ 成功' if discuz_ok else '❌ 失败'}")
    print(f"   WZ数据库: {'✅ 成功' if wz_ok else '❌ 失败'}")
    
    if not discuz_ok:
        print("\n💡 可能的问题:")
        print("   1. 用户名或密码错误")
        print("   2. 数据库名称错误")
        print("   3. 用户权限不足")
        print("   4. 网络连接问题")
        print("   5. MySQL服务器配置问题")
    
    print("=" * 80)
