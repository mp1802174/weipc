#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试论坛发布功能
"""

import sys
import os
import logging

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fabu.forum_publisher import ForumPublisher
from fabu.batch_publisher import BatchPublisher
from fabu.discuz_client import DiscuzClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_discuz_connection():
    """测试Discuz连接"""
    print("🔍 测试Discuz数据库连接...")
    
    try:
        with DiscuzClient() as client:
            # 获取版块信息
            forum_info = client.get_forum_info(2)
            print(f"✅ 版块信息: {forum_info}")
            
            # 获取用户信息
            user_info = client.get_user_info(4)
            print(f"✅ 用户信息: {user_info}")
            
            # 获取下一个ID
            next_tid, next_pid = client.get_next_ids()
            print(f"✅ 下一个TID: {next_tid}, PID: {next_pid}")
            
        return True
        
    except Exception as e:
        print(f"❌ Discuz连接测试失败: {e}")
        return False

def test_get_pending_articles():
    """测试获取待发布文章"""
    print("\n🔍 测试获取待发布文章...")
    
    try:
        publisher = ForumPublisher()
        articles = publisher.get_pending_articles(5)
        
        print(f"✅ 找到{len(articles)}篇待发布文章:")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. ID={article['id']}, 标题={article['title'][:50]}...")
        
        return articles
        
    except Exception as e:
        print(f"❌ 获取待发布文章失败: {e}")
        return []

def test_single_publish(article_id: int):
    """测试单篇发布"""
    print(f"\n🔍 测试发布单篇文章 ID={article_id}...")
    
    try:
        publisher = ForumPublisher()
        result = publisher.publish_single_article(article_id)
        
        if result['success']:
            print(f"✅ 发布成功: {result['message']}")
        else:
            print(f"❌ 发布失败: {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ 单篇发布测试失败: {e}")
        return {'success': False, 'message': str(e)}

def test_batch_status():
    """测试批量发布状态"""
    print("\n🔍 测试批量发布状态...")
    
    try:
        batch_publisher = BatchPublisher()
        status = batch_publisher.get_publish_status()
        
        print(f"✅ 待发布文章数量: {status['pending_count']}")
        if status['pending_articles']:
            print("待发布文章列表:")
            for article in status['pending_articles']:
                print(f"  - ID={article['id']}: {article['title'][:50]}...")
        
        return status
        
    except Exception as e:
        print(f"❌ 获取批量发布状态失败: {e}")
        return {}

def progress_callback(current, total, article_info, result):
    """进度回调函数"""
    status = "✅ 成功" if result['success'] else "❌ 失败"
    print(f"[{current}/{total}] {status} - {article_info['title'][:50]}...")

def test_batch_publish_dry_run():
    """测试批量发布（仅显示会发布什么，不实际发布）"""
    print("\n🔍 批量发布预览（不实际发布）...")
    
    try:
        publisher = ForumPublisher()
        articles = publisher.get_pending_articles()
        
        if not articles:
            print("✅ 没有待发布的文章")
            return
        
        print(f"📋 将要发布{len(articles)}篇文章:")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. ID={article['id']}: {article['title']}")
            print(f"     来源: {article['account_name']}")
            print(f"     发布时间: {article['publish_timestamp']}")
            print()
        
    except Exception as e:
        print(f"❌ 批量发布预览失败: {e}")

def main():
    """主测试函数"""
    print("🧪 论坛发布功能测试")
    print("=" * 60)
    
    # 1. 测试Discuz连接
    if not test_discuz_connection():
        print("❌ Discuz连接失败，停止测试")
        return
    
    # 2. 测试获取待发布文章
    articles = test_get_pending_articles()
    if not articles:
        print("❌ 没有待发布文章，停止测试")
        return
    
    # 3. 测试批量发布状态
    test_batch_status()
    
    # 4. 批量发布预览
    test_batch_publish_dry_run()
    
    # 5. 询问是否进行实际测试
    print("\n" + "=" * 60)
    choice = input("是否要测试发布第一篇文章？(y/N): ").strip().lower()
    
    if choice == 'y':
        first_article_id = articles[0]['id']
        result = test_single_publish(first_article_id)
        
        if result['success']:
            print("\n✅ 单篇发布测试成功！")
            
            choice2 = input("是否要进行批量发布测试？(y/N): ").strip().lower()
            if choice2 == 'y':
                print("\n🚀 开始批量发布测试...")
                batch_publisher = BatchPublisher()
                batch_result = batch_publisher.publish_all(progress_callback)
                
                print(f"\n📊 批量发布结果:")
                print(f"  总计: {batch_result['total']}篇")
                print(f"  成功: {batch_result['success']}篇")
                print(f"  失败: {batch_result['failed']}篇")
                if batch_result.get('end_time'):
                    duration = batch_result['end_time'] - batch_result['start_time']
                    print(f"  耗时: {duration:.1f}秒")
        else:
            print("\n❌ 单篇发布测试失败，不进行批量测试")
    else:
        print("\n✅ 测试完成，未进行实际发布")

if __name__ == "__main__":
    main()
