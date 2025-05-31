#!/usr/bin/env python3
"""
修复CFCJ模块的cookies问题
解决"HEARD cookie too long"错误
"""

import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def backup_cookies(cookie_file: Path) -> Path:
    """备份原始cookies文件"""
    backup_file = cookie_file.with_suffix('.backup.json')
    if cookie_file.exists():
        import shutil
        shutil.copy2(cookie_file, backup_file)
        return backup_file
    return None

def analyze_cookies(cookie_file: Path, logger):
    """分析cookies文件中的问题"""
    if not cookie_file.exists():
        logger.info("Cookies文件不存在")
        return None
    
    try:
        with open(cookie_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cookies = data.get('cookies', {})
        
        logger.info(f"=== Cookies文件分析 ===")
        logger.info(f"文件大小: {cookie_file.stat().st_size} 字节")
        logger.info(f"域名数量: {len(cookies)}")
        
        total_cookies = 0
        invalid_cookies = 0
        oversized_cookies = 0
        
        for domain, domain_cookies in cookies.items():
            if not isinstance(domain_cookies, list):
                logger.warning(f"域名 {domain}: cookies格式无效 (不是列表)")
                invalid_cookies += 1
                continue
            
            domain_cookie_count = len(domain_cookies)
            total_cookies += domain_cookie_count
            
            logger.info(f"域名 {domain}: {domain_cookie_count} 个cookies")
            
            for i, cookie in enumerate(domain_cookies):
                if not isinstance(cookie, dict):
                    logger.warning(f"  Cookie {i}: 格式无效 (不是字典)")
                    invalid_cookies += 1
                    continue
                
                name = cookie.get('name', '')
                value = cookie.get('value', '')
                
                # 检查cookie名称是否有问题
                if any(char in str(name) for char in ['{', '}', '"', "'"]):
                    logger.warning(f"  Cookie {i}: 名称包含无效字符 - {name[:50]}...")
                    invalid_cookies += 1
                
                # 检查cookie值长度
                if len(str(value)) > 4096:
                    logger.warning(f"  Cookie {i}: 值过长 ({len(str(value))} 字符) - {name}")
                    oversized_cookies += 1
        
        logger.info(f"总计: {total_cookies} 个cookies")
        logger.info(f"无效cookies: {invalid_cookies} 个")
        logger.info(f"过大cookies: {oversized_cookies} 个")
        
        return {
            'total': total_cookies,
            'invalid': invalid_cookies,
            'oversized': oversized_cookies,
            'data': data
        }
        
    except Exception as e:
        logger.error(f"分析cookies文件失败: {e}")
        return None

def fix_cookies_file(cookie_file: Path, logger):
    """修复cookies文件"""
    # 备份原文件
    backup_file = backup_cookies(cookie_file)
    if backup_file:
        logger.info(f"已备份原文件到: {backup_file}")
    
    # 分析问题
    analysis = analyze_cookies(cookie_file, logger)
    if not analysis:
        return False
    
    if analysis['invalid'] == 0 and analysis['oversized'] == 0:
        logger.info("✅ Cookies文件没有发现问题")
        return True
    
    logger.info(f"开始修复cookies文件...")
    
    try:
        from wz.cfcj.config.settings import CFCJConfig
        from wz.cfcj.auth.manager import AuthManager
        
        # 创建AuthManager实例
        config = CFCJConfig()
        auth_manager = AuthManager(config)
        
        # 加载原始数据
        auth_manager.cookies = analysis['data'].get('cookies', {})
        auth_manager.session_data = analysis['data'].get('session_data', {})
        
        # 执行清理
        auth_manager.clean_cookies()
        
        # 保存清理后的数据
        auth_manager.save_auth_data()
        
        logger.info("✅ Cookies文件修复完成")
        
        # 重新分析验证
        new_analysis = analyze_cookies(cookie_file, logger)
        if new_analysis:
            logger.info(f"修复后: {new_analysis['total']} 个cookies, {new_analysis['invalid']} 个无效, {new_analysis['oversized']} 个过大")
        
        return True
        
    except Exception as e:
        logger.error(f"修复cookies文件失败: {e}")
        return False

def clear_cookies_completely(cookie_file: Path, logger):
    """完全清除cookies文件"""
    try:
        if cookie_file.exists():
            backup_file = backup_cookies(cookie_file)
            if backup_file:
                logger.info(f"已备份原文件到: {backup_file}")
            
            cookie_file.unlink()
            logger.info("✅ Cookies文件已完全清除")
            return True
        else:
            logger.info("Cookies文件不存在，无需清除")
            return True
    except Exception as e:
        logger.error(f"清除cookies文件失败: {e}")
        return False

def main():
    """主函数"""
    logger = setup_logging()
    
    print("CFCJ Cookies修复工具")
    print("=" * 50)
    
    try:
        from wz.cfcj.config.settings import CFCJConfig
        config = CFCJConfig()
        cookie_file = config.cookie_file_path
        
        print(f"Cookies文件路径: {cookie_file}")
        
        if not cookie_file.exists():
            print("✅ Cookies文件不存在，无需修复")
            return
        
        print("\n请选择操作:")
        print("1. 分析cookies文件")
        print("2. 修复cookies文件")
        print("3. 完全清除cookies文件")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            print("\n=== 分析Cookies文件 ===")
            analyze_cookies(cookie_file, logger)
            
        elif choice == '2':
            print("\n=== 修复Cookies文件 ===")
            success = fix_cookies_file(cookie_file, logger)
            if success:
                print("✅ 修复完成！现在可以重新测试CFCJ模块。")
            else:
                print("❌ 修复失败！")
                
        elif choice == '3':
            confirm = input("确认要完全清除cookies文件吗？(y/N): ").strip().lower()
            if confirm == 'y':
                print("\n=== 清除Cookies文件 ===")
                success = clear_cookies_completely(cookie_file, logger)
                if success:
                    print("✅ 清除完成！下次使用时会重新生成cookies。")
                else:
                    print("❌ 清除失败！")
            else:
                print("操作已取消")
                
        elif choice == '4':
            print("退出")
            
        else:
            print("无效选择")
            
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        import traceback
        logger.error(f"详细错误:\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()
