#!/usr/bin/env python3
"""
测试新URL的内容提取
只提取和保存核心内容部分
"""

import sys
import time
import logging
import json
from pathlib import Path

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

def test_new_url():
    """测试新URL的内容提取"""
    logger = setup_logging()
    logger.info("开始测试新URL的内容提取...")
    
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
        
        # 测试URL - 包含图片的帖子
        test_url = "https://linux.do/t/topic/691043"
        
        logger.info(f"测试URL: {test_url}")
        logger.info("开始采集页面...")
        
        start_time = time.time()
        
        # 采集文章
        result = api.crawl_article(test_url)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 显示结果
        logger.info(f"采集完成! 耗时: {elapsed_time:.2f}秒")
        
        # 提取核心信息
        core_info = {
            "url": result.get('url', ''),
            "title": result.get('title', ''),
            "content": result.get('content', '')
        }
        
        # 显示核心信息
        print("\n" + "="*50)
        print("核心提取结果:")
        print("="*50)
        print(f"URL: {core_info['url']}")
        print(f"标题: {core_info['title']}")
        print(f"内容长度: {len(core_info['content'])} 字符")
        print(f"内容预览:")
        print("-"*30)
        print(core_info['content'])
        print("-"*30)
        
        # 保存核心结果
        output_file = Path(__file__).parent / 'new_url_core_result.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(core_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"核心结果已保存到: {output_file}")
        
        # 分析内容
        content = core_info['content']
        if content:
            logger.info(f"内容分析:")
            logger.info(f"  - 字符数: {len(content)}")
            logger.info(f"  - 行数: {len(content.splitlines())}")
            
            # 检查是否包含回复特征
            reply_indicators = ['回复', '引用', '@', '楼主', '沙发', '板凳', '顶', '赞']
            found_indicators = [indicator for indicator in reply_indicators if indicator in content]
            if found_indicators:
                logger.warning(f"  - 可能包含回复元素: {found_indicators}")
            else:
                logger.info("  - ✅ 未发现回复元素")
        else:
            logger.warning("未提取到任何内容")
        
        # 检查图片信息
        images = result.get('images', [])
        logger.info(f"图片信息: 共 {len(images)} 张")
        for i, img in enumerate(images[:3]):  # 只显示前3张
            logger.info(f"  图片{i+1}: {img.get('url', 'N/A')}")
        
        return True, core_info
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False, None

if __name__ == "__main__":
    print("测试新URL内容提取")
    print("URL: https://linux.do/t/topic/691043")
    print("目标: 只提取核心内容部分")
    print()
    
    success, result = test_new_url()
    
    if success:
        print("\n✅ 测试完成！")
        print("请查看提取的核心内容是否符合预期。")
    else:
        print("\n❌ 测试失败！")
    
    input("\n按回车键退出...")
