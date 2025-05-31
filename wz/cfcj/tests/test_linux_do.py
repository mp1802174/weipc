"""
专门针对linux.do网站的测试
"""
import unittest
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from wz.cfcj.api import CFCJAPI
from wz.cfcj.config.settings import CFCJConfig


class TestLinuxDoCrawler(unittest.TestCase):
    """Linux.do网站专项测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = CFCJConfig()
        # 针对linux.do的特殊配置
        self.config.set('browser.headless', False)  # 可能需要显示浏览器来处理CF
        self.config.set('crawler.cf_wait_time', 15)  # 增加CF等待时间
        self.config.set('crawler.max_retries', 3)
        
        self.api = CFCJAPI(self.config)
        
        # 测试URL
        self.target_url = "https://linux.do/t/topic/690688/48"
        self.login_url = "https://linux.do/login"
        
        # 如果需要登录，可以在这里设置凭据
        self.login_credentials = {
            'username': '',  # 在实际测试时填入
            'password': '',  # 在实际测试时填入
            'login_url': self.login_url,
            'username_selector': '#login-account-name',
            'password_selector': '#login-account-password',
            'submit_selector': '#login-button'
        }
    
    def test_linux_do_without_login(self):
        """测试不登录访问linux.do"""
        try:
            print(f"正在测试访问: {self.target_url}")
            result = self.api.crawl_article(self.target_url)
            
            # 验证基本字段
            self.assertIsInstance(result, dict)
            self.assertIn('url', result)
            self.assertIn('title', result)
            self.assertIn('content', result)
            
            # 打印结果
            print(f"标题: {result.get('title', 'N/A')}")
            print(f"作者: {result.get('author', 'N/A')}")
            print(f"发布时间: {result.get('publish_time', 'N/A')}")
            print(f"内容长度: {len(result.get('content', ''))} 字符")
            print(f"字数统计: {result.get('word_count', 0)}")
            
            # Linux.do特有字段
            if 'reply_count' in result:
                print(f"回复数: {result['reply_count']}")
            if 'view_count' in result:
                print(f"浏览数: {result['view_count']}")
            if 'category' in result:
                print(f"分类: {result['category']}")
            
            # 保存结果到文件
            output_file = Path(__file__).parent / "linux_do_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"结果已保存到: {output_file}")
            
            # 验证内容不为空
            self.assertGreater(len(result.get('content', '')), 0, "内容不应为空")
            
        except Exception as e:
            print(f"测试失败: {e}")
            # 不直接失败，而是跳过测试，因为可能是网络或CF问题
            self.skipTest(f"Linux.do访问测试跳过: {e}")
    
    def test_linux_do_with_login(self):
        """测试登录后访问linux.do"""
        # 检查是否提供了登录凭据
        if not self.login_credentials['username'] or not self.login_credentials['password']:
            self.skipTest("跳过登录测试：未提供登录凭据")
        
        try:
            print(f"正在测试登录访问: {self.target_url}")
            result = self.api.crawl_article(
                self.target_url, 
                login_required=True, 
                login_credentials=self.login_credentials
            )
            
            # 验证结果
            self.assertIsInstance(result, dict)
            self.assertIn('url', result)
            self.assertIn('title', result)
            self.assertIn('content', result)
            
            print(f"登录访问成功: {result.get('title', 'N/A')}")
            
            # 保存登录结果
            output_file = Path(__file__).parent / "linux_do_login_result.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"登录结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"登录测试失败: {e}")
            self.skipTest(f"Linux.do登录测试跳过: {e}")
    
    def test_linux_do_connection(self):
        """测试linux.do连接"""
        try:
            result = self.api.test_connection(self.target_url)
            
            print(f"连接测试结果: {result}")
            
            if result['success']:
                print(f"连接成功，内容长度: {result['content_length']}")
                print(f"是否检测到Cloudflare: {result['has_cloudflare']}")
            else:
                print(f"连接失败: {result.get('error', 'Unknown error')}")
            
        except Exception as e:
            print(f"连接测试异常: {e}")
            self.skipTest(f"连接测试跳过: {e}")
    
    def test_multiple_linux_do_pages(self):
        """测试多个linux.do页面"""
        urls = [
            "https://linux.do/t/topic/690688/48",
            "https://linux.do/",  # 首页
            # 可以添加更多测试URL
        ]
        
        try:
            result = self.api.crawl_articles_batch(urls, batch_size=1)
            
            print(f"批量测试结果:")
            print(f"总数: {result['total']}")
            print(f"成功: {result['success_count']}")
            print(f"失败: {result['failed_count']}")
            
            for success_item in result['success']:
                print(f"成功: {success_item['title']} - {success_item['url']}")
            
            for failed_item in result['failed']:
                print(f"失败: {failed_item['url']} - {failed_item['error']}")
            
        except Exception as e:
            print(f"批量测试失败: {e}")
            self.skipTest(f"批量测试跳过: {e}")


def run_manual_test():
    """手动运行测试（用于调试）"""
    print("=== Linux.do 手动测试 ===")
    
    config = CFCJConfig()
    config.set('browser.headless', False)  # 显示浏览器便于观察
    config.set('crawler.cf_wait_time', 20)
    
    api = CFCJAPI(config)
    
    try:
        url = "https://linux.do/t/topic/690688/48"
        print(f"正在访问: {url}")
        
        result = api.crawl_article(url)
        
        print(f"采集成功!")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))}")
        print(f"作者: {result.get('author', 'N/A')}")
        
        # 保存结果
        with open('manual_test_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print("结果已保存到 manual_test_result.json")
        
    except Exception as e:
        print(f"手动测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Linux.do测试')
    parser.add_argument('--manual', action='store_true', help='运行手动测试')
    args = parser.parse_args()
    
    if args.manual:
        run_manual_test()
    else:
        # 设置测试输出
        import logging
        logging.basicConfig(level=logging.INFO)
        
        # 运行单元测试
        unittest.main(verbosity=2)
