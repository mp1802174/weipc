#!/usr/bin/env python3
"""
CFCJ基础功能测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_config():
    """测试配置模块"""
    print("测试配置模块...")
    try:
        from wz.cfcj.config.settings import CFCJConfig
        config = CFCJConfig()
        print(f"✓ 配置模块加载成功")
        print(f"  默认无头模式: {config.get('browser.headless')}")
        print(f"  最大重试次数: {config.get('crawler.max_retries')}")
        print(f"  配置文件路径: {config.config_file}")
        return True
    except Exception as e:
        print(f"✗ 配置模块测试失败: {e}")
        return False

def test_extractor():
    """测试内容提取模块"""
    print("\n测试内容提取模块...")
    try:
        from wz.cfcj.core.extractor import ContentExtractor
        extractor = ContentExtractor()
        
        # 测试HTML解析
        html = """
        <html>
        <head><title>Test Title</title></head>
        <body>
            <h1>Test Article</h1>
            <div class="content">Test content</div>
        </body>
        </html>
        """
        
        result = extractor.extract_article(html, "https://example.com/test")
        print(f"✓ 内容提取模块加载成功")
        print(f"  提取的标题: {result.get('title', 'N/A')}")
        print(f"  提取的内容: {result.get('content', 'N/A')[:50]}...")
        return True
    except Exception as e:
        print(f"✗ 内容提取模块测试失败: {e}")
        return False

def test_auth():
    """测试认证模块"""
    print("\n测试认证模块...")
    try:
        from wz.cfcj.auth.manager import AuthManager
        from wz.cfcj.config.settings import CFCJConfig
        
        config = CFCJConfig()
        auth = AuthManager(config)
        print(f"✓ 认证模块加载成功")
        print(f"  Cookie文件路径: {config.cookie_file_path}")
        return True
    except Exception as e:
        print(f"✗ 认证模块测试失败: {e}")
        return False

def test_api():
    """测试API模块"""
    print("\n测试API模块...")
    try:
        from wz.cfcj.api import CFCJAPI
        api = CFCJAPI()
        print(f"✓ API模块加载成功")
        print(f"  配置对象: {type(api.config)}")
        print(f"  认证管理器: {type(api.auth_manager)}")
        print(f"  内容提取器: {type(api.extractor)}")
        return True
    except Exception as e:
        print(f"✗ API模块测试失败: {e}")
        return False

def test_dependencies():
    """测试依赖项"""
    print("\n检查依赖项...")
    
    dependencies = [
        ("beautifulsoup4", "bs4", "BeautifulSoup"),
        ("lxml", "lxml", "etree"),
        ("requests", "requests", "get"),
        ("undetected-chromedriver", "undetected_chromedriver", "Chrome"),
        ("DrissionPage", "DrissionPage", "ChromiumPage"),
        ("selenium", "selenium", "webdriver"),
    ]
    
    available = []
    missing = []
    
    for name, module, attr in dependencies:
        try:
            mod = __import__(module)
            if hasattr(mod, attr):
                available.append(name)
                print(f"✓ {name} 可用")
            else:
                missing.append(name)
                print(f"✗ {name} 不完整")
        except ImportError:
            missing.append(name)
            print(f"✗ {name} 未安装")
    
    print(f"\n依赖项检查结果:")
    print(f"  可用: {len(available)}/{len(dependencies)}")
    print(f"  缺失: {missing if missing else '无'}")
    
    return len(missing) == 0

def main():
    """主测试函数"""
    print("CFCJ 基础功能测试")
    print("=" * 40)
    
    tests = [
        ("依赖项检查", test_dependencies),
        ("配置模块", test_config),
        ("内容提取模块", test_extractor),
        ("认证模块", test_auth),
        ("API模块", test_api),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"\n{'='*20} {name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✓ {name} 测试通过")
            else:
                print(f"✗ {name} 测试失败")
        except Exception as e:
            print(f"✗ {name} 测试异常: {e}")
    
    print(f"\n{'='*40}")
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！CFCJ模块基础功能正常。")
    else:
        print("⚠️  部分测试失败，请检查依赖项和模块代码。")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
