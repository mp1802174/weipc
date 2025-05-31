#!/usr/bin/env python3
"""
CFCJ依赖安装脚本
"""
import subprocess
import sys

def install_package(package):
    """安装Python包"""
    try:
        print(f"正在安装 {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {package} 安装失败: {e}")
        return False

def main():
    """主函数"""
    print("CFCJ 依赖安装脚本")
    print("=" * 40)
    
    # 核心依赖
    core_packages = [
        "beautifulsoup4",
        "lxml", 
        "requests",
        "selenium",
        "undetected-chromedriver",
    ]
    
    # 可选依赖
    optional_packages = [
        "webdriver-manager",
        "fake-useragent",
    ]
    
    print("安装核心依赖...")
    success_count = 0
    for package in core_packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n核心依赖安装结果: {success_count}/{len(core_packages)} 成功")
    
    if success_count == len(core_packages):
        print("\n安装可选依赖...")
        for package in optional_packages:
            install_package(package)
    
    print("\n安装完成！")
    print("运行测试: python test_basic.py")

if __name__ == '__main__':
    main()
