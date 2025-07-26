"""
多站点认证管理器
根据站点类型使用不同的登录策略
"""
import time
import logging
from typing import Dict, Any, Optional, Union
from selenium.webdriver.remote.webdriver import WebDriver

from .manager import AuthManager
from ..core.site_detector import SiteDetector
from ..utils.exceptions import AuthenticationError


class MultiSiteAuthManager:
    """多站点认证管理器"""
    
    def __init__(self, config):
        """
        初始化多站点认证管理器
        
        Args:
            config: 配置管理器
        """
        self.config = config
        self.site_detector = SiteDetector(config)
        self.auth_manager = AuthManager(config)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.multi_site_auth')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def login(self, url: str, driver_or_page: Union[WebDriver, Any], 
              username: str, password: str) -> bool:
        """
        根据URL自动选择登录策略
        
        Args:
            url: 目标URL
            driver_or_page: 浏览器驱动或页面对象
            username: 用户名
            password: 密码
            
        Returns:
            登录是否成功
        """
        # 检测站点类型
        site_info = self.site_detector.detect_site(url)
        if not site_info:
            raise AuthenticationError(f"不支持的站点: {url}")
        
        # 检查是否需要登录
        if not site_info.get('requires_login', False):
            self.logger.info(f"{site_info['site_name']} 不需要登录")
            return True
        
        login_config = site_info.get('login_config', {})
        if not login_config:
            raise AuthenticationError(f"{site_info['site_name']} 缺少登录配置")
        
        self.logger.info(f"开始 {site_info['site_name']} 登录流程")
        
        # 根据站点类型选择登录方法
        site_key = site_info['site_key']
        
        if site_key == 'linux.do':
            return self._login_linux_do(driver_or_page, username, password, login_config)
        elif site_key == 'nodeseek.com':
            return self._login_nodeseek(driver_or_page, username, password, login_config)
        else:
            return self._login_generic(driver_or_page, username, password, login_config)
    
    def _login_linux_do(self, driver_or_page: Union[WebDriver, Any], 
                       username: str, password: str, login_config: Dict[str, Any]) -> bool:
        """Linux.do 登录"""
        try:
            login_url = login_config.get('login_url')
            username_selector = login_config.get('username_selector')
            password_selector = login_config.get('password_selector')
            submit_selector = login_config.get('submit_selector')
            
            return self.auth_manager.login_with_credentials(
                driver_or_page, username, password, login_url,
                username_selector, password_selector, submit_selector
            )
        except Exception as e:
            self.logger.error(f"Linux.do 登录失败: {e}")
            return False
    
    def _login_nodeseek(self, driver_or_page: Union[WebDriver, Any], 
                       username: str, password: str, login_config: Dict[str, Any]) -> bool:
        """NodeSeek 登录"""
        try:
            login_url = login_config.get('login_url')
            
            # 访问登录页面
            if hasattr(driver_or_page, 'find_element'):  # Selenium
                driver_or_page.get(login_url)
                time.sleep(3)
                
                # 查找并填写表单
                username_element = driver_or_page.find_element("css selector", login_config.get('username_selector'))
                password_element = driver_or_page.find_element("css selector", login_config.get('password_selector'))
                submit_element = driver_or_page.find_element("css selector", login_config.get('submit_selector'))
                
                username_element.clear()
                username_element.send_keys(username)
                
                password_element.clear()
                password_element.send_keys(password)
                
                submit_element.click()
                
            else:  # DrissionPage
                driver_or_page.get(login_url)
                time.sleep(3)
                
                # 查找并填写表单
                username_element = driver_or_page.ele(login_config.get('username_selector'), timeout=5)
                password_element = driver_or_page.ele(login_config.get('password_selector'), timeout=5)
                submit_element = driver_or_page.ele(login_config.get('submit_selector'), timeout=5)
                
                if not all([username_element, password_element, submit_element]):
                    raise AuthenticationError("NodeSeek 登录表单元素未找到")
                
                username_element.clear()
                username_element.input(username)
                
                password_element.clear()
                password_element.input(password)
                
                submit_element.click()
            
            # 等待登录完成
            time.sleep(5)
            
            # 检查登录是否成功
            success_indicators = login_config.get('success_indicators', [])
            return self._check_login_success(driver_or_page, success_indicators)
            
        except Exception as e:
            self.logger.error(f"NodeSeek 登录失败: {e}")
            return False
    
    def _login_generic(self, driver_or_page: Union[WebDriver, Any], 
                      username: str, password: str, login_config: Dict[str, Any]) -> bool:
        """通用登录方法"""
        try:
            login_url = login_config.get('login_url')
            username_selector = login_config.get('username_selector')
            password_selector = login_config.get('password_selector')
            submit_selector = login_config.get('submit_selector')
            
            return self.auth_manager.login_with_credentials(
                driver_or_page, username, password, login_url,
                username_selector, password_selector, submit_selector
            )
        except Exception as e:
            self.logger.error(f"通用登录失败: {e}")
            return False
    
    def _check_login_success(self, driver_or_page: Union[WebDriver, Any], 
                           success_indicators: list) -> bool:
        """检查登录是否成功"""
        try:
            for indicator in success_indicators:
                if hasattr(driver_or_page, 'find_element'):  # Selenium
                    try:
                        driver_or_page.find_element("css selector", indicator)
                        self.logger.info(f"找到登录成功标志: {indicator}")
                        return True
                    except:
                        continue
                else:  # DrissionPage
                    element = driver_or_page.ele(indicator, timeout=2)
                    if element:
                        self.logger.info(f"找到登录成功标志: {indicator}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"检查登录状态失败: {e}")
            return False
    
    def is_login_required(self, url: str) -> bool:
        """
        检查URL是否需要登录
        
        Args:
            url: 要检查的URL
            
        Returns:
            是否需要登录
        """
        site_info = self.site_detector.detect_site(url)
        if not site_info:
            return False
        
        return site_info.get('requires_login', False)
    
    def get_login_config(self, url: str) -> Optional[Dict[str, Any]]:
        """
        获取URL对应的登录配置
        
        Args:
            url: 目标URL
            
        Returns:
            登录配置字典
        """
        site_info = self.site_detector.detect_site(url)
        if not site_info:
            return None
        
        return site_info.get('login_config')
    
    def save_cookies_from_page(self, driver_or_page: Union[WebDriver, Any]) -> None:
        """保存页面cookies"""
        self.auth_manager.save_cookies_from_page(driver_or_page)
    
    def load_cookies_to_page(self, driver_or_page: Union[WebDriver, Any], domain: str) -> None:
        """加载cookies到页面"""
        self.auth_manager.load_cookies_to_page(driver_or_page, domain)
