import re
import time
import datetime
from DrissionPage import ChromiumPage
from utils.file_utils import handle_json # 从 WZ 下的 utils 包导入

# 定义自定义异常
class LoginError(Exception):
    """登录失败时抛出的自定义异常。"""
    pass

class WeChatAuth:
    """封装微信公众号登录及会话状态检查功能。"""

    def __init__(self, id_info_filename='id_info', id_info_base_path='data'):
        """
        初始化 WeChatAuth 实例。

        Args:
            id_info_filename (str): 存储 token 和 cookie 的JSON文件名 (不含.json后缀)。
            id_info_base_path (str): id_info.json 文件所在的目录，相对于 WZ/。
        """
        self.id_info_filename = id_info_filename
        self.id_info_base_path = id_info_base_path
        self.token = None
        self.cookie_str = None
        self._load_id_info() # 初始化时尝试加载现有信息

    def _load_id_info(self):
        """从 id_info.json 加载 token 和 cookie。"""
        id_info = handle_json(self.id_info_filename, base_path=self.id_info_base_path)
        if id_info and isinstance(id_info, dict):
            self.token = id_info.get('token')
            self.cookie_str = id_info.get('cookie')
            # print(f"从 {self.id_info_base_path}/{self.id_info_filename}.json 加载 token 和 cookie 成功。")
        else:
            # print(f"未能从 {self.id_info_base_path}/{self.id_info_filename}.json 加载信息或文件为空/格式错误。")
            pass

    def login(self, drission_page_config=None):
        """
        使用 DrissionPage 模拟用户登录微信公众平台网页版。
        成功登录后，自动从浏览器会话中获取 token 和 cookie，
        并将其保存到 WZ/data/id_info.json 文件中。

        Args:
            drission_page_config (dict, optional): DrissionPage ChromiumPage 的配置项。
                                                   例如: {'driver_path': '/path/to/chromedriver'}
                                                   如果为 None，则使用 DrissionPage 的默认配置。
        Raises:
            LoginError: 如果登录失败或获取 token/cookie 失败。
        """
        print("开始登录微信公众平台...")
        bro = None # 初始化 bro
        try:
            if drission_page_config:
                bro = ChromiumPage(addr_driver_opts=drission_page_config)
            else:
                bro = ChromiumPage() # 使用默认配置

            bro.get('https://mp.weixin.qq.com/')
            bro.set.window.max()
            print("请在打开的浏览器窗口中扫码登录...")

            timeout_seconds = 300
            start_time = time.time()
            while 'token=' not in bro.url:
                if time.time() - start_time > timeout_seconds:
                    raise LoginError("登录超时（5分钟）。请确保您已成功扫码登录。")
                time.sleep(1)
            
            print("登录成功，正在获取 token 和 cookie...")
            token_match = re.search(r'token=([a-zA-Z0-9_]+)', bro.url)
            if not token_match:
                raise LoginError("登录成功，但无法从URL中提取token。")
            self.token = token_match.group(1)

            # 获取 cookie，移除了 as_dict=False 参数
            cookies = bro.cookies()
            if not cookies: # 检查 cookies 是否为空
                 raise LoginError("登录成功，但获取到的Cookie为空。")
            
            # 确保 cookies 是一个可迭代的列表，并且列表中的元素是字典
            if not isinstance(cookies, list) or not all(isinstance(c, dict) for c in cookies):
                # 如果不是预期的格式，尝试打印类型和内容以帮助调试
                print(f"获取到的 cookies 格式非预期: 类型 {type(cookies)}, 内容: {cookies}")
                # DrissionPage 某些版本可能直接返回拼接好的字符串，这里尝试处理这种情况
                if isinstance(cookies, str):
                    self.cookie_str = cookies
                else: # 如果无法处理，则抛出错误
                    raise LoginError("登录成功，但获取到的Cookie格式非预期（既不是字典列表也不是字符串）。")
            else: # cookies 是字典列表，正常处理
                self.cookie_str = '; '.join([f"{c['name']}={c['value']}" for c in cookies if 'name' in c and 'value' in c])

            if not self.cookie_str: # 再次检查 self.cookie_str 是否成功生成
                raise LoginError("登录成功，但未能成功构建Cookie字符串。")

            id_data = {
                'token': self.token,
                'cookie': self.cookie_str,
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            handle_json(self.id_info_filename, data=id_data, base_path=self.id_info_base_path)
            print(f"Token 和 Cookie 已成功保存到 {self.id_info_base_path}/{self.id_info_filename}.json")

        except Exception as e:
            raise LoginError(f"登录过程中发生错误: {e}")
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
                  如果 login() 尝试失败，会向上抛出 LoginError。
        """
        if not isinstance(api_response, dict):
            # print("无效的 API 响应格式，应为字典。")
            return False # 或者抛出异常，取决于希望如何处理无效输入

        base_resp = api_response.get('base_resp')
        if not isinstance(base_resp, dict):
            # print("API 响应中缺少 'base_resp' 或其格式不正确。")
            return False

        err_msg = base_resp.get('err_msg', '').lower()

        if 'invalid session' in err_msg or 'invalid csrf token' in err_msg or 'token无效' in err_msg or '登录过期' in err_msg:
            print(f"检测到会话/Token过期 (错误消息: {err_msg})。尝试重新登录...")
            try:
                self.login() # 假设 login 不需要额外参数，或已通过 __init__ 配置
                print("重新登录成功。")
                return True
            except LoginError as e:
                print(f"重新登录失败: {e}")
                raise  # 将 LoginError 向上抛出
            except Exception as e:
                print(f"重新登录过程中发生未知错误: {e}")
                raise LoginError(f"重新登录时发生未知错误: {e}") # 包装为LoginError

        elif 'freq control' in err_msg or 'frequency control' in err_msg or '请求频率过快' in err_msg:
            print(f"检测到请求频率过快 (错误消息: {err_msg})。请稍后重试。")
            # 可选：实现等待后重试的逻辑
            # time.sleep(60) # 例如等待60秒
            return True # 表示遇到了可处理的频率问题
        
        # ret = base_resp.get('ret')
        # if ret == 200013: # token过期的一种表现形式
        #     print(f"检测到Token过期 (ret: {ret})。尝试重新登录...")
        #     try:
        #         self.login()
        #         print("重新登录成功。")
        #         return True
        #     except LoginError as e:
        #         print(f"重新登录失败: {e}")
        #         raise
        #     except Exception as e:
        #         print(f"重新登录过程中发生未知错误: {e}")
        #         raise LoginError(f"重新登录时发生未知错误: {e}")

        return False # Session/Token 有效且无频率问题

# 示例用法 (可以放在 main.py 中)
if __name__ == '__main__':
    # 这里的 main 测试块不应直接运行
    # 如果要测试，需要确保 utils.file_utils 可以被找到
    # 例如，将 WZ 目录添加到 PYTHONPATH
    print("此脚本 (`wechat_auth.py`) 中的 main 测试块不应直接运行。")
    print("请通过运行 WZ 目录下的 main.py 来进行测试。")
    
    # # 伪造一个API响应进行测试
    # # auth_handler = WeChatAuth(id_info_base_path='../data') # 调整路径以便直接测试
    # auth_handler = None # 避免未初始化错误
    
    # # 测试加载现有 id_info.json
    # print(f"初始 Token: {auth_handler.token if auth_handler else 'N/A'}")
    # print(f"初始 Cookie: {auth_handler.cookie_str if auth_handler else 'N/A'}")

    # # # 测试登录 (会打开浏览器，需要手动扫码)
    # # try:
    # #     auth_handler.login()
    # #     print(f"登录后 Token: {auth_handler.token}")
    # #     print(f"登录后 Cookie: {auth_handler.cookie_str}")
    # # except LoginError as e:
    # #     print(f"登录测试失败: {e}")

    # # 测试 session 过期
    # expired_response = {
    #     'base_resp': {
    #         'err_msg': 'invalid session',
    #         'ret': -18
    #     }
    # }
    # print(f"\n测试过期响应: {expired_response}")
    # # try:
    # #     if auth_handler.session_is_overdue(expired_response):
    # #         print("session_is_overdue 返回 True，表示已尝试重新登录或遇到频率问题。")
    # #     else:
    # #         print("session_is_overdue 返回 False，表示会话有效。")
    # # except LoginError as e:
    # #     print(f"处理过期响应时，重新登录失败: {e}")

    # # 测试频率控制
    # freq_response = {
    #     'base_resp': {
    #         'err_msg': 'freq control please try again later',
    #         'ret': -8
    #     }
    # }
    # print(f"\n测试频率控制响应: {freq_response}")
    # # if auth_handler.session_is_overdue(freq_response):
    # #     print("session_is_overdue 返回 True，表示已尝试重新登录或遇到频率问题。")
    # # else:
    # #     print("session_is_overdue 返回 False，表示会话有效。")

    # # 测试正常响应
    # # ok_response = {
    # #     'base_resp': {
    # #         'err_msg': 'ok',
    # #         'ret': 0
    # #     },
    # #     'data': 'some_data'
    # # }
    # # print(f"\n测试正常响应: {ok_response}")
    # # if auth_handler.session_is_overdue(ok_response):
    # #     print("session_is_overdue 返回 True，表示已尝试重新登录或遇到频率问题。")
    # # else:
    # #     print("session_is_overdue 返回 False，表示会话有效。") 