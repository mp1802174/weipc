"""
CFCJ演示脚本
展示如何使用CFCJ模块采集Cloudflare保护的网站
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def demo_basic_usage():
    """基本使用演示"""
    print("=== CFCJ 基本使用演示 ===")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器便于观察
        config.set('crawler.cf_wait_time', 15)  # 增加CF等待时间
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 测试URL
        test_url = "https://linux.do/t/topic/690688/48"
        
        print(f"正在采集: {test_url}")
        print("注意: 这可能需要一些时间来绕过Cloudflare保护...")
        
        # 采集文章
        result = api.crawl_article(test_url)
        
        # 显示结果
        print(f"\n采集成功!")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"作者: {result.get('author', 'N/A')}")
        print(f"发布时间: {result.get('publish_time', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        print(f"字数统计: {result.get('word_count', 0)}")
        
        # Linux.do特有信息
        if 'reply_count' in result:
            print(f"回复数: {result['reply_count']}")
        if 'view_count' in result:
            print(f"浏览数: {result['view_count']}")
        if 'category' in result:
            print(f"分类: {result['category']}")
        
        # 保存结果
        output_file = "demo_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {output_file}")
        
        return True
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所需依赖: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_connection_test():
    """连接测试演示"""
    print("\n=== CFCJ 连接测试演示 ===")
    
    try:
        from wz.cfcj.api import CFCJAPI
        
        api = CFCJAPI()
        
        test_urls = [
            "https://linux.do/",
            "https://linux.do/t/topic/690688/48",
            "https://httpbin.org/html"  # 简单测试页面
        ]
        
        for url in test_urls:
            print(f"\n测试连接: {url}")
            result = api.test_connection(url)
            
            if result['success']:
                print(f"✓ 连接成功")
                print(f"  内容长度: {result['content_length']}")
                print(f"  检测到Cloudflare: {result['has_cloudflare']}")
            else:
                print(f"✗ 连接失败: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"连接测试失败: {e}")
        return False


def demo_batch_crawl():
    """批量采集演示"""
    print("\n=== CFCJ 批量采集演示 ===")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        config.set('browser.headless', True)  # 批量采集使用无头模式
        
        api = CFCJAPI(config)
        
        # 测试URL列表
        urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
            # 可以添加更多测试URL
        ]
        
        print(f"正在批量采集 {len(urls)} 个URL...")
        
        result = api.crawl_articles_batch(urls, batch_size=2)
        
        print(f"\n批量采集完成!")
        print(f"总数: {result['total']}")
        print(f"成功: {result['success_count']}")
        print(f"失败: {result['failed_count']}")
        
        # 显示成功的文章
        for article in result['success']:
            print(f"✓ {article.get('title', 'N/A')} - {article['url']}")
        
        # 显示失败的URL
        for failed in result['failed']:
            print(f"✗ {failed['url']} - {failed['error']}")
        
        return True
        
    except Exception as e:
        print(f"批量采集演示失败: {e}")
        return False


def demo_config_management():
    """配置管理演示"""
    print("\n=== CFCJ 配置管理演示 ===")
    
    try:
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置实例
        config = CFCJConfig()
        
        print("默认配置:")
        print(f"  无头模式: {config.get('browser.headless')}")
        print(f"  最大重试: {config.get('crawler.max_retries')}")
        print(f"  CF等待时间: {config.get('crawler.cf_wait_time')}")
        
        # 修改配置
        config.set('browser.headless', False)
        config.set('crawler.max_retries', 5)
        config.set('crawler.cf_wait_time', 20)
        
        print("\n修改后的配置:")
        print(f"  无头模式: {config.get('browser.headless')}")
        print(f"  最大重试: {config.get('crawler.max_retries')}")
        print(f"  CF等待时间: {config.get('crawler.cf_wait_time')}")
        
        print(f"\n配置文件位置: {config.config_file}")
        print(f"数据目录: {config.data_dir}")
        
        return True
        
    except Exception as e:
        print(f"配置管理演示失败: {e}")
        return False


def main():
    """主函数"""
    print("CFCJ (Cloudflare Content Crawler) 演示程序")
    print("=" * 50)
    
    # 检查依赖
    try:
        import undetected_chromedriver
        print("✓ undetected-chromedriver 可用")
    except ImportError:
        print("✗ undetected-chromedriver 不可用")
        print("  安装: pip install undetected-chromedriver")
    
    try:
        from DrissionPage import ChromiumPage
        print("✓ DrissionPage 可用")
    except ImportError:
        print("✗ DrissionPage 不可用")
        print("  安装: pip install DrissionPage")
    
    try:
        from bs4 import BeautifulSoup
        print("✓ BeautifulSoup 可用")
    except ImportError:
        print("✗ BeautifulSoup 不可用")
        print("  安装: pip install beautifulsoup4")
    
    print()
    
    # 运行演示
    demos = [
        ("配置管理", demo_config_management),
        ("连接测试", demo_connection_test),
        ("批量采集", demo_batch_crawl),
        ("基本使用", demo_basic_usage),  # 放在最后，因为可能需要用户交互
    ]
    
    for name, demo_func in demos:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            success = demo_func()
            if success:
                print(f"✓ {name} 演示完成")
            else:
                print(f"✗ {name} 演示失败")
        except KeyboardInterrupt:
            print(f"\n用户中断 {name} 演示")
            break
        except Exception as e:
            print(f"✗ {name} 演示异常: {e}")
    
    print(f"\n{'='*50}")
    print("演示程序结束")


if __name__ == '__main__':
    main()
