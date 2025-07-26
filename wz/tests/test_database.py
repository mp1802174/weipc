#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一数据库管理器测试
"""

import unittest
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import UnifiedDatabaseManager, Article, PublishTask, SourceType, CrawlStatus, PublishStatus
from core.config import UnifiedConfig

class TestUnifiedDatabaseManager(unittest.TestCase):
    """统一数据库管理器测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 创建测试配置
        cls.config = UnifiedConfig()
        cls.config.database.database = "cj_test"  # 使用测试数据库
        
        # 创建数据库管理器
        cls.db_manager = UnifiedDatabaseManager(cls.config)
        
        # 连接数据库
        if not cls.db_manager.connect():
            raise Exception("无法连接到测试数据库")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.db_manager.disconnect()
    
    def setUp(self):
        """每个测试方法前的初始化"""
        # 清理测试数据
        self._cleanup_test_data()
    
    def tearDown(self):
        """每个测试方法后的清理"""
        # 清理测试数据
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """清理测试数据"""
        try:
            self.db_manager.execute_update("DELETE FROM publish_tasks WHERE article_id IN (SELECT id FROM articles WHERE title LIKE 'TEST_%')")
            self.db_manager.execute_update("DELETE FROM articles WHERE title LIKE 'TEST_%'")
        except:
            pass
    
    def test_article_crud_operations(self):
        """测试文章CRUD操作"""
        # 创建测试文章
        article = Article(
            source_type=SourceType.WECHAT.value,
            source_name="测试公众号",
            title="TEST_文章标题",
            article_url="https://test.example.com/article/123",
            content="这是测试内容",
            word_count=100,
            crawl_status=CrawlStatus.COMPLETED.value
        )
        
        # 测试插入
        article_id = self.db_manager.insert_article(article)
        self.assertIsNotNone(article_id)
        self.assertGreater(article_id, 0)
        
        # 测试根据ID查询
        retrieved_article = self.db_manager.get_article_by_id(article_id)
        self.assertIsNotNone(retrieved_article)
        self.assertEqual(retrieved_article.title, article.title)
        self.assertEqual(retrieved_article.source_name, article.source_name)
        
        # 测试根据URL查询
        url_article = self.db_manager.get_article_by_url(SourceType.WECHAT.value, article.article_url)
        self.assertIsNotNone(url_article)
        self.assertEqual(url_article.id, article_id)
        
        # 测试更新
        retrieved_article.content = "更新后的内容"
        retrieved_article.word_count = 200
        update_result = self.db_manager.update_article(retrieved_article)
        self.assertGreater(update_result, 0)
        
        # 验证更新结果
        updated_article = self.db_manager.get_article_by_id(article_id)
        self.assertEqual(updated_article.content, "更新后的内容")
        self.assertEqual(updated_article.word_count, 200)
    
    def test_crawl_status_management(self):
        """测试采集状态管理"""
        # 创建待采集文章
        article = Article(
            source_type=SourceType.LINUX_DO.value,
            source_name="Linux.do",
            title="TEST_待采集文章",
            article_url="https://linux.do/test/456",
            crawl_status=CrawlStatus.PENDING.value
        )
        
        article_id = self.db_manager.insert_article(article)
        
        # 测试获取待采集文章
        pending_articles = self.db_manager.get_pending_articles()
        self.assertGreater(len(pending_articles), 0)
        
        found_article = None
        for a in pending_articles:
            if a.id == article_id:
                found_article = a
                break
        
        self.assertIsNotNone(found_article)
        self.assertEqual(found_article.crawl_status, CrawlStatus.PENDING.value)
        
        # 测试更新采集状态
        test_content = "采集到的内容"
        test_images = [{"url": "https://example.com/image.jpg", "alt": "测试图片"}]
        
        update_result = self.db_manager.update_crawl_status(
            article_id,
            CrawlStatus.COMPLETED.value,
            content=test_content,
            content_html=f"<p>{test_content}</p>",
            word_count=50,
            images=test_images
        )
        
        self.assertGreater(update_result, 0)
        
        # 验证状态更新
        updated_article = self.db_manager.get_article_by_id(article_id)
        self.assertEqual(updated_article.crawl_status, CrawlStatus.COMPLETED.value)
        self.assertEqual(updated_article.content, test_content)
        self.assertEqual(updated_article.word_count, 50)
        self.assertIsNotNone(updated_article.images)
        self.assertEqual(len(updated_article.images), 1)
        self.assertIsNotNone(updated_article.crawled_at)
    
    def test_publish_task_management(self):
        """测试发布任务管理"""
        # 先创建一篇文章
        article = Article(
            source_type=SourceType.WECHAT.value,
            source_name="测试公众号",
            title="TEST_发布测试文章",
            article_url="https://test.example.com/publish/789",
            content="待发布的内容",
            crawl_status=CrawlStatus.COMPLETED.value
        )
        
        article_id = self.db_manager.insert_article(article)
        
        # 创建发布任务
        publish_task = PublishTask(
            article_id=article_id,
            target_platform="8wf_net",
            target_forum_id="1",
            status=PublishStatus.PENDING.value,
            priority=5,
            custom_title="自定义标题"
        )
        
        task_id = self.db_manager.create_publish_task(publish_task)
        self.assertIsNotNone(task_id)
        self.assertGreater(task_id, 0)
        
        # 测试获取待处理任务
        pending_tasks = self.db_manager.get_pending_publish_tasks()
        self.assertGreater(len(pending_tasks), 0)
        
        found_task = None
        for task in pending_tasks:
            if task.id == task_id:
                found_task = task
                break
        
        self.assertIsNotNone(found_task)
        self.assertEqual(found_task.article_id, article_id)
        self.assertEqual(found_task.target_platform, "8wf_net")
        
        # 测试更新任务状态
        update_result = self.db_manager.update_publish_task_status(
            task_id,
            PublishStatus.COMPLETED.value,
            published_url="https://8wf.net/thread/123",
            published_id="123"
        )
        
        self.assertGreater(update_result, 0)
        
        # 验证任务状态更新
        updated_tasks = self.db_manager.get_pending_publish_tasks()
        task_still_pending = any(task.id == task_id for task in updated_tasks)
        self.assertFalse(task_still_pending)  # 已完成的任务不应该在待处理列表中
    
    def test_publish_status_management(self):
        """测试发布状态管理"""
        # 创建文章
        article = Article(
            source_type=SourceType.WECHAT.value,
            source_name="测试公众号",
            title="TEST_发布状态测试",
            article_url="https://test.example.com/status/999",
            content="测试内容",
            crawl_status=CrawlStatus.COMPLETED.value
        )
        
        article_id = self.db_manager.insert_article(article)
        
        # 测试更新发布状态
        self.db_manager.update_publish_status(article_id, "8wf_net", "completed")
        self.db_manager.update_publish_status(article_id, "1rmb_net", "pending")
        
        # 验证发布状态
        updated_article = self.db_manager.get_article_by_id(article_id)
        self.assertIsNotNone(updated_article.publish_status)
        self.assertEqual(updated_article.publish_status["8wf_net"], "completed")
        self.assertEqual(updated_article.publish_status["1rmb_net"], "pending")
        
        # 测试获取待发布文章
        articles_for_publish = self.db_manager.get_articles_for_publish("00077_top")
        found_article = any(a.id == article_id for a in articles_for_publish)
        self.assertTrue(found_article)  # 00077_top平台还没有发布状态，应该在待发布列表中
    
    def test_statistics(self):
        """测试统计功能"""
        # 创建测试数据
        articles_data = [
            ("wechat", "公众号A", CrawlStatus.COMPLETED.value),
            ("wechat", "公众号B", CrawlStatus.PENDING.value),
            ("linux_do", "Linux.do", CrawlStatus.COMPLETED.value),
            ("linux_do", "Linux.do", CrawlStatus.FAILED.value),
        ]
        
        article_ids = []
        for source_type, source_name, status in articles_data:
            article = Article(
                source_type=source_type,
                source_name=source_name,
                title=f"TEST_统计测试_{len(article_ids)}",
                article_url=f"https://test.example.com/stats/{len(article_ids)}",
                crawl_status=status,
                word_count=100
            )
            article_id = self.db_manager.insert_article(article)
            article_ids.append(article_id)
        
        # 测试采集统计
        crawl_stats = self.db_manager.get_crawl_statistics()
        self.assertIn("wechat", crawl_stats)
        self.assertIn("linux_do", crawl_stats)
        
        wechat_stats = crawl_stats["wechat"]
        self.assertEqual(wechat_stats["completed"], 1)
        self.assertEqual(wechat_stats["pending"], 1)
        
        linux_stats = crawl_stats["linux_do"]
        self.assertEqual(linux_stats["completed"], 1)
        self.assertEqual(linux_stats["failed"], 1)
    
    def test_json_fields(self):
        """测试JSON字段处理"""
        # 创建包含JSON数据的文章
        images_data = [
            {"url": "https://example.com/img1.jpg", "alt": "图片1"},
            {"url": "https://example.com/img2.jpg", "alt": "图片2"}
        ]
        
        links_data = [
            {"url": "https://example.com/link1", "text": "链接1"},
            {"url": "https://example.com/link2", "text": "链接2"}
        ]
        
        tags_data = ["标签1", "标签2", "标签3"]
        
        publish_status_data = {
            "8wf_net": "completed",
            "1rmb_net": "pending"
        }
        
        article = Article(
            source_type=SourceType.WECHAT.value,
            source_name="测试公众号",
            title="TEST_JSON字段测试",
            article_url="https://test.example.com/json/123",
            images=images_data,
            links=links_data,
            tags=tags_data,
            publish_status=publish_status_data
        )
        
        # 插入文章
        article_id = self.db_manager.insert_article(article)
        
        # 查询并验证JSON字段
        retrieved_article = self.db_manager.get_article_by_id(article_id)
        
        self.assertEqual(len(retrieved_article.images), 2)
        self.assertEqual(retrieved_article.images[0]["url"], "https://example.com/img1.jpg")
        
        self.assertEqual(len(retrieved_article.links), 2)
        self.assertEqual(retrieved_article.links[1]["text"], "链接2")
        
        self.assertEqual(len(retrieved_article.tags), 3)
        self.assertIn("标签2", retrieved_article.tags)
        
        self.assertEqual(retrieved_article.publish_status["8wf_net"], "completed")
        self.assertEqual(retrieved_article.publish_status["1rmb_net"], "pending")

class TestDatabaseIntegration(unittest.TestCase):
    """数据库集成测试"""
    
    def setUp(self):
        """测试初始化"""
        self.config = UnifiedConfig()
        self.config.database.database = "cj_test"
        self.db_manager = UnifiedDatabaseManager(self.config)
    
    def test_connection_management(self):
        """测试连接管理"""
        # 测试连接
        self.assertTrue(self.db_manager.connect())
        self.assertIsNotNone(self.db_manager.connection)
        
        # 测试断开连接
        self.db_manager.disconnect()
        self.assertIsNone(self.db_manager.connection)
    
    def test_context_manager(self):
        """测试上下文管理器"""
        with UnifiedDatabaseManager(self.config) as db:
            self.assertIsNotNone(db.connection)
            
            # 执行简单查询
            result = db.execute_query("SELECT 1 as test")
            self.assertEqual(result[0]["test"], 1)
        
        # 上下文结束后连接应该关闭
        self.assertIsNone(db.connection)

if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
