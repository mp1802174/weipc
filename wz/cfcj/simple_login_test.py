#!/usr/bin/env python3
"""
简单的登录采集测试
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def simple_manual_login_test():
    """简单的手动登录测试"""
    print("=== 简单登录采集测试 ===")
    print("这将打开浏览器，请手动登录linux.do")
    print()
    
    try:
        from wz.cfcj.core.crawler import CFContentCrawler
        from wz.cfcj.core.extractor import ContentExtractor
        from wz.cfcj.config.settings import CFCJConfig
        
        # 配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器
        config.set('crawler.cf_wait_time', 15)
        
        # 创建爬虫和提取器
        crawler = CFContentCrawler(config)
        extractor = ContentExtractor(config)
        
        print("1. 启动浏览器...")
        crawler.start_browser()
        
        print("2. 访问登录页面...")
        login_url = "https://linux.do/login"
        crawler.get_page(login_url)
        print("✓ 登录页面已打开")
        print("请在浏览器中完成登录")
        
        input("登录完成后，按回车键继续...")
        
        print("3. 访问目标页面...")
        target_url = "https://linux.do/t/topic/690688/48"
        html_content = crawler.get_page(target_url)
        print(f"✓ 获取页面内容，长度: {len(html_content)} 字符")
        
        print("4. 提取文章内容...")
        result = extractor.extract_article(html_content, target_url)
        
        print("\n=== 采集结果 ===")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        print(f"作者: {result.get('author', 'N/A')}")
        print(f"发布时间: {result.get('publish_time', 'N/A')}")
        
        # 保存结果到cfcj目录
        cfcj_dir = Path(__file__).parent
        output_file = cfcj_dir / "simple_login_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {output_file}")
        
        # 显示部分内容
        content = result.get('content', '')
        if content:
            print(f"\n内容预览:")
            print(content[:300] + "..." if len(content) > 300 else content)
        
        crawler.close_browser()
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    simple_manual_login_test()
