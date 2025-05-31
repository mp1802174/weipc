"""
CFCJ主程序
提供命令行接口和示例用法
"""
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wz.cfcj.api import CFCJAPI, crawl_single_article
from wz.cfcj.config.settings import CFCJConfig
from wz.cfcj.utils.exceptions import CFCJError


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CFCJ - Cloudflare Content Crawler')
    
    # 基本参数
    parser.add_argument('url', nargs='?', help='要采集的URL')
    parser.add_argument('--urls', nargs='+', help='批量采集的URL列表')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--config', help='配置文件路径')
    
    # 浏览器配置
    parser.add_argument('--headless', action='store_true', help='无头模式运行')
    parser.add_argument('--no-headless', action='store_true', help='显示浏览器窗口')
    
    # 登录配置
    parser.add_argument('--login', action='store_true', help='需要登录')
    parser.add_argument('--username', help='登录用户名')
    parser.add_argument('--password', help='登录密码')
    parser.add_argument('--login-url', help='登录页面URL')
    
    # 其他选项
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--test-connection', action='store_true', help='测试连接')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--batch-size', type=int, default=5, help='批量处理大小')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # 加载配置
    config = CFCJConfig(args.config) if args.config else CFCJConfig()
    
    # 设置浏览器模式
    if args.headless:
        config.set('browser.headless', True)
    elif args.no_headless:
        config.set('browser.headless', False)
    
    # 创建API实例
    api = CFCJAPI(config)
    
    try:
        if args.test:
            run_tests()
        elif args.test_connection:
            if not args.url:
                print("错误: 测试连接需要提供URL")
                sys.exit(1)
            test_connection(api, args.url)
        elif args.urls:
            # 批量采集
            batch_crawl(api, args.urls, args, config)
        elif args.url:
            # 单个采集
            single_crawl(api, args.url, args, config)
        else:
            # 交互模式
            interactive_mode(api, config)
            
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def single_crawl(api: CFCJAPI, url: str, args, config: CFCJConfig):
    """单个URL采集"""
    print(f"正在采集: {url}")
    
    # 准备登录凭据
    login_credentials = None
    if args.login:
        if not all([args.username, args.password, args.login_url]):
            print("错误: 登录模式需要提供 --username, --password, --login-url")
            sys.exit(1)
        
        login_credentials = {
            'username': args.username,
            'password': args.password,
            'login_url': args.login_url
        }
    
    try:
        result = api.crawl_article(url, args.login, login_credentials)
        
        # 输出结果
        print(f"采集成功!")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"作者: {result.get('author', 'N/A')}")
        print(f"发布时间: {result.get('publish_time', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        print(f"字数统计: {result.get('word_count', 0)}")
        
        # 保存结果
        if args.output:
            save_result(result, args.output)
        else:
            # 默认保存到当前目录
            filename = f"article_{result.get('title', 'unknown')[:50]}.json"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            save_result(result, filename)
        
    except CFCJError as e:
        print(f"采集失败: {e}")
        sys.exit(1)


def batch_crawl(api: CFCJAPI, urls: List[str], args, config: CFCJConfig):
    """批量URL采集"""
    print(f"正在批量采集 {len(urls)} 个URL")
    
    # 准备登录凭据
    login_credentials = None
    if args.login:
        if not all([args.username, args.password, args.login_url]):
            print("错误: 登录模式需要提供 --username, --password, --login-url")
            sys.exit(1)
        
        login_credentials = {
            'username': args.username,
            'password': args.password,
            'login_url': args.login_url
        }
    
    try:
        result = api.crawl_articles_batch(
            urls, 
            args.login, 
            login_credentials, 
            args.batch_size
        )
        
        # 输出结果
        print(f"批量采集完成!")
        print(f"总数: {result['total']}")
        print(f"成功: {result['success_count']}")
        print(f"失败: {result['failed_count']}")
        
        # 显示成功的文章
        for article in result['success']:
            print(f"✓ {article.get('title', 'N/A')} - {article['url']}")
        
        # 显示失败的URL
        for failed in result['failed']:
            print(f"✗ {failed['url']} - {failed['error']}")
        
        # 保存结果
        if args.output:
            save_result(result, args.output)
        else:
            save_result(result, "batch_crawl_result.json")
        
    except CFCJError as e:
        print(f"批量采集失败: {e}")
        sys.exit(1)


def test_connection(api: CFCJAPI, url: str):
    """测试连接"""
    print(f"正在测试连接: {url}")
    
    try:
        result = api.test_connection(url)
        
        if result['success']:
            print(f"✓ 连接成功")
            print(f"  内容长度: {result['content_length']}")
            print(f"  检测到Cloudflare: {result['has_cloudflare']}")
            if 'title' in result:
                print(f"  页面标题: {result['title']}")
        else:
            print(f"✗ 连接失败: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"✗ 测试失败: {e}")


def interactive_mode(api: CFCJAPI, config: CFCJConfig):
    """交互模式"""
    print("=== CFCJ 交互模式 ===")
    print("输入 'help' 查看帮助，输入 'quit' 退出")
    
    while True:
        try:
            command = input("\nCFCJ> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                break
            elif command.lower() == 'help':
                show_help()
            elif command.startswith('crawl '):
                url = command[6:].strip()
                if url:
                    try:
                        result = api.crawl_article(url)
                        print(f"采集成功: {result.get('title', 'N/A')}")
                        print(f"内容长度: {len(result.get('content', ''))} 字符")
                    except Exception as e:
                        print(f"采集失败: {e}")
                else:
                    print("请提供URL")
            elif command.startswith('test '):
                url = command[5:].strip()
                if url:
                    test_connection(api, url)
                else:
                    print("请提供URL")
            elif command == 'config':
                print(f"当前配置:")
                print(f"  无头模式: {config.get('browser.headless')}")
                print(f"  最大重试: {config.get('crawler.max_retries')}")
                print(f"  CF等待时间: {config.get('crawler.cf_wait_time')}")
            else:
                print("未知命令，输入 'help' 查看帮助")
                
        except KeyboardInterrupt:
            print("\n使用 'quit' 退出")
        except EOFError:
            break


def show_help():
    """显示帮助信息"""
    help_text = """
可用命令:
  crawl <url>     - 采集指定URL的文章
  test <url>      - 测试连接到指定URL
  config          - 显示当前配置
  help            - 显示此帮助信息
  quit/exit/q     - 退出程序

示例:
  crawl https://linux.do/t/topic/690688/48
  test https://linux.do/
"""
    print(help_text)


def save_result(result: Dict[str, Any], filename: str):
    """保存结果到文件"""
    try:
        # 如果filename不是绝对路径，则保存到cfcj目录
        if not Path(filename).is_absolute():
            cfcj_dir = Path(__file__).parent
            filename = cfcj_dir / filename

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"结果已保存到: {filename}")
    except Exception as e:
        print(f"保存文件失败: {e}")


def run_tests():
    """运行测试"""
    print("正在运行CFCJ测试...")
    
    try:
        import unittest
        from wz.cfcj.tests.test_crawler import TestCFCJCrawler
        
        # 创建测试套件
        suite = unittest.TestLoader().loadTestsFromTestCase(TestCFCJCrawler)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        if result.wasSuccessful():
            print("所有测试通过!")
        else:
            print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
            
    except ImportError as e:
        print(f"无法运行测试: {e}")


if __name__ == '__main__':
    main()
