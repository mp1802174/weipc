"""
微信公众平台认证模块核心类
提供WeChatAuth类用于登录微信公众平台和管理认证信息
"""
import re
import time
import datetime
from DrissionPage import ChromiumPage

from .exceptions import LoginError
from .config import default_config
from .utils.file_utils import handle_json

class WeChatAuth:
    """封装微信公众号登录及会话状态检查功能。"""

    def __init__(self, config=None):
        """
        初始化 WeChatAuth 实例。

        Args:
            config: 配置对象，如果为None则使用默认配置
        """
        self.config = config or default_config
        self.token = None
        self.cookie_str = None
        self._load_id_info()  # 初始化时尝试加载现有信息

    def _load_id_info(self):
        """从 id_info.json 加载 token 和 cookie。"""
        id_info_path = self.config.get_id_info_path()
        id_info = handle_json(str(id_info_path))
        
        if id_info and isinstance(id_info, dict):
            self.token = id_info.get('token')
            self.cookie_str = id_info.get('cookie')
        else:
            # 未找到有效凭据信息时，token和cookie保持为None
            pass

    def login(self, drission_page_config=None):
        """
        使用 DrissionPage 模拟用户登录微信公众平台网页版。
        成功登录后，自动从浏览器会话中获取 token 和 cookie，
        并将其保存到配置的JSON文件中。

        Args:
            drission_page_config (dict, optional): DrissionPage ChromiumPage 的配置项。
                                                  例如: {'driver_path': '/path/to/chromedriver'}
        
        Raises:
            LoginError: 如果登录失败或获取 token/cookie 失败。
        """
        print("开始登录微信公众平台...")
        bro = None  # 初始化浏览器对象
        try:
            if drission_page_config:
                bro = ChromiumPage(addr_driver_opts=drission_page_config)
            else:
                bro = ChromiumPage()  # 使用默认配置

            bro.get('https://mp.weixin.qq.com/')
            bro.set.window.max()
            print("请在打开的浏览器窗口中扫码登录...")

            timeout_seconds = 300  # 5分钟超时
            start_time = time.time()
            while 'token=' not in bro.url:
                if time.time() - start_time > timeout_seconds:
                    raise LoginError("登录超时（5分钟）。请确保您已成功扫码登录。")
                time.sleep(1)
            
            print("登录成功，正在获取 token 和 cookie...")
            # 从URL中提取token
            token_match = re.search(r'token=([a-zA-Z0-9_]+)', bro.url)
            if not token_match:
                raise LoginError("登录成功，但无法从URL中提取token。")
            self.token = token_match.group(1)

            # 获取cookies
            cookies = bro.cookies()
            if not cookies:  # 检查cookies是否为空
                 raise LoginError("登录成功，但获取到的Cookie为空。")
            
            # 处理不同DrissionPage版本返回的cookies格式
            if isinstance(cookies, str):
                self.cookie_str = cookies
            elif isinstance(cookies, list) and all(isinstance(c, dict) for c in cookies):
                self.cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies if 'name' in c and 'value' in c])
            else:
                raise LoginError(f"登录成功，但获取到的Cookie格式非预期: {type(cookies)}")

            if not self.cookie_str:  # 再次检查cookie_str是否成功生成
                raise LoginError("登录成功，但未能成功构建Cookie字符串。")

            # 保存认证信息
            id_data = {
                'token': self.token,
                'cookie': self.cookie_str,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            id_info_path = self.config.get_id_info_path()
            handle_json(str(id_info_path), data=id_data)
            print(f"Token 和 Cookie 已成功保存到 {id_info_path}")

        except Exception as e:
            raise LoginError(f"登录过程中发生错误", details=str(e))
        finally:
            if bro:
                try:
                    bro.quit()
                except Exception as eq:
                    print(f"关闭浏览器时发生错误: {eq}")

    def session_is_overdue(self, api_response):
        """
        检查 API 返回信息，判断 session 或 token 是否过期，或是否遇到频率控制。

        Args:
            api_response (dict): API 调用返回的响应内容 (通常是解析后的JSON字典)。

        Returns:
            bool: True 如果 session/token 过期或遇到频率问题 (并已尝试处理)，
                 False 如果 session/token 有效且无频率控制错误。
        
        Raises:
            LoginError: 如果重新登录尝试失败。
        """
        if not isinstance(api_response, dict):
            return False

        base_resp = api_response.get('base_resp')
        if not isinstance(base_resp, dict):
            return False

        err_msg = base_resp.get('err_msg', '').lower()

        # 会话过期情况处理
        if any(msg in err_msg for msg in ['invalid session', 'invalid csrf token', 'token无效', '登录过期']):
            print(f"检测到会话/Token过期 (错误消息: {err_msg})。尝试重新登录...")
            try:
                self.login()  # 重新登录
                print("重新登录成功。")
                return True
            except LoginError as e:
                print(f"重新登录失败: {e}")
                raise  # 将 LoginError 向上抛出
            except Exception as e:
                print(f"重新登录过程中发生未知错误: {e}")
                raise LoginError(f"重新登录时发生未知错误", details=str(e))

        # 频率控制情况处理
        elif any(msg in err_msg for msg in ['freq control', 'frequency control', '请求频率过快']):
            print(f"检测到请求频率过快 (错误消息: {err_msg})。请稍后重试。")
            return True  # 表示遇到了可处理的频率问题
        
        return False  # Session/Token 有效且无频率问题

    def get_headers(self):
        """
        获取包含认证信息的HTTP请求头
        
        Returns:
            dict: 包含token和cookie的请求头
        
        Raises:
            LoginError: 如果认证信息不完整
        """
        if not self.token or not self.cookie_str:
            raise LoginError("认证信息不完整，请先调用login()方法")
            
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'Referer': 'https://mp.weixin.qq.com/',
            'Cookie': self.cookie_str
        } 