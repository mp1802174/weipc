"""
微信公众平台认证模块
提供WeChatAuth类用于登录微信公众平台和管理认证信息
"""

from .auth import WeChatAuth
from .exceptions import LoginError

__all__ = ['WeChatAuth', 'LoginError'] 