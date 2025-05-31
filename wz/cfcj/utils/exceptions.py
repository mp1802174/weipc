"""
CFCJ异常定义模块
"""


class CFCJError(Exception):
    """CFCJ基础异常类"""
    pass


class BrowserNotAvailableError(CFCJError):
    """浏览器驱动不可用异常"""
    pass


class CloudflareBlockedError(CFCJError):
    """被Cloudflare阻止异常"""
    pass


class AuthenticationError(CFCJError):
    """认证失败异常"""
    pass


class LoginTimeoutError(AuthenticationError):
    """登录超时异常"""
    pass


class ExtractionError(CFCJError):
    """内容提取失败异常"""
    pass


class ConfigurationError(CFCJError):
    """配置错误异常"""
    pass


class NetworkError(CFCJError):
    """网络错误异常"""
    pass
