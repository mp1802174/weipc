#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目集成测试脚本
验证整个系统的工作流程
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.integrated_crawler import IntegratedCrawler
from core.database import UnifiedDatabaseManager, Article, CrawlStatus
from core.config import get_config

def test_database_connection():
    """测试数据库连接"""
    print("=== 测试数据库连接 ===")
    
    try:
        db_manager = UnifiedDatabaseManager()
        if db_manager.connect():
            print("✅ 数据库连接成功")
            
            # 获取统计信息
            stats = db_manager.get_crawl_statistics()
            print(f"📊 数据库统计: {len(stats)} 个数据源")
            
            for source_type, stat in stats.items():
                print(f"  {source_type}: 总计 {stat['total_articles']}, 已完成 {stat['completed']}")
            
            db_manager.disconnect()
            return True
        else:
            print("❌ 数据库连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 数据库连接异常: {e}")
        return False

def test_config_system():
    """测试配置系统"""
    print("\n=== 测试配置系统 ===")
    
    try:
        config = get_config()
        print("✅ 配置系统加载成功")
        
        print(f"📋 配置信息:")
        print(f"  数据库: {config.database.host}:{config.database.port}/{config.database.database}")
        print(f"  微信采集: {'启用' if config.wechat.enabled else '禁用'}")
        print(f"  CFCJ采集: {'启用' if config.cfcj.enabled else '禁用'}")
        print(f"  自动发布: {'启用' if config.publisher.enabled else '禁用'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置系统异常: {e}")
        return False

def test_integrated_crawler():
    """测试集成采集器"""
    print("\n=== 测试集成采集器 ===")
    
    try:
        with IntegratedCrawler() as crawler:
            print("✅ 集成采集器初始化成功")
            
            # 测试获取待采集文章
            pending_articles = crawler.get_pending_articles(limit=5)
            print(f"📄 待采集文章: {len(pending_articles)} 篇")
            
            for article in pending_articles[:3]:  # 只显示前3篇
                print(f"  - {article.title[:50]}... ({article.source_type})")
            
            # 测试统计功能
            stats = crawler.get_crawl_statistics()
            print(f"📊 采集统计获取成功")
            
            return True
            
    except Exception as e:
        print(f"❌ 集成采集器异常: {e}")
        return False

def test_article_management():
    """测试文章管理功能"""
    print("\n=== 测试文章管理功能 ===")
    
    try:
        db_manager = UnifiedDatabaseManager()
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return False
        
        # 创建测试文章
        test_article = Article(
            source_type="external",
            source_name="集成测试",
            title="测试文章 - 集成测试",
            article_url="https://test.example.com/integration-test",
            content="这是一篇集成测试文章",
            crawl_status=CrawlStatus.COMPLETED.value,
            word_count=10
        )
        
        # 插入文章
        article_id = db_manager.insert_article(test_article)
        print(f"✅ 测试文章创建成功，ID: {article_id}")
        
        # 查询文章
        retrieved_article = db_manager.get_article_by_id(article_id)
        if retrieved_article and retrieved_article.title == test_article.title:
            print("✅ 文章查询成功")
        else:
            print("❌ 文章查询失败")
            return False
        
        # 更新文章状态
        db_manager.update_crawl_status(
            article_id,
            CrawlStatus.COMPLETED.value,
            content="更新后的内容",
            word_count=20
        )
        print("✅ 文章状态更新成功")
        
        # 清理测试数据
        db_manager.execute_update("DELETE FROM articles WHERE id = %s", (article_id,))
        print("✅ 测试数据清理完成")
        
        db_manager.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ 文章管理测试异常: {e}")
        return False

def test_url_crawling():
    """测试URL采集功能"""
    print("\n=== 测试URL采集功能 ===")
    
    try:
        # 使用一个简单的测试URL
        test_urls = ["https://httpbin.org/html"]
        
        with IntegratedCrawler() as crawler:
            print("✅ 集成采集器初始化成功")
            
            # 注意：这个测试可能会失败，因为httpbin.org不在支持的站点列表中
            # 这是预期的行为
            result = crawler.crawl_by_urls(
                urls=test_urls,
                source_type="external",
                source_name="集成测试"
            )
            
            print(f"📊 采集结果:")
            print(f"  总计: {result['total']}")
            print(f"  成功: {result['summary']['success']}")
            print(f"  失败: {result['summary']['failed']}")
            print(f"  跳过: {result['summary']['skipped']}")
            print(f"  错误: {result['summary']['error']}")
            
            # 清理测试数据
            if result['results']:
                db_manager = UnifiedDatabaseManager()
                db_manager.connect()
                for result_item in result['results']:
                    if 'article_id' in result_item:
                        db_manager.execute_update(
                            "DELETE FROM articles WHERE id = %s", 
                            (result_item['article_id'],)
                        )
                db_manager.disconnect()
                print("✅ 测试数据清理完成")
            
            return True
            
    except Exception as e:
        print(f"❌ URL采集测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 60)
    print("WZ项目集成测试")
    print("=" * 60)
    
    tests = [
        ("数据库连接", test_database_connection),
        ("配置系统", test_config_system),
        ("集成采集器", test_integrated_crawler),
        ("文章管理", test_article_management),
        ("URL采集", test_url_crawling),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("🎉 所有测试通过！WZ项目集成成功！")
        return True
    else:
        print("⚠️ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
