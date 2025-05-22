#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取命令行入口
"""

import sys
import os

# 确保WZ目录在sys.path中
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# 导入并执行主程序
from wzzq.main import main

if __name__ == '__main__':
    sys.exit(main()) 