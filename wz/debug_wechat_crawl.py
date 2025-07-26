#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试微信公众号抓取问题
检查配置、数据库状态和抓取结果
"""

import sys
import os
import json
import logging
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import mysql.connector

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接"""
    db_config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': 'cj',
        'password': '760516',
        'database': 'cj',
        'charset': 'utf8mb4'
    }
    return mysql.connector.connect(**db_config)

def check_account_config():
    """检查公众号配置"""
    print("🔧 检查公众号配置")
    print("=" * 60)
    
    accounts = {
        "舞林攻略指南": "Mzg4MDcwNTQxMw==",
        "人类砂舞行为研究": "MzkwNjY0ODI2MQ==",
        "砂砂之家": "MzkyMjUxOTI5Mg=="
    }
    
    print(f"✅ 配置的公众号数量: {len(accounts)}")
    for name, biz in accounts.items():
        print(f"   📱 {name}: {biz}")
    
    return accounts

def check_database_articles(accounts):
    """检查数据库中的文章情况"""
    print("\n📊 检查数据库中的文章情况")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查总文章数
        cursor.execute("SELECT COUNT(*) FROM wechat_articles")
        total_count = cursor.fetchone()[0]
        print(f"📝 数据库总文章数: {total_count}")
        
        # 检查每个公众号的文章数
        for account_name in accounts.keys():
            cursor.execute(
                "SELECT COUNT(*) FROM wechat_articles WHERE account_name = %s",
                (account_name,)
            )
            count = cursor.fetchone()[0]
            print(f"   📱 {account_name}: {count} 篇文章")
        
        # 检查最近的文章
        print(f"\n📅 最近的文章:")
        cursor.execute("""
            SELECT account_name, title, article_url, crawled_at
            FROM wechat_articles
            ORDER BY crawled_at DESC
            LIMIT 10
        """)

        recent_articles = cursor.fetchall()
        if recent_articles:
            for article in recent_articles:
                account, title, url, crawled = article
                print(f"   🕒 {crawled} | {account} | {title[:50]}...")
        else:
            print("   ⚠️  没有找到任何文章")

        # 检查今天的文章
        today = datetime.now().date()
        cursor.execute("""
            SELECT account_name, COUNT(*)
            FROM wechat_articles
            WHERE DATE(crawled_at) = %s
            GROUP BY account_name
        """, (today,))

        today_articles = cursor.fetchall()
        print(f"\n📅 今天 ({today}) 的新文章:")
        if today_articles:
            for account, count in today_articles:
                print(f"   📱 {account}: {count} 篇")
        else:
            print("   ⚠️  今天没有新文章")
        
        return total_count, recent_articles, today_articles
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {e}")
        return 0, [], []
    finally:
        if 'conn' in locals():
            conn.close()

def check_crawl_status():
    """检查抓取状态"""
    print("\n🔍 检查抓取状态")
    print("=" * 60)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查抓取状态分布
        cursor.execute("""
            SELECT crawl_status, COUNT(*) 
            FROM wechat_articles 
            GROUP BY crawl_status
        """)
        
        status_counts = cursor.fetchall()
        print("📊 抓取状态分布:")
        status_names = {0: "待采集", 1: "已采集", 2: "采集失败"}
        for status, count in status_counts:
            status_name = status_names.get(status, f"未知({status})")
            print(f"   {status_name}: {count} 篇")
        
        # 检查最近的抓取记录
        cursor.execute("""
            SELECT article_url, crawl_status, title, account_name, crawled_at
            FROM wechat_articles
            WHERE crawled_at >= %s
            ORDER BY crawled_at DESC
            LIMIT 5
        """, (datetime.now() - timedelta(hours=24),))

        recent_crawls = cursor.fetchall()
        print(f"\n🕒 最近24小时的抓取记录:")
        if recent_crawls:
            for url, status, title, account, crawled in recent_crawls:
                status_name = status_names.get(status, f"未知({status})")
                print(f"   {crawled} | {status_name} | {account} | {title[:30]}...")
        else:
            print("   ⚠️  最近24小时没有抓取记录")
        
    except Exception as e:
        print(f"❌ 抓取状态检查失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def test_wechat_api():
    """测试微信API抓取"""
    print("\n🧪 测试微信API抓取")
    print("=" * 60)
    
    try:
        # 导入微信抓取模块
        from wzzq.wechat_crawler import WechatCrawler
        
        accounts = {
            "舞林攻略指南": "Mzg4MDcwNTQxMw==",
            "人类砂舞行为研究": "MzkwNjY0ODI2MQ==",
            "砂砂之家": "MzkyMjUxOTI5Mg=="
        }
        
        crawler = WechatCrawler()
        
        # 测试第一个公众号
        test_account = "舞林攻略指南"
        test_biz = accounts[test_account]

        print(f"🔍 测试抓取公众号: {test_account}")
        print(f"📱 Biz参数: {test_biz}")

        # 执行抓取测试
        result = crawler.get_articles(test_account, limit=10)
        
        if result and len(result) > 0:
            print(f"✅ 抓取成功!")
            print(f"📝 获取到文章数: {len(result)}")

            if result:
                print(f"📄 文章列表:")
                for i, article in enumerate(result[:5], 1):  # 只显示前5篇
                    title = article.get('title', '无标题')
                    url = article.get('link', '无链接')
                    create_time = article.get('create_time', '无时间')
                    print(f"   {i}. {title}")
                    print(f"      🔗 {url}")
                    print(f"      🕒 {create_time}")
            else:
                print("⚠️  虽然抓取成功，但没有获取到文章")
                print("💡 可能原因:")
                print("   1. 该公众号最近没有发布新文章")
                print("   2. 所有文章都已经在数据库中")
                print("   3. 微信API返回了空结果")
        else:
            print(f"❌ 抓取失败或无结果")
            print(f"   返回结果: {result}")
            
    except ImportError as e:
        print(f"❌ 无法导入微信抓取模块: {e}")
        print("💡 请检查 wzzq/wechat_crawler.py 是否存在")
    except Exception as e:
        print(f"❌ 测试抓取失败: {e}")

def check_recent_wechat_posts():
    """检查是否有最近的微信文章可以抓取"""
    print("\n🔍 检查微信公众号最近发布情况")
    print("=" * 60)
    
    print("💡 建议手动检查:")
    print("1. 打开微信，搜索这些公众号")
    print("2. 查看它们最近是否有发布新文章")
    print("3. 确认文章发布时间")
    
    accounts = {
        "舞林攻略指南": "Mzg4MDcwNTQxMw==",
        "人类砂舞行为研究": "MzkwNjY0ODI2MQ==",
        "砂砂之家": "MzkyMjUxOTI5Mg=="
    }
    
    for account_name in accounts.keys():
        print(f"📱 {account_name}")
        print(f"   微信搜索: {account_name}")

def main():
    """主诊断函数"""
    print("🔧 微信公众号抓取问题诊断")
    print("=" * 80)
    
    # 1. 检查配置
    accounts = check_account_config()
    
    # 2. 检查数据库
    total_count, recent_articles, today_articles = check_database_articles(accounts)
    
    # 3. 检查抓取状态
    check_crawl_status()
    
    # 4. 测试API抓取
    test_wechat_api()
    
    # 5. 检查微信发布情况
    check_recent_wechat_posts()
    
    # 总结
    print(f"\n{'='*80}")
    print("📋 诊断总结:")
    print(f"   📊 数据库总文章数: {total_count}")
    print(f"   📅 今天新文章数: {len(today_articles)}")
    print(f"   🔧 配置公众号数: {len(accounts)}")
    
    if total_count == 0:
        print("\n💡 建议:")
        print("   1. 检查微信抓取模块是否正常工作")
        print("   2. 检查网络连接和代理设置")
        print("   3. 确认公众号Biz参数是否正确")
    elif len(today_articles) == 0:
        print("\n💡 可能原因:")
        print("   1. 这些公众号今天确实没有发布新文章")
        print("   2. 文章已经被抓取过了")
        print("   3. 抓取时间设置问题")
    
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
