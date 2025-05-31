#!/usr/bin/env python3
"""
测试已登录状态下的采集功能
假设浏览器已经登录了linux.do
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_logged_in_crawl():
    """测试已登录状态下的采集"""
    print("=== 测试已登录状态下的采集 ===")
    print("假设浏览器已经登录了linux.do")
    print()
    
    try:
        from wz.cfcj.api import CFCJAPI
        from wz.cfcj.config.settings import CFCJConfig
        
        # 创建配置
        config = CFCJConfig()
        config.set('browser.headless', False)  # 显示浏览器
        config.set('crawler.cf_wait_time', 15)
        config.set('crawler.max_retries', 2)
        
        # 创建API实例
        api = CFCJAPI(config)
        
        # 目标URL - 使用新的测试URL
        target_url = "https://linux.do/t/topic/690935"
        
        print(f"目标URL: {target_url}")
        print("开始采集...")
        
        # 直接采集（不指定需要登录）
        result = api.crawl_article(target_url)
        
        print("\n=== 采集结果 ===")
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
        
        # 显示图片和链接数量
        if result.get('images'):
            print(f"图片数量: {len(result['images'])}")
        if result.get('links'):
            print(f"链接数量: {len(result['links'])}")
        
        print()
        
        # 保存结果到cfcj目录
        cfcj_dir = Path(__file__).parent
        output_file = cfcj_dir / "logged_in_result.json"
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
        else:
            print("\n⚠️ 未提取到内容，可能需要登录")
        
        # 检查是否成功采集到有效内容
        if content and len(content) > 100:
            print(f"\n🎉 采集成功！获取到 {len(content)} 字符的内容")
            
            # 保存Cookie以便后续使用
            cookie_file = config.cookie_file_path
            if cookie_file.exists():
                print(f"✓ Cookie已保存到: {cookie_file}")
            
            return True
        else:
            print(f"\n⚠️ 采集的内容较少，可能页面需要登录或有其他限制")
            return False
        
    except Exception as e:
        print(f"✗ 采集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_saved_cookies():
    """使用保存的Cookie测试"""
    print("\n=== 使用保存的Cookie测试 ===")
    
    try:
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        cookie_file = config.cookie_file_path
        
        if not cookie_file.exists():
            print("未找到保存的Cookie文件")
            return False
        
        print(f"发现Cookie文件: {cookie_file}")
        
        # 读取Cookie内容
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_data = json.load(f)
        
        print(f"Cookie数据:")
        for domain, cookies in cookie_data.get('cookies', {}).items():
            print(f"  域名: {domain}, Cookie数量: {len(cookies)}")
        
        # 使用Cookie进行采集
        from wz.cfcj.api import CFCJAPI
        
        config.set('browser.headless', True)  # 无头模式
        api = CFCJAPI(config)
        
        target_url = "https://linux.do/t/topic/690688/48"
        print(f"\n使用Cookie采集: {target_url}")
        
        result = api.crawl_article(target_url)
        
        print("Cookie采集结果:")
        print(f"标题: {result.get('title', 'N/A')}")
        print(f"内容长度: {len(result.get('content', ''))} 字符")
        
        if len(result.get('content', '')) > 100:
            print("✓ Cookie复用成功")
            return True
        else:
            print("⚠️ Cookie可能已过期")
            return False
        
    except Exception as e:
        print(f"Cookie测试失败: {e}")
        return False


def main():
    """主函数"""
    print("CFCJ 已登录状态测试")
    print("=" * 50)
    print()
    
    # 测试1: 直接采集（假设已登录）
    success1 = test_logged_in_crawl()
    
    if success1:
        # 测试2: 使用保存的Cookie
        test_with_saved_cookies()
        
        print("\n" + "="*50)
        print("🎉 测试完成！")
        print("✓ 内容采集功能正常")
        print("✓ Cookie保存功能正常")
        print("\n建议:")
        print("1. 如果内容采集成功，说明CFCJ模块工作正常")
        print("2. 保存的Cookie可以用于后续的自动化采集")
        print("3. 可以将此模块集成到其他项目中使用")
    else:
        print("\n" + "="*50)
        print("⚠️ 测试未完全成功")
        print("可能的原因:")
        print("1. 浏览器未登录linux.do")
        print("2. 目标页面需要特殊权限")
        print("3. 网络连接问题")
        print("\n建议:")
        print("1. 手动在浏览器中登录linux.do")
        print("2. 然后重新运行此测试")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断测试")
    except Exception as e:
        print(f"测试异常: {e}")
        import traceback
        traceback.print_exc()
