"""
微信公众平台认证模块测试
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# 确保可以导入wechat_mp_auth模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from wechat_mp_auth import WeChatAuth, LoginError
from wechat_mp_auth.config import Config

class TestWeChatAuth(unittest.TestCase):
    """测试WeChatAuth类的基本功能"""
    
    def test_init(self):
        """测试初始化"""
        auth = WeChatAuth()
        self.assertIsNone(auth.token)
        self.assertIsNone(auth.cookie_str)
    
    @patch('wechat_mp_auth.auth.handle_json')
    def test_load_id_info(self, mock_handle_json):
        """测试加载ID信息"""
        # 模拟handle_json返回一个有效的id_info字典
        mock_handle_json.return_value = {
            'token': 'test_token',
            'cookie': 'test_cookie'
        }
        
        auth = WeChatAuth()
        self.assertEqual(auth.token, 'test_token')
        self.assertEqual(auth.cookie_str, 'test_cookie')
    
    def test_session_is_overdue_invalid_input(self):
        """测试session_is_overdue方法处理无效输入"""
        auth = WeChatAuth()
        
        # 测试非字典输入
        self.assertFalse(auth.session_is_overdue("not a dict"))
        
        # 测试缺少base_resp的字典
        self.assertFalse(auth.session_is_overdue({}))
        
        # 测试base_resp不是字典
        self.assertFalse(auth.session_is_overdue({'base_resp': 'not a dict'}))
    
    @patch('wechat_mp_auth.auth.WeChatAuth.login')
    def test_session_is_overdue_expired(self, mock_login):
        """测试session_is_overdue方法处理会话过期的情况"""
        auth = WeChatAuth()
        
        # 测试会话过期的情况
        expired_response = {
            'base_resp': {
                'err_msg': 'invalid session',
                'ret': -18
            }
        }
        
        # 设置mock不执行实际的login方法
        mock_login.return_value = None
        
        result = auth.session_is_overdue(expired_response)
        self.assertTrue(result)
        mock_login.assert_called_once()
    
    def test_session_is_overdue_freq_control(self):
        """测试session_is_overdue方法处理频率控制的情况"""
        auth = WeChatAuth()
        
        # 测试频率控制的情况
        freq_response = {
            'base_resp': {
                'err_msg': 'freq control please try again later',
                'ret': -8
            }
        }
        
        result = auth.session_is_overdue(freq_response)
        self.assertTrue(result)
    
    def test_session_is_overdue_normal(self):
        """测试session_is_overdue方法处理正常响应的情况"""
        auth = WeChatAuth()
        
        # 测试正常响应的情况
        ok_response = {
            'base_resp': {
                'err_msg': 'ok',
                'ret': 0
            },
            'data': 'some_data'
        }
        
        result = auth.session_is_overdue(ok_response)
        self.assertFalse(result)
    
    def test_get_headers(self):
        """测试get_headers方法"""
        auth = WeChatAuth()
        
        # 测试未设置token和cookie_str的情况
        with self.assertRaises(LoginError):
            auth.get_headers()
        
        # 测试设置了token和cookie_str的情况
        auth.token = 'test_token'
        auth.cookie_str = 'test_cookie'
        
        headers = auth.get_headers()
        self.assertEqual(headers['Cookie'], 'test_cookie')
        self.assertIn('User-Agent', headers)
        self.assertIn('Referer', headers)

if __name__ == '__main__':
    unittest.main() 