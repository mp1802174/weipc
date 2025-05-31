#!/usr/bin/env python3
"""
分析linux.do页面结构，为优化内容提取选择器提供依据
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
    log_file = Path(__file__).parent / 'analyze_page.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def analyze_linux_do_structure():
    """分析linux.do页面结构"""
    logger = setup_logging()
    logger.info("开始分析linux.do页面结构...")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器便于观察
        
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
        
        # 保存原始HTML用于分析
        html_file = Path(__file__).parent / 'page_structure.html'
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"原始HTML已保存到: {html_file}")
        
        # 解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 分析页面结构
        logger.info("\n=== 页面结构分析 ===")
        
        # 1. 分析标题结构
        logger.info("\n1. 标题结构分析:")
        title_candidates = [
            'h1',
            '.fancy-title',
            '.topic-title',
            'a.fancy-title span[dir="auto"]',
            '.fancy-title span[dir="auto"]'
        ]
        
        for selector in title_candidates:
            elements = soup.select(selector)
            if elements:
                for i, elem in enumerate(elements[:3]):  # 只显示前3个
                    text = elem.get_text(strip=True)[:100]
                    logger.info(f"  {selector}[{i}]: {text}")
        
        # 2. 分析主贴内容结构
        logger.info("\n2. 主贴内容结构分析:")
        
        # 查找第一个帖子（主贴）
        first_post = soup.select_one('#post_1, .topic-post:first-child, [data-post-number="1"]')
        if first_post:
            logger.info("  找到主贴容器")
            
            # 分析主贴内的内容选择器
            content_candidates = [
                '.cooked',
                '.post-content',
                '.topic-body .cooked',
                '[data-post-content]'
            ]
            
            for selector in content_candidates:
                elements = first_post.select(selector)
                if elements:
                    for i, elem in enumerate(elements[:2]):
                        text = elem.get_text(strip=True)[:150]
                        logger.info(f"  主贴 {selector}[{i}]: {text}")
        
        # 3. 分析图片结构
        logger.info("\n3. 图片结构分析:")
        if first_post:
            images = first_post.select('img')
            logger.info(f"  主贴中找到 {len(images)} 张图片")
            for i, img in enumerate(images[:5]):
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '')
                logger.info(f"  图片{i+1}: {src} (alt: {alt})")
        
        # 4. 分析需要排除的元素
        logger.info("\n4. 需要排除的元素分析:")
        exclude_candidates = [
            '.topic-navigation',
            '.topic-map',
            '.suggested-topics',
            '.post-menu-area',
            '.topic-footer-buttons',
            '.replies',
            '.user-info',
            '.avatar',
            '.controls',
            '.quote-controls',
            '.post-controls'
        ]
        
        for selector in exclude_candidates:
            elements = soup.select(selector)
            if elements:
                logger.info(f"  发现需排除元素 {selector}: {len(elements)} 个")
        
        # 5. 分析回复结构（用于排除）
        logger.info("\n5. 回复结构分析:")
        reply_posts = soup.select('.topic-post:not(:first-child), [data-post-number]:not([data-post-number="1"])')
        logger.info(f"  找到 {len(reply_posts)} 个回复帖子")
        
        # 6. 生成优化建议
        logger.info("\n=== 优化建议 ===")
        
        # 建议的选择器配置
        suggested_config = {
            "title_selectors": [
                "a.fancy-title span[dir='auto']",
                ".fancy-title span[dir='auto']",
                "h1"
            ],
            "main_post_selector": "#post_1, .topic-post:first-child, [data-post-number='1']",
            "content_selectors": [
                ".cooked",
                ".post-content"
            ],
            "exclude_selectors": [
                ".topic-navigation",
                ".topic-map", 
                ".suggested-topics",
                ".post-menu-area",
                ".topic-footer-buttons",
                ".replies",
                ".user-info",
                ".avatar",
                ".controls",
                ".quote-controls",
                ".post-controls",
                ".topic-post:not(:first-child)",
                "[data-post-number]:not([data-post-number='1'])"
            ]
        }
        
        # 保存建议配置
        import json
        config_file = Path(__file__).parent / 'suggested_selectors.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(suggested_config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"建议的选择器配置已保存到: {config_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False
    finally:
        if 'api' in locals() and api.crawler:
            api.crawler.close_browser()

if __name__ == "__main__":
    print("Linux.do页面结构分析")
    print("=" * 50)
    
    success = analyze_linux_do_structure()
    
    if success:
        print("\n✅ 页面结构分析完成！")
        print("请查看日志文件和生成的配置文件以获取详细信息。")
    else:
        print("\n❌ 页面结构分析失败！")
        print("请检查错误日志。")
    
    input("\n按回车键退出...")
