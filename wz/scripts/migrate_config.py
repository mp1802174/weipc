#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目配置迁移脚本
整合现有模块的配置到统一配置系统
"""

import os
import sys
import json
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import UnifiedConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigMigrator:
    """配置迁移器"""
    
    def __init__(self):
        self.project_root = project_root
        self.unified_config = UnifiedConfig()
        
    def migrate_wechat_mp_auth_config(self):
        """迁移wechat_mp_auth模块配置"""
        logger.info("迁移wechat_mp_auth模块配置...")
        
        try:
            # 检查wechat_mp_auth配置
            wechat_auth_config_file = self.project_root / "wechat_mp_auth" / "config.py"
            
            if wechat_auth_config_file.exists():
                # 读取现有配置
                # 这里可以根据实际的配置文件格式进行解析
                logger.info("发现wechat_mp_auth配置文件")
                
                # 更新统一配置
                self.unified_config.auth.cookie_file = "id_info.json"
                self.unified_config.auth.session_timeout = 3600
                self.unified_config.auth.auto_refresh = True
                
                logger.info("wechat_mp_auth配置迁移完成")
            else:
                logger.info("未找到wechat_mp_auth配置文件，使用默认配置")
                
        except Exception as e:
            logger.error(f"迁移wechat_mp_auth配置失败: {e}")
    
    def migrate_cfcj_config(self):
        """迁移CFCJ模块配置"""
        logger.info("迁移CFCJ模块配置...")
        
        try:
            # 检查CFCJ配置文件
            cfcj_config_file = self.project_root / "cfcj" / "data" / "cfcj_config.json"
            
            if cfcj_config_file.exists():
                with open(cfcj_config_file, 'r', encoding='utf-8') as f:
                    cfcj_config = json.load(f)
                
                logger.info("发现CFCJ配置文件")
                
                # 迁移浏览器配置
                if 'browser' in cfcj_config:
                    browser_config = cfcj_config['browser']
                    self.unified_config.cfcj.headless = browser_config.get('headless', True)
                    self.unified_config.cfcj.window_size = tuple(browser_config.get('window_size', [1920, 1080]))
                    self.unified_config.cfcj.user_agent = browser_config.get('user_agent', self.unified_config.cfcj.user_agent)
                    self.unified_config.cfcj.timeout = browser_config.get('timeout', 30)
                    self.unified_config.cfcj.page_load_timeout = browser_config.get('page_load_timeout', 60)
                    self.unified_config.cfcj.implicit_wait = browser_config.get('implicit_wait', 10)
                
                # 迁移爬虫配置
                if 'crawler' in cfcj_config:
                    crawler_config = cfcj_config['crawler']
                    self.unified_config.cfcj.max_retries = crawler_config.get('max_retries', 3)
                    self.unified_config.cfcj.retry_delay = crawler_config.get('retry_delay', 5)
                    self.unified_config.cfcj.cf_wait_time = crawler_config.get('cf_wait_time', 10)
                    self.unified_config.cfcj.request_delay = crawler_config.get('request_delay', 2)
                
                # 迁移认证配置
                if 'auth' in cfcj_config:
                    auth_config = cfcj_config['auth']
                    self.unified_config.auth.cookie_file = auth_config.get('cookie_file', 'cookies.json')
                    self.unified_config.auth.session_timeout = auth_config.get('session_timeout', 3600)
                    self.unified_config.auth.auto_refresh = auth_config.get('auto_login', True)
                
                logger.info("CFCJ配置迁移完成")
            else:
                logger.info("未找到CFCJ配置文件，使用默认配置")
                
        except Exception as e:
            logger.error(f"迁移CFCJ配置失败: {e}")
    
    def migrate_wzzq_config(self):
        """迁移WZZQ模块配置"""
        logger.info("迁移WZZQ模块配置...")
        
        try:
            # WZZQ模块主要使用数据库配置，从DatabaseManager中获取
            from wzzq.db import DatabaseManager
            
            # 创建数据库管理器实例来获取配置
            db_manager = DatabaseManager()
            
            # 更新数据库配置
            self.unified_config.database.host = db_manager.config.get('host', '140.238.201.162')
            self.unified_config.database.port = db_manager.config.get('port', 3306)
            self.unified_config.database.user = db_manager.config.get('user', 'cj')
            self.unified_config.database.password = db_manager.config.get('password', '760516')
            self.unified_config.database.database = db_manager.config.get('database', 'cj')
            self.unified_config.database.charset = db_manager.config.get('charset', 'utf8mb4')
            
            # 设置微信相关配置
            self.unified_config.wechat.enabled = True
            self.unified_config.wechat.batch_size = 10
            self.unified_config.wechat.retry_times = 3
            
            logger.info("WZZQ配置迁移完成")
            
        except Exception as e:
            logger.error(f"迁移WZZQ配置失败: {e}")
    
    def migrate_ye_config(self):
        """迁移YE模块配置"""
        logger.info("迁移YE模块配置...")
        
        try:
            # 检查YE模块的app.py文件中的配置
            ye_app_file = self.project_root / "YE" / "app.py"
            
            if ye_app_file.exists():
                # 读取app.py文件内容
                with open(ye_app_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取配置信息（简单的字符串匹配）
                if "app.config['SECRET_KEY']" in content:
                    # 可以进一步解析具体的配置值
                    pass
                
                # 设置Web配置
                self.unified_config.web.host = "0.0.0.0"
                self.unified_config.web.port = 5000
                self.unified_config.web.debug = False
                self.unified_config.web.secret_key = "wz_project_secret_key"
                
                logger.info("YE配置迁移完成")
            else:
                logger.info("未找到YE配置文件，使用默认配置")
                
        except Exception as e:
            logger.error(f"迁移YE配置失败: {e}")
    
    def migrate_data_files(self):
        """迁移数据文件路径"""
        logger.info("检查和迁移数据文件...")
        
        try:
            # 检查现有数据文件
            data_dir = self.project_root / "data"
            
            if data_dir.exists():
                logger.info(f"发现数据目录: {data_dir}")
                
                # 检查id_info.json
                id_info_file = data_dir / "id_info.json"
                if id_info_file.exists():
                    logger.info("发现微信认证文件: id_info.json")
                    self.unified_config.auth.cookie_file = "id_info.json"
                
                # 检查name2fakeid.json
                accounts_file = data_dir / "name2fakeid.json"
                if accounts_file.exists():
                    logger.info("发现微信账号文件: name2fakeid.json")
                    self.unified_config.wechat.accounts_file = "name2fakeid.json"
            
            # 确保数据目录存在
            self.unified_config.get_data_path().mkdir(parents=True, exist_ok=True)
            self.unified_config.get_logs_path().mkdir(parents=True, exist_ok=True)
            self.unified_config.get_temp_path().mkdir(parents=True, exist_ok=True)
            
            logger.info("数据文件迁移完成")
            
        except Exception as e:
            logger.error(f"迁移数据文件失败: {e}")
    
    def create_environment_config(self):
        """创建环境配置文件"""
        logger.info("创建环境配置文件...")
        
        try:
            # 创建开发环境配置
            dev_config = self.unified_config.to_dict()
            dev_config['system']['debug'] = True
            dev_config['system']['log_level'] = 'DEBUG'
            dev_config['web']['debug'] = True
            
            dev_config_file = self.project_root / "config" / "config.dev.json"
            with open(dev_config_file, 'w', encoding='utf-8') as f:
                json.dump(dev_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"开发环境配置已创建: {dev_config_file}")
            
            # 创建生产环境配置
            prod_config = self.unified_config.to_dict()
            prod_config['system']['debug'] = False
            prod_config['system']['log_level'] = 'INFO'
            prod_config['web']['debug'] = False
            prod_config['web']['secret_key'] = "CHANGE_THIS_IN_PRODUCTION"
            
            prod_config_file = self.project_root / "config" / "config.prod.json"
            with open(prod_config_file, 'w', encoding='utf-8') as f:
                json.dump(prod_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"生产环境配置已创建: {prod_config_file}")
            
        except Exception as e:
            logger.error(f"创建环境配置失败: {e}")
    
    def validate_migrated_config(self):
        """验证迁移后的配置"""
        logger.info("验证迁移后的配置...")
        
        try:
            errors = self.unified_config.validate_config()
            
            if errors:
                logger.warning("配置验证发现问题:")
                for section, error_list in errors.items():
                    for error in error_list:
                        logger.warning(f"  [{section}] {error}")
            else:
                logger.info("配置验证通过")
            
            return len(errors) == 0
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def run_migration(self):
        """执行完整的配置迁移"""
        logger.info("开始配置迁移...")
        
        try:
            # 1. 迁移各模块配置
            self.migrate_wzzq_config()
            self.migrate_cfcj_config()
            self.migrate_wechat_mp_auth_config()
            self.migrate_ye_config()
            
            # 2. 迁移数据文件
            self.migrate_data_files()
            
            # 3. 保存统一配置
            if self.unified_config.save_config():
                logger.info("统一配置已保存")
            else:
                logger.error("保存统一配置失败")
                return False
            
            # 4. 创建环境配置
            self.create_environment_config()
            
            # 5. 验证配置
            if self.validate_migrated_config():
                logger.info("配置迁移完成并验证通过")
                return True
            else:
                logger.warning("配置迁移完成但验证有问题")
                return False
                
        except Exception as e:
            logger.error(f"配置迁移失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("WZ项目配置迁移工具")
    print("=" * 60)
    
    migrator = ConfigMigrator()
    
    try:
        success = migrator.run_migration()
        
        if success:
            print("\n" + "=" * 60)
            print("配置迁移完成！")
            print("=" * 60)
            print("已创建以下配置文件:")
            print("- config/config.json (默认配置)")
            print("- config/config.dev.json (开发环境)")
            print("- config/config.prod.json (生产环境)")
            print("\n建议下一步:")
            print("1. 检查配置文件内容")
            print("2. 根据实际环境调整配置")
            print("3. 更新各模块代码使用统一配置")
        else:
            print("\n配置迁移失败，请检查日志")
        
        return success
        
    except Exception as e:
        logger.error(f"配置迁移过程中发生错误: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
