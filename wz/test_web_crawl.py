#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web界面的微信抓取功能
模拟Web界面调用，找出问题所在
"""

import sys
import os
import subprocess
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_crawl_wechat_script():
    """测试 crawl_wechat.py 脚本"""
    print("🧪 测试 crawl_wechat.py 脚本")
    print("=" * 60)
    
    # 准备命令
    script_path = os.path.join(os.path.dirname(__file__), 'crawl_wechat.py')
    cmd = [sys.executable, script_path, '--account', '舞林攻略指南', '--limit', '5']
    
    print(f"📝 执行命令: {' '.join(cmd)}")
    
    try:
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            encoding='utf-8'
        )
        
        print(f"📊 返回码: {result.returncode}")
        print(f"📤 标准输出:")
        if result.stdout:
            print(result.stdout)
        else:
            print("   (无输出)")
        
        print(f"❌ 错误输出:")
        if result.stderr:
            print(result.stderr)
        else:
            print("   (无错误)")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def test_direct_wzzq_main():
    """直接测试 wzzq.main 模块"""
    print("\n🧪 直接测试 wzzq.main 模块")
    print("=" * 60)
    
    try:
        # 模拟命令行参数
        original_argv = sys.argv
        sys.argv = ['main.py', '--account', '舞林攻略指南', '--limit', '5']
        
        # 导入并执行
        from wzzq.main import main
        
        print("📝 调用 wzzq.main.main()")
        exit_code = main()
        
        print(f"📊 返回码: {exit_code}")
        
        # 恢复原始参数
        sys.argv = original_argv
        
        return exit_code == 0
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        # 恢复原始参数
        sys.argv = original_argv
        return False

def check_database_after_test():
    """测试后检查数据库"""
    print("\n📊 检查测试后的数据库状态")
    print("=" * 60)
    
    try:
        import mysql.connector
        
        conn = mysql.connector.connect(
            host='140.238.201.162',
            port=3306,
            user='cj',
            password='760516',
            database='cj',
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 检查总文章数
        cursor.execute("SELECT COUNT(*) FROM wechat_articles")
        total_count = cursor.fetchone()[0]
        print(f"📝 数据库总文章数: {total_count}")
        
        # 检查舞林攻略指南的文章
        cursor.execute(
            "SELECT COUNT(*) FROM wechat_articles WHERE account_name = %s",
            ('舞林攻略指南',)
        )
        account_count = cursor.fetchone()[0]
        print(f"📱 舞林攻略指南文章数: {account_count}")
        
        # 检查最新的文章
        cursor.execute("""
            SELECT title, account_name, crawled_at 
            FROM wechat_articles 
            ORDER BY crawled_at DESC 
            LIMIT 3
        """)
        
        recent_articles = cursor.fetchall()
        if recent_articles:
            print(f"📄 最新的文章:")
            for title, account, crawled in recent_articles:
                print(f"   🕒 {crawled} | {account} | {title[:50]}...")
        else:
            print("   ⚠️  没有找到任何文章")
        
        conn.close()
        return total_count, account_count
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return 0, 0

def test_database_connection():
    """测试数据库连接"""
    print("\n🔗 测试数据库连接")
    print("=" * 60)
    
    try:
        from wzzq.db import DatabaseManager
        
        print("📝 创建 DatabaseManager 实例")
        with DatabaseManager() as db:
            if db.conn:
                print("✅ 数据库连接成功")
                
                # 测试表结构
                cursor = db.conn.cursor()
                cursor.execute("DESCRIBE wechat_articles")
                columns = cursor.fetchall()
                
                print(f"📊 wechat_articles 表字段:")
                for col in columns:
                    print(f"   {col[0]} - {col[1]}")
                
                return True
            else:
                print("❌ 数据库连接失败")
                return False
                
    except Exception as e:
        print(f"❌ 数据库连接测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🔧 Web界面微信抓取功能测试")
    print("=" * 80)
    
    # 1. 测试数据库连接
    db_ok = test_database_connection()
    
    # 2. 检查测试前的数据库状态
    print("\n📊 测试前数据库状态")
    print("=" * 60)
    before_total, before_account = check_database_after_test()
    
    if not db_ok:
        print("\n❌ 数据库连接失败，无法继续测试")
        return
    
    # 3. 测试脚本调用
    script_ok = test_crawl_wechat_script()
    
    # 4. 测试直接调用
    direct_ok = test_direct_wzzq_main()
    
    # 5. 检查测试后的数据库状态
    after_total, after_account = check_database_after_test()
    
    # 6. 总结
    print(f"\n{'='*80}")
    print("📋 测试总结:")
    print(f"   🔗 数据库连接: {'✅ 成功' if db_ok else '❌ 失败'}")
    print(f"   📜 脚本调用: {'✅ 成功' if script_ok else '❌ 失败'}")
    print(f"   🔧 直接调用: {'✅ 成功' if direct_ok else '❌ 失败'}")
    print(f"   📊 数据变化: {before_total} → {after_total} (总数)")
    print(f"   📱 账号文章: {before_account} → {after_account} (舞林攻略指南)")
    
    if after_total > before_total:
        print("🎉 测试成功！文章已保存到数据库")
    elif script_ok or direct_ok:
        print("⚠️  抓取成功但文章未保存到数据库，可能的原因:")
        print("   1. 文章已存在，被跳过了")
        print("   2. 保存逻辑有问题")
        print("   3. 数据库写入权限问题")
    else:
        print("❌ 抓取失败，请检查:")
        print("   1. 微信认证信息是否有效")
        print("   2. 网络连接是否正常")
        print("   3. 公众号配置是否正确")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
