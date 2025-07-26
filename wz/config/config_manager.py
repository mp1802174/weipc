#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器
统一管理WZ系统的所有配置信息
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，默认为config/config.json
        """
        if config_file is None:
            # 获取当前文件所在目录
            current_dir = Path(__file__).parent
            config_file = current_dir / "config.json"
        
        self.config_file = Path(config_file)
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键，如 'database.wz_database.host'
            default: 默认值
            
        Returns:
            配置值
        """
        if self._config is None:
            return default
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_database_config(self, db_type: str = 'wz_database') -> Dict[str, Any]:
        """
        获取数据库配置
        
        Args:
            db_type: 数据库类型，'wz_database' 或 'discuz_database'
            
        Returns:
            数据库配置字典
        """
        config = self.get(f'database.{db_type}', {})
        
        # 移除非连接参数
        connection_config = {}
        for key, value in config.items():
            if key not in ['description', 'autocommit', 'pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle']:
                connection_config[key] = value
        
        return connection_config
    
    def get_forum_config(self) -> Dict[str, Any]:
        """
        获取论坛发布配置
        
        Returns:
            论坛发布配置字典
        """
        return self.get('forum_publisher', {})
    
    def get_wechat_config(self) -> Dict[str, Any]:
        """
        获取微信配置
        
        Returns:
            微信配置字典
        """
        return self.get('wechat', {})
    
    def get_cfcj_config(self) -> Dict[str, Any]:
        """
        获取CFCJ配置
        
        Returns:
            CFCJ配置字典
        """
        return self.get('cfcj', {})
    
    def get_web_config(self) -> Dict[str, Any]:
        """
        获取Web配置
        
        Returns:
            Web配置字典
        """
        return self.get('web', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            系统配置字典
        """
        return self.get('system', {})
    
    def reload(self):
        """重新加载配置文件"""
        self._load_config()
    
    def update_config(self, key: str, value: Any):
        """
        更新配置值（仅在内存中，不保存到文件）
        
        Args:
            key: 配置键
            value: 配置值
        """
        if self._config is None:
            self._config = {}
        
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

# 全局配置管理器实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_database_config(db_type: str = 'wz_database') -> Dict[str, Any]:
    """快捷方法：获取数据库配置"""
    return get_config_manager().get_database_config(db_type)

def get_forum_config() -> Dict[str, Any]:
    """快捷方法：获取论坛发布配置"""
    return get_config_manager().get_forum_config()

def get_wechat_config() -> Dict[str, Any]:
    """快捷方法：获取微信配置"""
    return get_config_manager().get_wechat_config()

def get_cfcj_config() -> Dict[str, Any]:
    """快捷方法：获取CFCJ配置"""
    return get_config_manager().get_cfcj_config()

def get_web_config() -> Dict[str, Any]:
    """快捷方法：获取Web配置"""
    return get_config_manager().get_web_config()

def get_system_config() -> Dict[str, Any]:
    """快捷方法：获取系统配置"""
    return get_config_manager().get_system_config()

# 使用示例
if __name__ == "__main__":
    # 测试配置管理器
    config_mgr = ConfigManager()
    
    print("=== 数据库配置测试 ===")
    wz_db_config = config_mgr.get_database_config('wz_database')
    print(f"WZ数据库配置: {wz_db_config}")
    
    discuz_db_config = config_mgr.get_database_config('discuz_database')
    print(f"Discuz数据库配置: {discuz_db_config}")
    
    print("\n=== 论坛发布配置测试 ===")
    forum_config = config_mgr.get_forum_config()
    print(f"论坛发布配置: {forum_config}")
    
    print("\n=== 其他配置测试 ===")
    print(f"微信配置: {config_mgr.get_wechat_config()}")
    print(f"系统配置: {config_mgr.get_system_config()}")
