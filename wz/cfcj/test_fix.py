#!/usr/bin/env python3
"""
测试CFCJ模块修复后的功能
验证是否解决了反复刷新页面卡住的问题
"""

import sys
import os
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    log_file = Path(__file__).parent / 'test_fix.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def test_cfcj_fix():
    """测试CFCJ修复"""
    logger = setup_logging()
    logger.info("开始测试CFCJ修复...")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置 - 显示浏览器便于观察
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器
        config.set('crawler.cf_wait_time', 10)  # 减少CF等待时间
        config.set('crawler.max_retries', 1)    # 减少重试次数
        config.set('crawler.request_delay', 2)  # 减少请求延迟
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 测试URL
        test_url = "https://linux.do/t/topic/690688/48"
        
        logger.info(f"测试URL: {test_url}")
        logger.info("注意观察浏览器是否还会反复刷新页面...")
        
        start_time = time.time()
        
        # 采集文章
        result = api.crawl_article(test_url)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 显示结果
        logger.info(f"测试完成! 耗时: {elapsed_time:.2f}秒")
        logger.info(f"标题: {result.get('title', 'N/A')}")
        logger.info(f"作者: {result.get('author', 'N/A')}")
        logger.info(f"发布时间: {result.get('publish_time', 'N/A')}")
        logger.info(f"内容长度: {len(result.get('content', ''))} 字符")
        
        # 保存结果到文件
        output_file = Path(__file__).parent / 'test_fix_result.json'
        import json
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False

def test_cookies_loading():
    """测试cookies加载功能"""
    logger = logging.getLogger(__name__)
    logger.info("测试cookies加载功能...")
    
    try:
        from wz.cfcj.auth.manager import AuthManager
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        auth_manager = AuthManager(config)
        
        # 检查是否有保存的cookies
        auth_manager.load_auth_data()
        
        if auth_manager.cookies:
            logger.info(f"发现保存的cookies，包含域名: {list(auth_manager.cookies.keys())}")
            
            # 测试特定域名的cookies加载
            test_domain = "linux.do"
            if test_domain in auth_manager.cookies:
                cookies_count = len(auth_manager.cookies[test_domain])
                logger.info(f"域名 {test_domain} 有 {cookies_count} 个cookies")
            else:
                logger.info(f"域名 {test_domain} 没有保存的cookies")
        else:
            logger.info("没有发现保存的cookies")
            
        return True
        
    except Exception as e:
        logger.error(f"测试cookies加载失败: {e}")
        return False

if __name__ == "__main__":
    print("CFCJ模块修复测试")
    print("=" * 50)
    
    # 测试cookies加载
    print("\n1. 测试cookies加载功能...")
    cookies_test_result = test_cookies_loading()
    
    # 测试主要功能
    print("\n2. 测试主要采集功能...")
    main_test_result = test_cfcj_fix()
    
    print("\n" + "=" * 50)
    print("测试结果:")
    print(f"Cookies加载测试: {'通过' if cookies_test_result else '失败'}")
    print(f"主要功能测试: {'通过' if main_test_result else '失败'}")
    
    if main_test_result and cookies_test_result:
        print("\n✅ 所有测试通过！修复成功！")
        print("现在CFCJ模块应该不会再出现反复刷新页面卡住的问题。")
    else:
        print("\n❌ 测试失败，需要进一步调试。")
    
    input("\n按回车键退出...")
