#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取命令行入口
"""

import sys
import os
import io

# 设置标准输出编码为UTF-8，解决Windows下的编码问题
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 确保WZ目录在sys.path中
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 导入并执行主程序
from wzzq.main import main

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"执行失败: {e}", file=sys.stderr)
        sys.exit(1)