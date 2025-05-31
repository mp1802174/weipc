#!/usr/bin/env python3
"""
CFCJ自动登录测试脚本
自动登录linux.do并保存Cookie，然后采集目标页面
"""
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def auto_login_and_crawl():
    """自动登录并采集"""
    print("=== CFCJ 自动登录采集测试 ===")
    print("将自动登录linux.do并采集目标页面")
    print()
    
    # 登录凭据
    username = "l516q"
    password = "Pp1112131@"
    login_url = "https://linux.do/login"
    target_url = "https://linux.do/t/topic/690688/48"
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置 - 显示浏览器便于观察登录过程
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器便于观察
        config.set('crawler.cf_wait_time', 20)  # 增加CF等待时间
        config.set('crawler.max_retries', 3)
        config.set('crawler.request_delay', 3)  # 增加请求间隔
        
        # 创建API实例
        api = CFCJAPI(config)
        
        print(f"登录信息:")
        print(f"  用户名: {username}")
        print(f"  登录URL: {login_url}")
        print(f"  目标URL: {target_url}")
        print()
        
        # 准备登录凭据
        login_credentials = {
            'username': username,
            'password': password,
            'login_url': login_url,
            # linux.do的登录表单选择器
            'username_selector': '#login-account-name',
            'password_selector': '#login-account-password', 
            'submit_selector': '#login-button'
        }
        
        print("1. 开始自动登录并采集...")
        
        # 使用API进行自动登录采集
        result = api.crawl_article(
            target_url,
            login_required=True,
            login_credentials=login_credentials
        )
        
        print("2. 采集完成！")
        print()
        
        # 显示采集结果
        print("=== 采集结果 ===")
        print(f"URL: {result.get('url', 'N/A')}")
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
        
        # 显示提取的标签
        if result.get('tags'):
            print(f"标签: {', '.join(result['tags'])}")
        
        # 显示图片数量
        if result.get('images'):
            print(f"图片数量: {len(result['images'])}")
        
        # 显示链接数量
        if result.get('links'):
            print(f"链接数量: {len(result['links'])}")
        
        print()
        
        # 保存完整结果到cfcj目录
        cfcj_dir = Path(__file__).parent
        output_file = cfcj_dir / "auto_login_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✓ 完整结果已保存到: {output_file}")
        
        # 显示内容预览
        content = result.get('content', '')
        if content:
            print(f"\n=== 内容预览 ===")
            preview_length = 500
            if len(content) > preview_length:
                print(content[:preview_length] + "...")
                print(f"[内容已截断，完整内容请查看 {output_file}]")
            else:
                print(content)
        
        # 检查Cookie保存状态
        cookie_file = config.cookie_file_path
        if cookie_file.exists():
            print(f"\n✓ 登录Cookie已保存到: {cookie_file}")
            print("下次可以直接使用保存的Cookie进行采集")
        else:
            print("\n⚠️ Cookie保存可能失败")
        
        return True
        
    except Exception as e:
        print(f"✗ 自动登录采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cookie_reuse():
    """测试Cookie复用"""
    print("\n=== 测试Cookie复用 ===")
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        config.set('browser.headless', True)  # 无头模式测试
        
        # 检查Cookie文件
        cookie_file = config.cookie_file_path
        if not cookie_file.exists():
            print("Cookie文件不存在，请先运行自动登录")
            return False
        
        print(f"发现Cookie文件: {cookie_file}")
        
        api = CFCJAPI(config)
        target_url = "https://linux.do/t/topic/690688/48"
        
        print(f"使用保存的Cookie采集: {target_url}")
        
        # 直接采集（不需要登录，使用保存的Cookie）
        result = api.crawl_article(target_url)
        
        print("Cookie复用采集成功！")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        
        # 保存复用结果到cfcj目录
        cfcj_dir = Path(__file__).parent
        output_file = cfcj_dir / "cookie_reuse_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Cookie复用测试失败: {e}")
        return False


def main():
    """主函数"""
    print("CFCJ 自动登录功能测试")
    print("=" * 50)
    print()
    
    # 步骤1: 自动登录并采集
    print("步骤1: 自动登录并采集目标页面")
    success1 = auto_login_and_crawl()
    
    if success1:
        print("\n" + "="*50)
        
        # 步骤2: 测试Cookie复用
        print("步骤2: 测试Cookie复用功能")
        success2 = test_cookie_reuse()
        
        if success2:
            print("\n🎉 所有测试完成！")
            print("✓ 自动登录功能正常")
            print("✓ Cookie保存功能正常") 
            print("✓ Cookie复用功能正常")
            print("✓ 内容采集功能正常")
        else:
            print("\n⚠️ Cookie复用测试失败，但自动登录功能正常")
    else:
        print("\n❌ 自动登录测试失败")
    
    print("\n测试结束")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
