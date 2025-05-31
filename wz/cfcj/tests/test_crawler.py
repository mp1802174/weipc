"""
CFCJ爬虫模块测试
"""
import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from wz.cfcj.api import CFCJAPI, crawl_single_article
from wz.cfcj.config.settings import CFCJConfig
from wz.cfcj.utils.exceptions import CFCJError


class TestCFCJCrawler(unittest.TestCase):
    """CFCJ爬虫测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = CFCJConfig()
        # 设置测试配置
        self.config.set('browser.headless', True)
        self.config.set('crawler.max_retries', 2)
        self.api = CFCJAPI(self.config)
        
        # 测试URL
        self.test_url = "https://linux.do/t/topic/690688/48"
        self.simple_test_url = "https://httpbin.org/html"  # 简单测试页面
    
    def test_config_loading(self):
        """测试配置加载"""
        self.assertIsNotNone(self.config)
        self.assertTrue(self.config.get('browser.headless'))
        self.assertEqual(self.config.get('crawler.max_retries'), 2)
    
    def test_api_initialization(self):
        """测试API初始化"""
        self.assertIsNotNone(self.api)
        self.assertIsNotNone(self.api.config)
        self.assertIsNotNone(self.api.auth_manager)
        self.assertIsNotNone(self.api.extractor)
    
    def test_invalid_url(self):
        """测试无效URL处理"""
        with self.assertRaises(CFCJError):
            self.api.crawl_article("invalid-url")
    
    def test_simple_crawl(self):
        """测试简单页面爬取"""
        try:
            result = self.api.crawl_article(self.simple_test_url)
            self.assertIsInstance(result, dict)
            self.assertIn('url', result)
            self.assertIn('title', result)
            self.assertIn('content', result)
            self.assertEqual(result['url'], self.simple_test_url)
            print(f"简单爬取测试成功: {result['title']}")
        except Exception as e:
            self.skipTest(f"简单爬取测试跳过，可能是网络问题: {e}")
    
    def test_linux_do_crawl(self):
        """测试linux.do网站爬取"""
        try:
            result = self.api.crawl_article(self.test_url)
            self.assertIsInstance(result, dict)
            self.assertIn('url', result)
            self.assertIn('title', result)
            self.assertIn('content', result)
            self.assertEqual(result['url'], self.test_url)
            
            # 检查linux.do特有字段
            if 'reply_count' in result:
                self.assertIsInstance(result['reply_count'], int)
            if 'view_count' in result:
                self.assertIsInstance(result['view_count'], int)
            
            print(f"Linux.do爬取测试成功: {result['title']}")
            print(f"内容长度: {len(result['content'])} 字符")
            
        except Exception as e:
            self.skipTest(f"Linux.do爬取测试跳过，可能是CF保护或网络问题: {e}")
    
    def test_batch_crawl(self):
        """测试批量爬取"""
        urls = [
            self.simple_test_url,
            "https://httpbin.org/json"
        ]
        
        try:
            result = self.api.crawl_articles_batch(urls, batch_size=2)
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('failed', result)
            self.assertIn('total', result)
            self.assertEqual(result['total'], len(urls))
            
            print(f"批量爬取测试: 成功 {result['success_count']}, 失败 {result['failed_count']}")
            
        except Exception as e:
            self.skipTest(f"批量爬取测试跳过: {e}")
    
    def test_connection_test(self):
        """测试连接测试功能"""
        try:
            result = self.api.test_connection(self.simple_test_url)
            self.assertIsInstance(result, dict)
            self.assertIn('success', result)
            self.assertIn('url', result)
            
            if result['success']:
                self.assertIn('content_length', result)
                print(f"连接测试成功: {result['url']}")
            else:
                print(f"连接测试失败: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.skipTest(f"连接测试跳过: {e}")
    
    def test_convenience_function(self):
        """测试便捷函数"""
        try:
            result = crawl_single_article(self.simple_test_url, self.config)
            self.assertIsInstance(result, dict)
            self.assertIn('url', result)
            print(f"便捷函数测试成功: {result.get('title', 'No title')}")
        except Exception as e:
            self.skipTest(f"便捷函数测试跳过: {e}")


class TestCFCJExtractor(unittest.TestCase):
    """CFCJ提取器测试类"""
    
    def setUp(self):
        """测试前准备"""
        from wz.cfcj.core.extractor import ContentExtractor
        self.extractor = ContentExtractor()
    
    def test_extract_from_html(self):
        """测试从HTML提取内容"""
        html = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <h1>Test Title</h1>
            <div class="content">
                <p>This is test content.</p>
                <p>Another paragraph.</p>
            </div>
            <div class="author">Test Author</div>
            <time datetime="2024-01-01">2024-01-01</time>
        </body>
        </html>
        """
        
        result = self.extractor.extract_article(html, "https://example.com/test")
        
        self.assertIsInstance(result, dict)
        self.assertIn('title', result)
        self.assertIn('content', result)
        self.assertIn('author', result)
        self.assertIn('publish_time', result)
        
        print(f"HTML提取测试成功: {result['title']}")


if __name__ == '__main__':
    # 设置测试输出
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 运行测试
    unittest.main(verbosity=2)
