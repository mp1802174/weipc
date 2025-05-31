"""
CFCJ - Cloudflare Content Crawler
Cloudflare保护网站内容采集模块

主要功能：
- 绕过Cloudflare保护进行内容采集
- 支持登录认证和Cookie管理
- 提供结构化的文章数据提取
- 支持批量采集功能
"""

from .core.crawler import CFContentCrawler
from .core.extractor import ContentExtractor
from .auth.manager import AuthManager
from .config.settings import CFCJConfig

__version__ = "1.0.0"
__author__ = "CFCJ Team"

# 导出主要接口
__all__ = [
    'CFContentCrawler',
    'ContentExtractor', 
    'AuthManager',
    'CFCJConfig'
]
