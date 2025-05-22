"""
微信公众平台认证模块的异常类定义
"""

class LoginError(Exception):
    """登录失败时抛出的自定义异常。

    属性:
        message -- 错误消息
        details -- 详细错误信息
    """
    
    def __init__(self, message, details=None):
        self.message = message
        self.details = details
        super().__init__(self.message)
        
    def __str__(self):
        if self.details:
            return f"{self.message} - 详细信息: {self.details}"
        return self.message 