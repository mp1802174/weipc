#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取Web界面启动脚本
"""

import os
import sys
import logging
import traceback

# 配置基本日志，以便能看到启动信息
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 确保 sys.path 正确设置
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    logger.info(f"当前工作目录: {os.getcwd()}")
    logger.info(f"脚本目录: {current_dir}")
except Exception as path_err:
    logger.error(f"设置路径时出错: {path_err}")
    traceback.print_exc()

# 延迟导入 YE.app，捕获可能的导入错误
try:
    from YE.app import app, scheduler
    logger.info("成功导入 YE.app 模块")
except ImportError as import_err:
    logger.critical(f"导入 YE.app 模块失败: {import_err}")
    traceback.print_exc()
    print(f"严重错误: 无法导入 YE.app 模块。请确保安装了所有依赖并且代码结构正确。错误详情: {import_err}")
    sys.exit(1)
except SyntaxError as syntax_err:
    logger.critical(f"YE.app 模块存在语法错误: {syntax_err}")
    traceback.print_exc()
    print(f"严重错误: YE.app 模块存在语法错误。请修复后再试。错误详情: {syntax_err}")
    sys.exit(1)
except Exception as general_err:
    logger.critical(f"导入 YE.app 模块时发生未知错误: {general_err}")
    traceback.print_exc()
    print(f"严重错误: 导入 YE.app 模块时发生未知错误。错误详情: {general_err}")
    sys.exit(1)

if __name__ == '__main__':
    # 启动调度器 (在应用配置和作业加载完成后)
    if scheduler:
        try:
            if not scheduler.running:
                logger.info("准备在 start_web.py 中启动调度器...")
                scheduler.start()
                logger.info("调度器已在 start_web.py 中成功启动。")
            else:
                logger.info("调度器已经在运行中，无需重新启动。")
        except Exception as scheduler_err:
            logger.error(f"在 start_web.py 中启动调度器失败: {scheduler_err}", exc_info=True)
            print(f"警告: 启动调度器失败，定时任务将不会执行。错误详情: {scheduler_err}")
    else:
        logger.warning("调度器对象为空，无法启动。定时任务将不会执行。")
            
    # 设置端口参数
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError as port_err:
            logger.warning(f"无效的端口参数: {sys.argv[1]}，使用默认端口 5000。错误: {port_err}")
            
    # 启动Web应用
    try:
        print(f"启动微信公众号文章抓取Web界面，访问地址: http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as app_err:
        logger.critical(f"启动Web应用失败: {app_err}", exc_info=True)
        print(f"严重错误: 启动Web应用失败。错误详情: {app_err}")
        sys.exit(1) 