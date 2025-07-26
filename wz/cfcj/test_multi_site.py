"""
多站点功能测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from wz.cfcj.core.site_detector import SiteDetector
from wz.cfcj.core.multi_site_extractor import MultiSiteExtractor
from wz.cfcj.auth.multi_site_auth import MultiSiteAuthManager
from wz.cfcj.config.settings import CFCJConfig


def test_site_detection():
    """测试站点识别功能"""
    print("=== 测试站点识别功能 ===")
    
    config = CFCJConfig()
    detector = SiteDetector(config)
    
    test_urls = [
        "https://linux.do/t/topic/694091",
        "https://www.nodeseek.com/post-355294-1", 
        "https://mp.weixin.qq.com/s/IMVROkN8-u9k2MTtgH3a2w",
        "https://example.com/unknown-site"
    ]
    
    for url in test_urls:
        print(f"\n测试URL: {url}")
        site_info = detector.detect_site(url)
        
        if site_info:
            print(f"  ✓ 识别为: {site_info['site_name']}")
            print(f"  域名: {site_info['domain']}")
            print(f"  需要登录: {site_info['requires_login']}")
            if site_info['requires_login']:
                login_config = site_info.get('login_config', {})
                print(f"  登录URL: {login_config.get('login_url', 'N/A')}")
        else:
            print(f"  ✗ 不支持的站点")


def test_supported_sites():
    """测试支持的站点列表"""
    print("\n=== 支持的站点列表 ===")
    
    config = CFCJConfig()
    detector = SiteDetector(config)
    
    supported_sites = detector.get_supported_sites()
    
    for domain, name in supported_sites.items():
        site_config = detector.get_site_config(domain)
        requires_login = site_config.get('requires_login', False) if site_config else False
        print(f"  • {name} ({domain}) - {'需要登录' if requires_login else '无需登录'}")


def test_login_detection():
    """测试登录需求检测"""
    print("\n=== 测试登录需求检测 ===")
    
    config = CFCJConfig()
    auth_manager = MultiSiteAuthManager(config)
    
    test_urls = [
        "https://linux.do/t/topic/694091",
        "https://www.nodeseek.com/post-355294-1", 
        "https://mp.weixin.qq.com/s/IMVROkN8-u9k2MTtgH3a2w"
    ]
    
    for url in test_urls:
        requires_login = auth_manager.is_login_required(url)
        print(f"  {url} - {'需要登录' if requires_login else '无需登录'}")


def test_extraction_config():
    """测试提取配置"""
    print("\n=== 测试提取配置 ===")
    
    config = CFCJConfig()
    detector = SiteDetector(config)
    
    test_urls = [
        "https://linux.do/t/topic/694091",
        "https://www.nodeseek.com/post-355294-1", 
        "https://mp.weixin.qq.com/s/IMVROkN8-u9k2MTtgH3a2w"
    ]
    
    for url in test_urls:
        site_info = detector.detect_site(url)
        if site_info:
            extraction = site_info.get('extraction', {})
            print(f"\n{site_info['site_name']} 提取配置:")
            print(f"  标题选择器: {len(extraction.get('title_selectors', []))} 个")
            print(f"  内容选择器: {len(extraction.get('content_selectors', []))} 个")
            print(f"  排除选择器: {len(extraction.get('exclude_selectors', []))} 个")


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    config = CFCJConfig()
    detector = SiteDetector(config)
    
    # 测试有效配置
    valid_config = {
        'domain': 'test.com',
        'requires_login': True,
        'login_config': {
            'login_url': 'https://test.com/login',
            'username_selector': 'input[name="username"]',
            'password_selector': 'input[name="password"]',
            'submit_selector': 'button[type="submit"]'
        },
        'extraction': {
            'title_selectors': ['h1'],
            'content_selectors': ['.content']
        }
    }
    
    is_valid = detector.validate_site_config(valid_config)
    print(f"  有效配置验证: {'✓ 通过' if is_valid else '✗ 失败'}")
    
    # 测试无效配置
    invalid_config = {
        'domain': 'test.com'
        # 缺少必需字段
    }
    
    is_valid = detector.validate_site_config(invalid_config)
    print(f"  无效配置验证: {'✗ 正确拒绝' if not is_valid else '✓ 错误通过'}")


def main():
    """主函数"""
    print("CFCJ 多站点功能测试")
    print("=" * 50)
    
    try:
        test_site_detection()
        test_supported_sites()
        test_login_detection()
        test_extraction_config()
        test_config_validation()
        
        print("\n" + "=" * 50)
        print("✓ 所有测试完成")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
