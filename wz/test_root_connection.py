#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import mysql.connector
import sys
import io

# 设置输出编码
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_root_connection():
    """测试root用户连接"""
    print("🔍 测试root用户连接Discuz数据库")
    print("=" * 60)
    
    # root用户连接参数
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': 'root',
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
        print("✅ root用户连接成功!")
        
        cursor = conn.cursor()
        
        # 检查数据库
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        print(f"   当前数据库: {db_name}")
        
        # 检查MySQL版本
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"   MySQL版本: {version}")
        
        # 检查关键表是否存在
        print("\n📋 检查Discuz关键表...")
        tables_to_check = [
            'pre_forum_thread', 
            'pre_forum_post', 
            'pre_forum_forum', 
            'pre_common_member'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} 条记录")
            except mysql.connector.Error as e:
                print(f"   ❌ {table}: 错误 - {e}")
        
        # 检查版块ID=2
        print("\n🎯 检查目标版块...")
        try:
            cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = 2")
            result = cursor.fetchone()
            if result:
                fid, name, threads, posts = result
                print(f"   ✅ 版块ID=2: {name} (主题:{threads}, 帖子:{posts})")
            else:
                print("   ❌ 版块ID=2: 不存在")
        except mysql.connector.Error as e:
            print(f"   ❌ 版块查询失败: {e}")
        
        # 检查用户ID=4
        print("\n👤 检查目标用户...")
        try:
            cursor.execute("SELECT uid, username, posts FROM pre_common_member WHERE uid = 4")
            result = cursor.fetchone()
            if result:
                uid, username, posts = result
                print(f"   ✅ 用户ID=4: {username} (发帖:{posts})")
            else:
                print("   ❌ 用户ID=4: 不存在")
        except mysql.connector.Error as e:
            print(f"   ❌ 用户查询失败: {e}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ root用户连接失败: {e}")
        print(f"   错误代码: {e.errno}")
        print(f"   错误信息: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def test_original_user():
    """测试原用户00077"""
    print("\n🔍 重新测试用户00077")
    print("=" * 60)
    
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': '00077',
        'password': '760516',
        'database': '00077',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        print("✅ 用户00077连接成功!")
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pre_forum_thread")
        count = cursor.fetchone()[0]
        print(f"   主题表记录数: {count}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ 用户00077连接失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 数据库连接测试")
    print("=" * 80)
    
    # 测试root连接
    root_ok = test_root_connection()
    
    # 测试原用户
    user_ok = test_original_user()
    
    print(f"\n{'='*80}")
    print("📋 测试结果:")
    print(f"   root用户: {'✅ 成功' if root_ok else '❌ 失败'}")
    print(f"   00077用户: {'✅ 成功' if user_ok else '❌ 失败'}")
    
    if root_ok:
        print("\n🎉 可以使用root用户进行后续开发!")
    elif user_ok:
        print("\n🎉 可以使用00077用户进行后续开发!")
    else:
        print("\n❌ 两个用户都无法连接，需要检查配置!")
    
    print("=" * 80)
