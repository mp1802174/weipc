#!/usr/bin/env python3
"""
测试CFCJ模块采集新页面
测试URL: https://linux.do/t/topic/690973
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    log_file = Path(__file__).parent / 'test_new_page.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_new_page_crawling():
    """测试新页面采集"""
    logger = setup_logging()
    logger.info("开始测试新页面采集...")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置 - 显示浏览器便于观察
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器
        config.set('crawler.cf_wait_time', 10)  # CF等待时间
        config.set('crawler.max_retries', 2)    # 重试次数
        config.set('crawler.request_delay', 2)  # 请求延迟
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 测试URL
        test_url = "https://linux.do/t/topic/690973"
        
        logger.info(f"测试URL: {test_url}")
        logger.info("开始采集页面...")
        
        start_time = time.time()
        
        # 采集文章
        result = api.crawl_article(test_url)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 显示结果
        logger.info(f"采集完成! 耗时: {elapsed_time:.2f}秒")
        logger.info(f"标题: {result.get('title', 'N/A')}")
        logger.info(f"作者: {result.get('author', 'N/A')}")
        logger.info(f"发布时间: {result.get('publish_time', 'N/A')}")
        logger.info(f"内容长度: {len(result.get('content', ''))} 字符")
        logger.info(f"字数统计: {result.get('word_count', 0)}")
        logger.info(f"图片数量: {len(result.get('images', []))}")
        logger.info(f"链接数量: {len(result.get('links', []))}")
        
        # 显示内容预览
        content = result.get('content', '')
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"内容预览: {preview}")
        
        # 保存结果到文件
        output_file = Path(__file__).parent / 'test_new_page_result.json'
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")
        
        # 验证采集质量
        quality_check = {
            'has_title': bool(result.get('title')),
            'has_content': bool(result.get('content')),
            'content_length_ok': len(result.get('content', '')) > 50,
            'has_url': bool(result.get('url')),
            'extraction_time_ok': elapsed_time < 120  # 2分钟内完成
        }
        
        logger.info("采集质量检查:")
        for check, passed in quality_check.items():
            status = "✅ 通过" if passed else "❌ 失败"
            logger.info(f"  {check}: {status}")
        
        all_passed = all(quality_check.values())
        logger.info(f"整体质量: {'✅ 优秀' if all_passed else '⚠️ 需要改进'}")
        
        return True, result
        
    except Exception as e:
        logger.error(f"采集失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False, None

def analyze_content(result):
    """分析采集内容"""
    logger = logging.getLogger(__name__)
    
    if not result:
        logger.warning("没有采集结果可分析")
        return
    
    logger.info("\n=== 内容分析 ===")
    
    # 基本信息
    title = result.get('title', '')
    content = result.get('content', '')
    
    logger.info(f"标题长度: {len(title)} 字符")
    logger.info(f"内容长度: {len(content)} 字符")
    
    # 内容特征分析
    if content:
        lines = content.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        logger.info(f"总行数: {len(lines)}")
        logger.info(f"非空行数: {len(non_empty_lines)}")
        
        # 检查是否包含常见的论坛元素
        forum_indicators = ['回复', '点赞', '收藏', '分享', '楼主', '沙发']
        found_indicators = [indicator for indicator in forum_indicators if indicator in content]
        if found_indicators:
            logger.info(f"发现论坛元素: {', '.join(found_indicators)}")
    
    # 媒体内容
    images = result.get('images', [])
    links = result.get('links', [])
    
    if images:
        logger.info(f"图片信息:")
        for i, img in enumerate(images[:5]):  # 只显示前5个
            logger.info(f"  图片{i+1}: {img.get('url', 'N/A')}")
    
    if links:
        logger.info(f"链接信息 (前5个):")
        for i, link in enumerate(links[:5]):
            logger.info(f"  链接{i+1}: {link.get('url', 'N/A')} - {link.get('text', 'N/A')}")

if __name__ == "__main__":
    print("CFCJ模块新页面采集测试")
    print("=" * 50)
    print("测试URL: https://linux.do/t/topic/690973")
    print()
    
    # 执行测试
    success, result = test_new_page_crawling()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 采集测试成功！")
        
        # 分析内容
        analyze_content(result)
        
        print("\n修复后的CFCJ模块工作正常，可以成功采集页面内容。")
    else:
        print("\n" + "=" * 50)
        print("❌ 采集测试失败！")
        print("请检查错误日志以获取详细信息。")
    
    input("\n按回车键退出...")
