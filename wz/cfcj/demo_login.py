#!/usr/bin/env python3
"""
CFCJ登录采集演示脚本
演示如何使用CFCJ采集需要登录的linux.do页面
"""
import sys
import json
import getpass
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def demo_linux_do_login():
    """演示linux.do登录采集"""
    print("=== Linux.do 登录采集演示 ===")
    print("注意：这将打开浏览器窗口，需要您手动完成登录过程")
    print()
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置 - 显示浏览器便于手动登录
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器
        config.set('crawler.cf_wait_time', 20)  # 增加等待时间
        config.set('crawler.max_retries', 2)
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 目标URL
        target_url = "https://linux.do/t/topic/690688/48"
        login_url = "https://linux.do/login"
        
        print(f"目标文章: {target_url}")
        print(f"登录页面: {login_url}")
        print()
        
        # 方法1: 手动登录方式（推荐）
        print("=== 方法1: 手动登录方式 ===")
        print("1. 程序将打开浏览器并访问登录页面")
        print("2. 请在浏览器中手动完成登录")
        print("3. 登录完成后，程序将自动采集目标页面")
        print()
        
        input("按回车键开始手动登录演示...")
        
        # 启动浏览器
        api.crawler = api.crawler or api._create_crawler()
        api.crawler.start_browser()
        
        # 访问登录页面
        print("正在打开登录页面...")
        login_html = api.crawler.get_page(login_url)
        print("✓ 登录页面已打开，请在浏览器中完成登录")
        
        # 等待用户手动登录
        input("完成登录后，按回车键继续采集目标页面...")
        
        # 采集目标页面
        print(f"正在采集目标页面: {target_url}")
        article_html = api.crawler.get_page(target_url)
        
        # 提取内容
        result = api.extractor.extract_article(article_html, target_url)
        
        # 显示结果
        print("\n=== 采集结果 ===")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"作者: {result.get('author', 'N/A')}")
        print(f"发布时间: {result.get('publish_time', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        print(f"字数统计: {result.get('word_count', 0)}")
        
        # Linux.do特有信息
        if 'reply_count' in result:
            print(f"回复数: {result['reply_count']}")
        if 'view_count' in result:
            print(f"浏览数: {result['view_count']}")
        if 'category' in result:
            print(f"分类: {result['category']}")
        
        # 保存结果
        output_file = "linux_do_login_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {output_file}")
        
        # 关闭浏览器
        api.crawler.close_browser()
        
        return True
        
    except Exception as e:
        print(f"演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_auto_login():
    """演示自动登录（需要提供用户名密码）"""
    print("\n=== 方法2: 自动登录方式 ===")
    print("注意：需要提供linux.do的用户名和密码")
    print()
    
    # 获取登录凭据
    username = input("请输入linux.do用户名（或按回车跳过）: ").strip()
    if not username:
        print("跳过自动登录演示")
        return False
    
    password = getpass.getpass("请输入密码: ")
    if not password:
        print("跳过自动登录演示")
        return False
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器便于观察
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 登录凭据
        login_credentials = {
            'username': username,
            'password': password,
            'login_url': 'https://linux.do/login',
            'username_selector': '#login-account-name',  # linux.do的用户名输入框
            'password_selector': '#login-account-password',  # 密码输入框
            'submit_selector': '#login-button'  # 登录按钮
        }
        
        # 目标URL
        target_url = "https://linux.do/t/topic/690688/48"
        
        print(f"正在自动登录并采集: {target_url}")
        
        # 采集文章（包含自动登录）
        result = api.crawl_article(
            target_url,
            login_required=True,
            login_credentials=login_credentials
        )
        
        # 显示结果
        print("\n=== 自动登录采集结果 ===")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        
        # 保存结果
        output_file = "linux_do_auto_login_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"自动登录失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_cookie_reuse():
    """演示Cookie复用"""
    print("\n=== 方法3: Cookie复用方式 ===")
    print("如果之前已经登录过，可以复用保存的Cookie")
    print()
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        api = CFCJAPI(config)
        
        # 检查是否有保存的Cookie
        cookie_file = config.cookie_file_path
        if cookie_file.exists():
            print(f"发现已保存的Cookie文件: {cookie_file}")
            
            # 直接尝试采集（使用已保存的Cookie）
            target_url = "https://linux.do/t/topic/690688/48"
            print(f"正在使用已保存的Cookie采集: {target_url}")
            
            result = api.crawl_article(target_url)
            
            print("\n=== Cookie复用采集结果 ===")
            print(f"标题: {result.get('title', 'N/A')}")
            print(f"内容长度: {len(result.get('content', ''))} 字符")
            
            return True
        else:
            print("未找到已保存的Cookie文件")
            print("请先运行手动登录或自动登录演示")
            return False
            
    except Exception as e:
        print(f"Cookie复用失败: {e}")
        return False


def main():
    """主函数"""
    print("CFCJ Linux.do 登录采集演示")
    print("=" * 50)
    print()
    print("本演示将展示如何使用CFCJ采集需要登录的linux.do页面")
    print("提供三种登录方式：")
    print("1. 手动登录（推荐）- 在浏览器中手动完成登录")
    print("2. 自动登录 - 提供用户名密码自动登录")
    print("3. Cookie复用 - 使用之前保存的登录状态")
    print()
    
    # 检查依赖
    try:
        from wz.cfcj.api import CFCJAPI
        print("✓ CFCJ模块加载成功")
    except ImportError as e:
        print(f"✗ CFCJ模块加载失败: {e}")
        return False
    
    print()
    
    # 选择演示方式
    while True:
        print("请选择演示方式:")
        print("1. 手动登录演示")
        print("2. 自动登录演示")
        print("3. Cookie复用演示")
        print("4. 退出")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == '1':
            demo_linux_do_login()
            break
        elif choice == '2':
            demo_auto_login()
            break
        elif choice == '3':
            demo_cookie_reuse()
            break
        elif choice == '4':
            print("退出演示")
            break
        else:
            print("无效选择，请重新输入")
    
    print("\n演示结束！")
    return True


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断演示")
    except Exception as e:
        print(f"演示异常: {e}")
        import traceback
        traceback.print_exc()
