import sys
import os

# 确保此脚本的父目录（WZ）在 sys.path 中，以便能够找到 auth 和 utils
# 通常，当直接运行脚本时，脚本所在的目录会自动添加到 sys.path
# 但为了明确和在某些环境下更可靠，可以显式添加 WZ 目录
current_script_dir = os.path.dirname(os.path.abspath(__file__)) # WZ 目录的绝对路径
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)

# 如果是从 WZ 的父目录运行 python WZ/main.py, current_script_dir 已经是 WZ
# 如果是 cd WZ 然后 python main.py, '' (代表当前目录) 会在 sys.path 中，也能找到 auth

# from WZ.auth import WeChatAuth, LoginError # 如果 WZ 本身是一个包
from auth import WeChatAuth, LoginError # 从同级的 auth 包导入

def demonstrate_login():
    """演示登录功能。"""
    print("--- 演示登录功能 ---")
    # 实例化 WeChatAuth，它会尝试从 WZ/data/id_info.json 加载信息
    auth_handler = WeChatAuth()
    print(f"登录前 - Token: {auth_handler.token}, Cookie: {auth_handler.cookie_str}")

    try:
        # 此处可以传递 DrissionPage 的配置，例如 ChromeDriver 路径
        # auth_handler.login(drission_page_config={'executable_path': '/path/to/your/chromedriver'})
        print("调用 login() 方法... 这将打开浏览器并要求您扫码登录。")
        auth_handler.login()
        print("登录调用完成。")
        print(f"登录后 - Token: {auth_handler.token}, Cookie: {auth_handler.cookie_str}")
        print(f"登录信息已保存到 WZ/data/id_info.json")
    except LoginError as e:
        print(f"登录失败: {e}")
    except Exception as e:
        print(f"发生意外错误: {e}")

def demonstrate_session_check():
    """演示会话检查功能。"""
    print("\n--- 演示会话检查功能 ---")
    auth_handler = WeChatAuth() # 同样会尝试加载 WZ/data/id_info.json

    if not auth_handler.token or not auth_handler.cookie_str:
        print("提示: WZ/data/id_info.json 中无有效的 token/cookie，会话检查可能直接触发登录。")
        print("建议先成功运行一次登录演示，或手动填充 WZ/data/id_info.json。")

    # 1. 模拟会话过期的 API 响应
    expired_response = {
        'base_resp': {
            'err_msg': 'invalid session',
            'ret': -18
        }
    }
    print(f"\n测试 [会话过期] 响应: {expired_response}")
    try:
        if auth_handler.session_is_overdue(expired_response):
            print("session_is_overdue: 返回 True (预期行为，触发了登录尝试)。")
            print(f"检查更新后的 Token: {auth_handler.token}") # 如果登录成功，这里会更新
        else:
            print("session_is_overdue: 返回 False (意外行为)。")
    except LoginError as e:
        print(f"处理 [会话过期] 响应时，重新登录失败: {e}")
    except Exception as e:
        print(f"处理 [会话过期] 响应时发生意外错误: {e}")

    # 2. 模拟频率控制的 API 响应
    freq_response = {
        'base_resp': {
            'err_msg': 'freq control please try again later',
            'ret': -8
        }
    }
    print(f"\n测试 [频率控制] 响应: {freq_response}")
    try:
        if auth_handler.session_is_overdue(freq_response):
            print("session_is_overdue: 返回 True (预期行为，检测到频率控制)。")
        else:
            print("session_is_overdue: 返回 False (意外行为)。")
    except LoginError as e:
        print(f"处理 [频率控制] 响应时发生错误 (不应触发登录): {e}") # 不预期 LoginError
    except Exception as e:
        print(f"处理 [频率控制] 响应时发生意外错误: {e}")

    # 3. 模拟正常的 API 响应
    ok_response = {
        'base_resp': {
            'err_msg': 'ok',
            'ret': 0
        },
        'data': 'some_data'
    }
    print(f"\n测试 [正常] 响应: {ok_response}")
    try:
        if auth_handler.session_is_overdue(ok_response):
            print("session_is_overdue: 返回 True (意外行为)。")
        else:
            print("session_is_overdue: 返回 False (预期行为，会话有效)。")
    except Exception as e: # 不预期任何异常
        print(f"处理 [正常] 响应时发生意外错误: {e}")

if __name__ == "__main__":
    print("****************************************************************")
    print("*      微信公众号认证模块 (WZ) - 功能演示脚本             *")
    print("****************************************************************")
    print("本脚本将演示登录和会话检查功能。")
    print("注意: 登录功能会打开浏览器，需要您手动扫码。")
    print("如果 Chromedriver 不在系统 PATH 中或 DrissionPage 无法自动找到它，")
    print("您可能需要在 WeChatAuth().login() 中配置 'executable_path'。")
    print("----------------------------------------------------------------")

    # 用户可以选择要运行的演示
    # demonstrate_login()
    demonstrate_session_check()

    print("\n演示结束。如果执行了登录，请检查 WZ/data/id_info.json 文件。") 