#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目统一配置管理模块
整合所有子模块的配置，提供统一的配置接口
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ConfigType(Enum):
    """配置类型枚举"""
    SYSTEM = "system"
    DATABASE = "database"
    WECHAT = "wechat"
    CFCJ = "cfcj"
    PUBLISHER = "publisher"
    AUTH = "auth"
    WEB = "web"

@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = ""
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = ""
    charset: str = "utf8mb4"
    autocommit: bool = True

    def __post_init__(self):
        """从配置文件加载数据库配置"""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
            from config_manager import get_database_config

            config = get_database_config('wz_database')
            self.host = config.get('host', '')
            self.port = config.get('port', 3306)
            self.user = config.get('user', '')
            self.password = config.get('password', '')
            self.database = config.get('database', '')
            self.charset = config.get('charset', 'utf8mb4')
        except Exception:
            # 如果配置加载失败，保持默认空值
            pass
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

@dataclass
class WechatConfig:
    """微信公众号配置"""
    enabled: bool = True
    batch_size: int = 10
    retry_times: int = 3
    retry_delay: int = 5
    request_delay: int = 2
    auto_login: bool = True
    session_timeout: int = 3600
    cookie_file: str = "id_info.json"
    accounts_file: str = "name2fakeid.json"

@dataclass
class CFCJConfig:
    """CFCJ内容采集配置"""
    enabled: bool = True
    headless: bool = True
    window_size: tuple = (1920, 1080)
    timeout: int = 30
    page_load_timeout: int = 60
    implicit_wait: int = 10
    max_retries: int = 3
    retry_delay: int = 5
    cf_wait_time: int = 10
    request_delay: int = 2
    batch_size: int = 5
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

@dataclass
class PublisherConfig:
    """发布模块配置"""
    enabled: bool = False
    auto_publish: bool = False
    batch_size: int = 5
    retry_times: int = 3
    retry_delay: int = 10
    platforms: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.platforms is None:
            self.platforms = {
                "8wf_net": {
                    "enabled": False,
                    "type": "discuz",
                    "url": "https://8wf.net",
                    "username": "",
                    "password": "",
                    "default_forum_id": "1",
                    "auto_category": True
                },
                "00077_top": {
                    "enabled": False,
                    "type": "discourse",
                    "url": "https://00077.top",
                    "api_key": "",
                    "api_username": "",
                    "default_category": "1"
                },
                "1rmb_net": {
                    "enabled": False,
                    "type": "discuz",
                    "url": "https://1rmb.net",
                    "username": "",
                    "password": "",
                    "default_forum_id": "1",
                    "auto_category": True
                }
            }

@dataclass
class AuthConfig:
    """认证配置"""
    cookie_file: str = "cookies.json"
    session_timeout: int = 3600
    auto_refresh: bool = True
    encryption_key: str = ""
    
@dataclass
class WebConfig:
    """Web界面配置"""
    host: str = "0.0.0.0"
    port: int = 5000
    debug: bool = False
    secret_key: str = "wz_project_secret_key"
    auto_crawl_interval: int = 3600
    max_log_size: int = 5 * 1024 * 1024  # 5MB
    log_backup_count: int = 3

@dataclass
class SystemConfig:
    """系统配置"""
    project_name: str = "WZ Content Management System"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    data_dir: str = "data"
    logs_dir: str = "logs"
    temp_dir: str = "temp"
    timezone: str = "Asia/Shanghai"
    language: str = "zh_CN"

class UnifiedConfig:
    """统一配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        self.project_root = Path(__file__).parent.parent
        self.config_file = config_file or self.project_root / "config" / "config.json"
        
        # 初始化各模块配置
        self.system = SystemConfig()
        self.database = DatabaseConfig()
        self.wechat = WechatConfig()
        self.cfcj = CFCJConfig()
        self.publisher = PublisherConfig()
        self.auth = AuthConfig()
        self.web = WebConfig()
        
        # 确保配置目录存在
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> bool:
        """
        从文件加载配置
        
        Returns:
            bool: 是否成功加载
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # 更新各模块配置
                self._update_config_from_dict(config_data)
                logger.info(f"配置已从 {self.config_file} 加载")
                return True
            else:
                logger.info("配置文件不存在，使用默认配置")
                self.save_config()  # 保存默认配置
                return True
                
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return False
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 是否成功保存
        """
        try:
            config_data = {
                "system": asdict(self.system),
                "database": asdict(self.database),
                "wechat": asdict(self.wechat),
                "cfcj": asdict(self.cfcj),
                "publisher": asdict(self.publisher),
                "auth": asdict(self.auth),
                "web": asdict(self.web)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存到 {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def _update_config_from_dict(self, config_data: Dict[str, Any]):
        """从字典更新配置"""
        for section_name, section_data in config_data.items():
            if hasattr(self, section_name) and isinstance(section_data, dict):
                config_obj = getattr(self, section_name)
                for key, value in section_data.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，格式为 "section.key"
            default: 默认值
            
        Returns:
            配置值
        """
        try:
            parts = key.split('.')
            if len(parts) != 2:
                return default
            
            section_name, config_key = parts
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                return getattr(section, config_key, default)
            
            return default
            
        except Exception:
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，格式为 "section.key"
            value: 配置值
            
        Returns:
            bool: 是否成功设置
        """
        try:
            parts = key.split('.')
            if len(parts) != 2:
                return False
            
            section_name, config_key = parts
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                if hasattr(section, config_key):
                    setattr(section, config_key, value)
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        db = self.database
        return f"mysql://{db.user}:{db.password}@{db.host}:{db.port}/{db.database}?charset={db.charset}"
    
    def get_data_path(self, filename: str = "") -> Path:
        """获取数据文件路径"""
        data_dir = self.project_root / self.system.data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / filename if filename else data_dir
    
    def get_logs_path(self, filename: str = "") -> Path:
        """获取日志文件路径"""
        logs_dir = self.project_root / self.system.logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir / filename if filename else logs_dir
    
    def get_temp_path(self, filename: str = "") -> Path:
        """获取临时文件路径"""
        temp_dir = self.project_root / self.system.temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir / filename if filename else temp_dir
    
    def validate_config(self) -> Dict[str, list]:
        """
        验证配置的有效性
        
        Returns:
            Dict[str, list]: 验证结果，键为配置段名，值为错误列表
        """
        errors = {}
        
        # 验证数据库配置
        db_errors = []
        if not self.database.host:
            db_errors.append("数据库主机不能为空")
        if not (1 <= self.database.port <= 65535):
            db_errors.append("数据库端口必须在1-65535之间")
        if not self.database.user:
            db_errors.append("数据库用户名不能为空")
        if not self.database.database:
            db_errors.append("数据库名不能为空")
        if db_errors:
            errors["database"] = db_errors
        
        # 验证Web配置
        web_errors = []
        if not (1 <= self.web.port <= 65535):
            web_errors.append("Web端口必须在1-65535之间")
        if not self.web.secret_key:
            web_errors.append("Web密钥不能为空")
        if web_errors:
            errors["web"] = web_errors
        
        # 验证CFCJ配置
        cfcj_errors = []
        if self.cfcj.timeout <= 0:
            cfcj_errors.append("超时时间必须大于0")
        if self.cfcj.max_retries < 0:
            cfcj_errors.append("重试次数不能为负数")
        if cfcj_errors:
            errors["cfcj"] = cfcj_errors
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "system": asdict(self.system),
            "database": asdict(self.database),
            "wechat": asdict(self.wechat),
            "cfcj": asdict(self.cfcj),
            "publisher": asdict(self.publisher),
            "auth": asdict(self.auth),
            "web": asdict(self.web)
        }
    
    def from_dict(self, config_data: Dict[str, Any]):
        """从字典更新配置"""
        self._update_config_from_dict(config_data)
    
    def reset_to_defaults(self):
        """重置为默认配置"""
        self.system = SystemConfig()
        self.database = DatabaseConfig()
        self.wechat = WechatConfig()
        self.cfcj = CFCJConfig()
        self.publisher = PublisherConfig()
        self.auth = AuthConfig()
        self.web = WebConfig()

# 全局配置实例
_global_config = None

def get_config() -> UnifiedConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = UnifiedConfig()
    return _global_config

def reload_config():
    """重新加载配置"""
    global _global_config
    if _global_config is not None:
        _global_config.load_config()

def set_config_file(config_file: str):
    """设置配置文件路径"""
    global _global_config
    _global_config = UnifiedConfig(config_file)
