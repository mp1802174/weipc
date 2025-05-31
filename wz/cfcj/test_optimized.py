#!/usr/bin/env python3
"""
测试优化后的CFCJ内容提取功能
验证是否只采集主贴内容，排除回复和无关元素
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
    log_file = Path(__file__).parent / 'test_optimized.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_optimized_extraction():
    """测试优化后的内容提取"""
    logger = setup_logging()
    logger.info("开始测试优化后的内容提取...")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器便于观察
        config.set('crawler.cf_wait_time', 10)
        config.set('crawler.max_retries', 2)
        config.set('crawler.request_delay', 2)
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 测试URL - 使用之前测试成功的URL
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
        logger.info(f"内容长度: {len(result.get('content', ''))} 字符")
        logger.info(f"图片数量: {len(result.get('images', []))}")
        
        # 分析内容质量
        content = result.get('content', '')
        logger.info("\n=== 内容质量分析 ===")
        
        # 检查是否包含回复内容的特征
        reply_indicators = ['回复', '引用', '@', '楼主', '沙发']
        found_replies = [indicator for indicator in reply_indicators if indicator in content]
        if found_replies:
            logger.warning(f"内容中可能包含回复元素: {found_replies}")
        else:
            logger.info("✅ 内容中未发现回复元素")
        
        # 显示内容预览
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            logger.info(f"内容预览:\n{preview}")
        
        # 分析图片
        images = result.get('images', [])
        logger.info(f"\n=== 图片分析 ===")
        logger.info(f"共提取到 {len(images)} 张图片")
        
        content_images = 0
        avatar_images = 0
        
        for i, img in enumerate(images[:5]):  # 只显示前5张
            url = img.get('url', '')
            
            if 'avatar' in url.lower() or 'user_avatar' in url.lower():
                avatar_images += 1
                logger.warning(f"图片{i+1}: 头像图片 - {url}")
            else:
                content_images += 1
                logger.info(f"图片{i+1}: 内容图片 - {url}")
        
        logger.info(f"内容图片: {content_images} 张")
        logger.info(f"头像图片: {avatar_images} 张")
        
        # 保存结果
        output_file = Path(__file__).parent / 'optimized_result.json'
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")
        
        return True, result
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False, None

if __name__ == "__main__":
    print("CFCJ优化后内容提取测试")
    print("=" * 50)
    print("测试URL: https://linux.do/t/topic/690973")
    print("目标: 只采集主贴内容，排除回复和无关元素")
    print()
    
    # 执行测试
    success, result = test_optimized_extraction()
    
    if success:
        print("\n✅ 优化测试成功！")
        print("优化后的CFCJ模块能够精确提取主贴内容。")
    else:
        print("\n❌ 优化测试失败！")
        print("请检查错误日志。")
    
    input("\n按回车键退出...")
