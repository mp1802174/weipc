#!/usr/bin/env python3
"""
调试linux.do页面选择器
分析页面结构，找出正确的主贴内容选择器
"""

import sys
import time
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def debug_page_structure():
    """调试页面结构"""
    logger = setup_logging()
    logger.info("开始调试页面结构...")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 测试URL
        test_url = "https://linux.do/t/topic/691043"
        
        logger.info(f"分析URL: {test_url}")
        
        # 启动浏览器并获取页面HTML
        api.crawler = api.crawler or api._create_crawler()
        api.crawler.start_browser()
        
        # 获取页面HTML
        html_content = api.crawler.get_page(test_url)
        
        # 保存HTML用于分析
        html_file = Path(__file__).parent / 'debug_page.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"页面HTML已保存到: {html_file}")
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        print("\n" + "="*60)
        print("页面结构分析")
        print("="*60)
        
        # 1. 分析标题
        print("\n1. 标题分析:")
        title_selectors = [
            'h1',
            '.fancy-title',
            'a.fancy-title span[dir="auto"]',
            '.fancy-title span[dir="auto"]'
        ]
        
        for selector in title_selectors:
            elements = soup.select(selector)
            if elements:
                for i, elem in enumerate(elements[:2]):
                    text = elem.get_text(strip=True)
                    print(f"  {selector}[{i}]: {text}")
        
        # 2. 分析主贴容器
        print("\n2. 主贴容器分析:")
        post_selectors = [
            '#post_1',
            '.topic-post:first-child',
            '[data-post-number="1"]',
            '.post-stream .topic-post:first-child',
            'article[data-post-number="1"]',
            '.topic-body'
        ]
        
        main_post = None
        for selector in post_selectors:
            elements = soup.select(selector)
            if elements:
                element = elements[0]
                print(f"  找到主贴容器: {selector}")
                print(f"    标签: {element.name}")
                print(f"    ID: {element.get('id', 'N/A')}")
                print(f"    类名: {element.get('class', [])}")
                
                if not main_post:
                    main_post = element
                break
        
        # 3. 在主贴中分析内容
        if main_post:
            print("\n3. 主贴内容分析:")
            content_selectors = [
                '.cooked',
                '.post-content',
                '.topic-body .cooked',
                '[data-post-content]',
                '.regular'
            ]
            
            for selector in content_selectors:
                content_elements = main_post.select(selector)
                if content_elements:
                    for i, elem in enumerate(content_elements[:2]):
                        text = elem.get_text(strip=True)
                        print(f"  {selector}[{i}]: {text[:100]}...")
                        
                        # 分析子元素
                        children = elem.find_all(['p', 'div', 'img'], recursive=False)
                        print(f"    子元素数量: {len(children)}")
                        for j, child in enumerate(children[:3]):
                            if child.name == 'img':
                                src = child.get('src') or child.get('data-src')
                                print(f"      子元素{j}: <img> src={src}")
                            else:
                                child_text = child.get_text(strip=True)
                                print(f"      子元素{j}: <{child.name}> {child_text[:50]}...")
        
        # 4. 分析图片
        print("\n4. 图片分析:")
        if main_post:
            images = main_post.find_all('img')
            print(f"  主贴中找到 {len(images)} 张图片")
            for i, img in enumerate(images[:5]):
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '')
                parent_class = img.parent.get('class', []) if img.parent else []
                print(f"    图片{i+1}: {src}")
                print(f"      alt: {alt}")
                print(f"      父元素类名: {parent_class}")
        
        # 5. 生成优化建议
        print("\n5. 优化建议:")
        print("  基于分析结果，建议的选择器配置:")
        
        # 关闭浏览器
        api.crawler.close_browser()
        
        return True
        
    except Exception as e:
        logger.error(f"调试失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("Linux.do页面结构调试工具")
    print("目标: 找出正确的主贴内容选择器")
    
    success = debug_page_structure()
    
    if success:
        print("\n✅ 调试完成！")
        print("请查看分析结果以优化选择器配置。")
    else:
        print("\n❌ 调试失败！")
    
    input("\n按回车键退出...")
