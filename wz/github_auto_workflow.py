#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Actions专用的WZ自动化工作流
针对GitHub Actions环境进行优化
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def setup_github_logging():
    """设置GitHub Actions专用日志"""
    # 创建日志目录
    log_dir = current_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 配置根日志器
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # 输出到控制台
            logging.FileHandler(
                log_dir / f"github_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                encoding='utf-8'
            )
        ]
    )
    
    return logging.getLogger(__name__)

def check_github_environment():
    """检查GitHub Actions环境"""
    logger = logging.getLogger(__name__)
    
    # 检查环境变量
    required_secrets = [
        'DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME',
        'FORUM_DB_HOST', 'FORUM_DB_PORT', 'FORUM_DB_USER', 'FORUM_DB_PASSWORD', 'FORUM_DB_NAME'
    ]
    
    missing_secrets = []
    for secret in required_secrets:
        if not os.getenv(secret):
            missing_secrets.append(secret)
    
    if missing_secrets:
        logger.error(f"缺少必要的环境变量: {missing_secrets}")
        return False
    
    # 检查Chrome浏览器
    try:
        import subprocess
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Chrome浏览器检查通过: {result.stdout.strip()}")
        else:
            logger.error("Chrome浏览器检查失败")
            return False
    except Exception as e:
        logger.error(f"Chrome浏览器检查异常: {e}")
        return False
    
    # 检查ChromeDriver
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"ChromeDriver检查通过: {result.stdout.strip()}")
        else:
            logger.error("ChromeDriver检查失败")
            return False
    except Exception as e:
        logger.error(f"ChromeDriver检查异常: {e}")
        return False
    
    logger.info("GitHub Actions环境检查通过")
    return True

def create_github_config():
    """创建GitHub Actions专用配置"""
    logger = logging.getLogger(__name__)
    
    config = {
        "database": {
            "host": os.getenv('DB_HOST'),
            "port": int(os.getenv('DB_PORT', 3306)),
            "user": os.getenv('DB_USER'),
            "password": os.getenv('DB_PASSWORD'),
            "database": os.getenv('DB_NAME'),
            "charset": "utf8mb4"
        },
        "cfcj": {
            "use_database": True,
            "headless": True,
            "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "chrome_options": [
                "--headless",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--window-size=1920,1080"
            ]
        },
        "forum": {
            "discuz": {
                "host": os.getenv('FORUM_DB_HOST'),
                "port": int(os.getenv('FORUM_DB_PORT', 3306)),
                "user": os.getenv('FORUM_DB_USER'),
                "password": os.getenv('FORUM_DB_PASSWORD'),
                "database": os.getenv('FORUM_DB_NAME'),
                "charset": "utf8mb4"
            }
        }
    }
    
    # 保存配置文件
    config_file = current_dir / "config" / "config.json"
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    logger.info(f"GitHub Actions配置文件已创建: {config_file}")
    return config_file

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GitHub Actions专用WZ自动化工作流')
    parser.add_argument('--steps', default='link_crawl,content_crawl,forum_publish',
                       help='执行步骤，用逗号分隔')
    parser.add_argument('--link-limit', type=int, default=3,
                       help='链接采集限制')
    parser.add_argument('--content-limit', type=int, default=50,
                       help='内容采集限制')
    parser.add_argument('--publish-limit', type=int, default=50,
                       help='论坛发布限制')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，不执行实际操作')
    
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_github_logging()
    logger.info("🚀 GitHub Actions WZ自动化工作流启动")
    logger.info(f"执行参数: {vars(args)}")
    
    try:
        # 检查环境
        if not check_github_environment():
            logger.error("环境检查失败，退出执行")
            sys.exit(1)
        
        # 创建配置
        config_file = create_github_config()
        
        # 导入工作流管理器
        from auto.workflow_manager import WorkflowManager
        
        # 创建工作流管理器
        manager = WorkflowManager(config_file=config_file)
        
        # 解析执行步骤
        steps = [step.strip() for step in args.steps.split(',') if step.strip()]
        
        if args.dry_run:
            logger.info("🧪 试运行模式，检查状态但不执行操作")
            status = manager.get_status()
            logger.info(f"工作流状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        else:
            # 执行工作流
            logger.info(f"开始执行步骤: {steps}")
            result = manager.run(steps=steps)
            
            if result.get('success', False):
                logger.info("✅ 工作流执行成功")
                logger.info(f"执行结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
            else:
                logger.error("❌ 工作流执行失败")
                logger.error(f"错误信息: {result.get('message', '未知错误')}")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"执行过程中发生异常: {e}", exc_info=True)
        sys.exit(1)
    
    logger.info("🎉 GitHub Actions WZ自动化工作流完成")

if __name__ == "__main__":
    main()
