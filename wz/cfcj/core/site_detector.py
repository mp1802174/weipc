"""
站点识别器模块
根据URL自动识别站点类型并返回相应的配置
"""
import re
from urllib.parse import urlparse
from typing import Dict, Any, Optional
import logging


class SiteDetector:
    """站点识别器"""
    
    def __init__(self, config):
        """
        初始化站点识别器
        
        Args:
            config: 配置管理器
        """
        self.config = config
        self.logger = self._setup_logger()
        
        # 支持的站点配置
        self.supported_sites = self.config.get('sites', {})
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.site_detector')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def detect_site(self, url: str) -> Optional[Dict[str, Any]]:
        """
        根据URL检测站点类型
        
        Args:
            url: 要检测的URL
            
        Returns:
            站点配置字典，如果不支持则返回None
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 移除www前缀进行匹配
            if domain.startswith('www.'):
                domain_without_www = domain[4:]
            else:
                domain_without_www = domain
            
            # 检查每个支持的站点
            for site_key, site_config in self.supported_sites.items():
                site_domain = site_config.get('domain', '').lower()
                
                # 精确匹配或子域名匹配
                if (domain == site_domain or 
                    domain_without_www == site_domain or
                    domain.endswith('.' + site_domain) or
                    domain_without_www.endswith('.' + site_domain)):
                    
                    self.logger.info(f"检测到站点类型: {site_config.get('name', site_key)} ({domain})")
                    
                    # 返回完整的站点配置
                    return {
                        'site_key': site_key,
                        'site_name': site_config.get('name', site_key),
                        'domain': site_domain,
                        'requires_login': site_config.get('requires_login', False),
                        'login_config': site_config.get('login_config', {}),
                        'extraction': site_config.get('extraction', {}),
                        'url': url,
                        'original_domain': domain
                    }
            
            self.logger.warning(f"不支持的站点: {domain}")
            return None
            
        except Exception as e:
            self.logger.error(f"站点检测失败: {e}")
            return None
    
    def is_supported_site(self, url: str) -> bool:
        """
        检查URL是否为支持的站点
        
        Args:
            url: 要检查的URL
            
        Returns:
            是否支持该站点
        """
        return self.detect_site(url) is not None
    
    def get_supported_sites(self) -> Dict[str, str]:
        """
        获取所有支持的站点列表
        
        Returns:
            站点域名到名称的映射
        """
        return {
            config.get('domain', key): config.get('name', key)
            for key, config in self.supported_sites.items()
        }
    
    def get_site_config(self, site_key: str) -> Optional[Dict[str, Any]]:
        """
        根据站点键获取站点配置
        
        Args:
            site_key: 站点键（如 'linux.do'）
            
        Returns:
            站点配置字典
        """
        return self.supported_sites.get(site_key)
    
    def validate_site_config(self, site_config: Dict[str, Any]) -> bool:
        """
        验证站点配置的完整性
        
        Args:
            site_config: 站点配置
            
        Returns:
            配置是否有效
        """
        required_fields = ['domain', 'extraction']
        
        for field in required_fields:
            if field not in site_config:
                self.logger.error(f"站点配置缺少必需字段: {field}")
                return False
        
        # 检查提取配置
        extraction = site_config.get('extraction', {})
        if not extraction.get('content_selectors') and not extraction.get('title_selectors'):
            self.logger.error("站点配置缺少内容或标题选择器")
            return False
        
        # 如果需要登录，检查登录配置
        if site_config.get('requires_login', False):
            login_config = site_config.get('login_config', {})
            required_login_fields = ['login_url', 'username_selector', 'password_selector', 'submit_selector']
            
            for field in required_login_fields:
                if field not in login_config:
                    self.logger.error(f"登录配置缺少必需字段: {field}")
                    return False
        
        return True
    
    def add_site_config(self, site_key: str, site_config: Dict[str, Any]) -> bool:
        """
        动态添加站点配置
        
        Args:
            site_key: 站点键
            site_config: 站点配置
            
        Returns:
            是否添加成功
        """
        if not self.validate_site_config(site_config):
            return False
        
        self.supported_sites[site_key] = site_config
        self.logger.info(f"成功添加站点配置: {site_key}")
        return True
