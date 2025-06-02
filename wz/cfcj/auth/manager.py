"""
CFCJ认证管理模块
处理登录认证和Cookie管理
"""
import json
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from ..config.settings import CFCJConfig
from ..utils.exceptions import AuthenticationError, LoginTimeoutError


class AuthManager:
    """认证管理器"""
    
    def __init__(self, config: Optional[CFCJConfig] = None):
        """
        初始化认证管理器
        
        Args:
            config: 配置管理器
        """
        self.config = config or CFCJConfig()
        self.logger = self._setup_logger()
        self.cookies = {}
        self.session_data = {}
        
        # 加载已保存的认证信息
        self.load_auth_data()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.auth')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_auth_data(self) -> None:
        """加载认证数据"""
        cookie_file = self.config.cookie_file_path

        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cookies = data.get('cookies', {})
                    self.session_data = data.get('session_data', {})

                    # 自动清理无效的cookies
                    self.clean_cookies()

                    self.logger.info("认证数据加载成功")
            except Exception as e:
                self.logger.error(f"加载认证数据失败: {e}")
                self.cookies = {}
                self.session_data = {}
    
    def save_auth_data(self) -> None:
        """保存认证数据"""
        cookie_file = self.config.cookie_file_path
        
        try:
            data = {
                'cookies': self.cookies,
                'session_data': self.session_data,
                'saved_at': time.time()
            }
            
            with open(cookie_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info("认证数据保存成功")
        except Exception as e:
            self.logger.error(f"保存认证数据失败: {e}")
    
    def login_with_credentials(self, driver_or_page, username: str, password: str, 
                             login_url: str, username_selector: str = None, 
                             password_selector: str = None, submit_selector: str = None) -> bool:
        """
        使用用户名密码登录
        
        Args:
            driver_or_page: 浏览器驱动或页面对象
            username: 用户名
            password: 密码
            login_url: 登录页面URL
            username_selector: 用户名输入框选择器
            password_selector: 密码输入框选择器
            submit_selector: 提交按钮选择器
            
        Returns:
            登录是否成功
        """
        try:
            self.logger.info(f"开始登录: {login_url}")

            # 访问登录页面
            if hasattr(driver_or_page, 'find_element'):  # Selenium WebDriver
                driver_or_page.get(login_url)
                return self._login_selenium(driver_or_page, username, password,
                                           username_selector, password_selector, submit_selector)
            else:  # DrissionPage
                driver_or_page.get(login_url)
                return self._login_drission(driver_or_page, username, password,
                                           username_selector, password_selector, submit_selector)
                
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            raise AuthenticationError(f"登录失败: {e}")
    
    def _login_selenium(self, driver, username: str, password: str,
                       username_selector: str, password_selector: str, 
                       submit_selector: str) -> bool:
        """使用Selenium进行登录"""
        if not SELENIUM_AVAILABLE:
            raise AuthenticationError("Selenium不可用")
        
        wait = WebDriverWait(driver, 10)
        
        try:
            # 等待并填写用户名
            username_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, username_selector))
            )
            username_element.clear()
            username_element.send_keys(username)
            
            # 填写密码
            password_element = driver.find_element(By.CSS_SELECTOR, password_selector)
            password_element.clear()
            password_element.send_keys(password)
            
            # 点击登录按钮
            submit_element = driver.find_element(By.CSS_SELECTOR, submit_selector)
            submit_element.click()
            
            # 等待登录完成
            time.sleep(3)
            
            # 检查登录是否成功
            if self._check_login_success_selenium(driver):
                self.save_cookies_from_driver(driver)
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败：未检测到登录成功标志")
                return False
                
        except TimeoutException:
            raise LoginTimeoutError("登录超时")
        except Exception as e:
            raise AuthenticationError(f"登录过程出错: {e}")
    
    def _login_drission(self, page, username: str, password: str,
                       username_selector: str, password_selector: str,
                       submit_selector: str) -> bool:
        """使用DrissionPage进行登录"""
        try:
            # 等待页面完全加载
            time.sleep(3)

            # 首先严格检查是否已经登录（使用更严格的检查）
            if self._check_login_success_strict(page):
                self.logger.info("检测到已经登录，跳过登录过程")
                self.save_cookies_from_page(page)
                return True

            # 检查是否在登录页面，增加等待时间
            self.logger.info("正在查找登录表单...")
            username_element = page.ele(username_selector, timeout=5)
            if not username_element:
                # 尝试其他常见的用户名选择器
                alternative_selectors = [
                    '#login-account-name',
                    'input[name="login"]',
                    'input[name="username"]',
                    'input[name="email"]',
                    '.login-form input[type="text"]',
                    '.login-form input[type="email"]'
                ]

                for alt_selector in alternative_selectors:
                    username_element = page.ele(alt_selector, timeout=2)
                    if username_element:
                        self.logger.info(f"使用备用选择器找到用户名输入框: {alt_selector}")
                        break

                if not username_element:
                    # 再次检查是否已经登录
                    if self._check_login_success_strict(page):
                        self.logger.info("未找到登录表单，但检测到已登录状态")
                        self.save_cookies_from_page(page)
                        return True
                    else:
                        raise AuthenticationError("找不到用户名输入框且未检测到登录状态")

            # 填写用户名
            self.logger.info("正在填写用户名...")
            username_element.clear()
            username_element.input(username)

            # 填写密码
            self.logger.info("正在查找密码输入框...")
            password_element = page.ele(password_selector, timeout=5)
            if not password_element:
                # 尝试其他常见的密码选择器
                alternative_password_selectors = [
                    '#login-account-password',
                    'input[name="password"]',
                    'input[type="password"]',
                    '.login-form input[type="password"]'
                ]

                for alt_selector in alternative_password_selectors:
                    password_element = page.ele(alt_selector, timeout=2)
                    if password_element:
                        self.logger.info(f"使用备用选择器找到密码输入框: {alt_selector}")
                        break

                if not password_element:
                    raise AuthenticationError("找不到密码输入框")

            self.logger.info("正在填写密码...")
            password_element.clear()
            password_element.input(password)

            # 点击登录按钮
            self.logger.info("正在查找登录按钮...")
            submit_element = page.ele(submit_selector, timeout=5)
            if not submit_element:
                # 尝试其他常见的提交按钮选择器
                alternative_submit_selectors = [
                    '#login-button',
                    'button[type="submit"]',
                    '.login-form button',
                    '.btn-primary',
                    'input[type="submit"]'
                ]

                for alt_selector in alternative_submit_selectors:
                    submit_element = page.ele(alt_selector, timeout=2)
                    if submit_element:
                        self.logger.info(f"使用备用选择器找到登录按钮: {alt_selector}")
                        break

                if not submit_element:
                    raise AuthenticationError("找不到登录按钮")

            self.logger.info("正在点击登录按钮...")
            submit_element.click()

            # 等待登录完成
            self.logger.info("等待登录完成...")
            time.sleep(8)

            # 检查登录是否成功
            if self._check_login_success_strict(page):
                self.save_cookies_from_page(page)
                self.logger.info("登录成功")
                return True
            else:
                self.logger.error("登录失败：未检测到登录成功标志")
                return False

        except Exception as e:
            # 如果登录过程出错，检查是否实际上已经登录了
            if self._check_login_success_strict(page):
                self.logger.info("登录过程出错，但检测到已登录状态")
                self.save_cookies_from_page(page)
                return True
            raise AuthenticationError(f"登录过程出错: {e}")
    
    def _check_login_success_selenium(self, driver) -> bool:
        """检查Selenium登录是否成功"""
        # 检查URL变化
        current_url = driver.current_url
        if 'login' not in current_url.lower():
            return True
        
        # 检查页面元素
        success_indicators = [
            '.user-menu',
            '.logout',
            '.profile',
            '.dashboard'
        ]
        
        for indicator in success_indicators:
            try:
                driver.find_element(By.CSS_SELECTOR, indicator)
                return True
            except:
                continue
        
        return False
    
    def _check_login_success_strict(self, page) -> bool:
        """严格检查DrissionPage登录是否成功"""
        try:
            current_url = page.url
            self.logger.debug(f"检查登录状态，当前URL: {current_url}")

            # Linux.do特定的登录成功标志（更严格的检查）
            linux_do_indicators = [
                '.header-dropdown-toggle',  # 用户头像下拉菜单
                '.current-user',            # 当前用户信息
                '.user-menu',               # 用户菜单
                '[data-user-card]',         # 用户卡片
                '.user-activity-link',      # 用户活动链接
                '.d-header .current-user'   # 头部当前用户
            ]

            # 检查明确的登录成功标志
            for indicator in linux_do_indicators:
                element = page.ele(indicator, timeout=2)
                if element:
                    self.logger.debug(f"找到明确的登录成功标志: {indicator}")
                    return True

            # 检查页面文本内容中的明确登录标志
            try:
                page_text = page.html.lower()
                # 更严格的文本检查
                if ('logout' in page_text or '退出' in page_text) and 'login' not in current_url.lower():
                    self.logger.debug("页面包含退出链接，确认已登录")
                    return True
            except:
                pass

            # 如果在登录页面，检查是否有错误信息（说明登录失败）
            if 'login' in current_url.lower():
                error_indicators = [
                    '.alert-error',
                    '.error-message',
                    '.login-error',
                    '.flash-error'
                ]

                for error_indicator in error_indicators:
                    if page.ele(error_indicator, timeout=1):
                        self.logger.debug("发现登录错误信息，确认未登录")
                        return False

            return False

        except Exception as e:
            self.logger.error(f"严格检查登录状态时出错: {e}")
            return False

    def _check_login_success_drission(self, page) -> bool:
        """检查DrissionPage登录是否成功（保持向后兼容）"""
        return self._check_login_success_strict(page)
    
    def load_cookies_to_driver(self, driver, target_domain: str = None) -> None:
        """
        将cookies加载到Selenium驱动

        Args:
            driver: Selenium WebDriver对象
            target_domain: 目标域名，如果指定则只加载该域名的cookies
        """
        if not self.cookies:
            self.logger.debug("没有保存的cookies，跳过加载")
            return

        try:
            # 如果指定了目标域名，只处理该域名的cookies
            if target_domain:
                domains_to_process = {target_domain: self.cookies.get(target_domain, [])}
            else:
                domains_to_process = self.cookies

            cookies_loaded = 0
            for domain, domain_cookies in domains_to_process.items():
                if not domain_cookies:
                    continue

                self.logger.debug(f"正在为域名 {domain} 加载 {len(domain_cookies)} 个cookies")

                # 只有在cookies不为空时才访问域名
                try:
                    # 检查当前页面是否已经在目标域名
                    current_url = driver.current_url
                    if not current_url or domain not in current_url:
                        self.logger.debug(f"访问域名以设置cookies: https://{domain}")
                        driver.get(f"https://{domain}")
                        time.sleep(0.5)  # 减少等待时间
                except Exception as e:
                    self.logger.warning(f"访问域名 {domain} 失败: {e}")
                    continue

                # 设置cookies
                for cookie in domain_cookies:
                    try:
                        driver.add_cookie(cookie)
                        cookies_loaded += 1
                    except Exception as e:
                        self.logger.debug(f"添加cookie失败 {cookie.get('name', 'unknown')}: {e}")

            self.logger.info(f"Cookies加载到驱动完成，共加载 {cookies_loaded} 个cookies")
        except Exception as e:
            self.logger.error(f"加载cookies到驱动失败: {e}")
    
    def load_cookies_to_page(self, page, target_domain: str = None) -> None:
        """
        将cookies加载到DrissionPage

        Args:
            page: DrissionPage页面对象
            target_domain: 目标域名，如果指定则只加载该域名的cookies
        """
        if not self.cookies:
            self.logger.debug("没有保存的cookies，跳过加载")
            return

        try:
            # 如果指定了目标域名，只处理该域名的cookies
            if target_domain:
                domains_to_process = {target_domain: self.cookies.get(target_domain, [])}
            else:
                domains_to_process = self.cookies

            cookies_loaded = 0
            for domain, domain_cookies in domains_to_process.items():
                if not domain_cookies:
                    continue

                self.logger.debug(f"正在为域名 {domain} 加载 {len(domain_cookies)} 个cookies")

                # 只有在cookies不为空时才访问域名
                try:
                    # 检查当前页面是否已经在目标域名
                    current_url = page.url
                    if not current_url or domain not in current_url:
                        self.logger.debug(f"访问域名以设置cookies: https://{domain}")
                        page.get(f"https://{domain}")
                        time.sleep(0.5)  # 减少等待时间
                except Exception as e:
                    self.logger.warning(f"访问域名 {domain} 失败: {e}")
                    continue

                # 设置cookies
                for cookie in domain_cookies:
                    try:
                        page.set.cookies(cookie)
                        cookies_loaded += 1
                    except Exception as e:
                        self.logger.debug(f"添加cookie失败 {cookie.get('name', 'unknown')}: {e}")

            self.logger.info(f"Cookies加载到页面完成，共加载 {cookies_loaded} 个cookies")
        except Exception as e:
            self.logger.error(f"加载cookies到页面失败: {e}")
    
    def save_cookies_from_driver(self, driver) -> None:
        """从Selenium驱动保存cookies"""
        try:
            current_cookies = driver.get_cookies()
            current_domain = driver.execute_script("return document.domain")
            
            if current_domain not in self.cookies:
                self.cookies[current_domain] = []
            
            self.cookies[current_domain] = current_cookies
            self.save_auth_data()
            self.logger.info("从驱动保存cookies完成")
        except Exception as e:
            self.logger.error(f"从驱动保存cookies失败: {e}")
    
    def save_cookies_from_page(self, page) -> None:
        """从DrissionPage保存cookies"""
        try:
            current_cookies = page.cookies()
            current_domain = page.run_js("return document.domain")

            if not current_domain:
                self.logger.warning("无法获取当前域名，跳过保存cookies")
                return

            # 转换cookies格式
            formatted_cookies = []

            if isinstance(current_cookies, dict):
                # 如果cookies是字典格式
                for name, value in current_cookies.items():
                    # 确保name和value都是字符串
                    if isinstance(name, str) and isinstance(value, (str, int, float)):
                        cookie_dict = {
                            'name': name,
                            'value': str(value),
                            'domain': current_domain,
                            'path': '/',
                            'secure': False,
                            'httpOnly': False
                        }

                        # 验证cookie有效性
                        if self._is_valid_cookie(cookie_dict):
                            cleaned_cookie = self._clean_cookie(cookie_dict)
                            if cleaned_cookie:
                                formatted_cookies.append(cleaned_cookie)
            else:
                # 如果cookies是对象列表格式
                for cookie in current_cookies:
                    try:
                        if hasattr(cookie, 'name') and hasattr(cookie, 'value'):
                            cookie_dict = {
                                'name': str(cookie.name),
                                'value': str(cookie.value),
                                'domain': getattr(cookie, 'domain', current_domain),
                                'path': getattr(cookie, 'path', '/'),
                                'secure': getattr(cookie, 'secure', False),
                                'httpOnly': getattr(cookie, 'httpOnly', False)
                            }

                            # 验证cookie有效性
                            if self._is_valid_cookie(cookie_dict):
                                cleaned_cookie = self._clean_cookie(cookie_dict)
                                if cleaned_cookie:
                                    formatted_cookies.append(cleaned_cookie)
                    except Exception as e:
                        self.logger.debug(f"处理单个cookie失败: {e}")
                        continue

            if formatted_cookies:
                self.cookies[current_domain] = formatted_cookies
                self.save_auth_data()
                self.logger.info(f"从页面保存cookies完成，共保存 {len(formatted_cookies)} 个cookies")
            else:
                self.logger.warning("没有有效的cookies可保存")

        except Exception as e:
            self.logger.error(f"从页面保存cookies失败: {e}")
    
    def is_session_valid(self, domain: str) -> bool:
        """检查会话是否有效"""
        if domain not in self.cookies:
            return False
        
        # 检查session超时
        session_timeout = self.config.get('auth.session_timeout', 3600)
        saved_time = self.session_data.get('saved_at', 0)
        
        if time.time() - saved_time > session_timeout:
            self.logger.info("会话已超时")
            return False
        
        return True
    
    def clear_auth_data(self) -> None:
        """清除认证数据"""
        self.cookies = {}
        self.session_data = {}

        cookie_file = self.config.cookie_file_path
        if cookie_file.exists():
            cookie_file.unlink()

        self.logger.info("认证数据已清除")

    def clean_cookies(self) -> None:
        """清理无效的cookies"""
        if not self.cookies:
            return

        cleaned_cookies = {}
        total_removed = 0

        for domain, domain_cookies in self.cookies.items():
            if not isinstance(domain_cookies, list):
                self.logger.warning(f"域名 {domain} 的cookies格式无效，跳过")
                total_removed += 1
                continue

            valid_cookies = []
            for cookie in domain_cookies:
                if self._is_valid_cookie(cookie):
                    # 清理cookie值，确保不会过长
                    cleaned_cookie = self._clean_cookie(cookie)
                    if cleaned_cookie:
                        valid_cookies.append(cleaned_cookie)
                else:
                    total_removed += 1

            if valid_cookies:
                cleaned_cookies[domain] = valid_cookies

        self.cookies = cleaned_cookies
        if total_removed > 0:
            self.logger.info(f"清理了 {total_removed} 个无效cookies")
            self.save_auth_data()

    def _is_valid_cookie(self, cookie) -> bool:
        """检查cookie是否有效"""
        if not isinstance(cookie, dict):
            return False

        # 检查必需字段
        if 'name' not in cookie or 'value' not in cookie:
            return False

        # 检查name和value是否为字符串
        if not isinstance(cookie['name'], str) or not isinstance(cookie['value'], str):
            return False

        # 检查cookie值长度（避免过长的cookie）
        if len(cookie['value']) > 4096:  # 一般cookie值不应超过4KB
            self.logger.debug(f"Cookie {cookie['name']} 值过长，长度: {len(cookie['value'])}")
            return False

        # 检查cookie名称是否包含无效字符
        if any(char in cookie['name'] for char in ['{', '}', '"', "'"]):
            self.logger.debug(f"Cookie名称包含无效字符: {cookie['name']}")
            return False

        return True

    def _clean_cookie(self, cookie: dict) -> dict:
        """清理单个cookie"""
        try:
            cleaned = {
                'name': str(cookie['name']).strip(),
                'value': str(cookie['value']).strip(),
                'domain': cookie.get('domain', ''),
                'path': cookie.get('path', '/'),
                'secure': bool(cookie.get('secure', False)),
                'httpOnly': bool(cookie.get('httpOnly', False))
            }

            # 确保domain字段有效
            if not cleaned['domain']:
                return None

            # 限制cookie值长度
            if len(cleaned['value']) > 4096:
                cleaned['value'] = cleaned['value'][:4096]
                self.logger.debug(f"截断过长的cookie值: {cleaned['name']}")

            return cleaned
        except Exception as e:
            self.logger.debug(f"清理cookie失败: {e}")
            return None
