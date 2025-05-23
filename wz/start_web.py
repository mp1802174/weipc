#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取Web界面启动脚本
"""

import os
import sys
from YE.app import app

if __name__ == '__main__':
    # 设置路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        
    # 设置端口参数
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
            
    print(f"启动微信公众号文章抓取Web界面，访问地址: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False) 