"""
CFCJ核心爬虫模块
实现Cloudflare保护网站的内容采集
"""
import time
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
    DRISSION_AVAILABLE = True
except ImportError:
    DRISSION_AVAILABLE = False

from ..config.settings import CFCJConfig
from ..auth.manager import AuthManager
from ..utils.exceptions import CFCJError, BrowserNotAvailableError, CloudflareBlockedError


class CFContentCrawler:
    """Cloudflare保护网站内容爬虫"""
    
    def __init__(self, config: Optional[CFCJConfig] = None, auth_manager: Optional[AuthManager] = None):
        """
        初始化爬虫
        
        Args:
            config: 配置管理器
            auth_manager: 认证管理器
        """
        self.config = config or CFCJConfig()
        self.auth_manager = auth_manager or AuthManager(self.config)
        self.driver = None
        self.page = None
        self.logger = self._setup_logger()
        
        # 检查可用的浏览器驱动
        self.browser_type = self._detect_browser_driver()
        
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.crawler')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _detect_browser_driver(self) -> str:
        """检测可用的浏览器驱动"""
        if SELENIUM_AVAILABLE:
            return 'selenium'
        elif DRISSION_AVAILABLE:
            return 'drission'
        else:
            raise BrowserNotAvailableError("未找到可用的浏览器驱动，请安装 undetected-chromedriver 或 DrissionPage")
    
    def _init_selenium_driver(self) -> None:
        """初始化Selenium驱动"""
        if not SELENIUM_AVAILABLE:
            raise BrowserNotAvailableError("Selenium不可用")
        
        options = uc.ChromeOptions()
        
        # 基础配置
        if self.config.get('browser.headless', True):
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'--user-agent={self.config.get("browser.user_agent")}')

        # 添加GitHub Actions专用的Chrome选项
        chrome_options = self.config.get('browser.chrome_options', [])
        for option in chrome_options:
            options.add_argument(option)

        window_size = self.config.get('browser.window_size', [1920, 1080])
        options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
        
        try:
            self.driver = uc.Chrome(options=options)
            self.driver.implicitly_wait(self.config.get('browser.implicit_wait', 10))
            self.driver.set_page_load_timeout(self.config.get('browser.page_load_timeout', 60))
            
            # 注意：这里不立即加载所有cookies，避免反复访问不同域名导致卡住
            # 将在实际访问页面时加载特定域名的cookies
            # self.auth_manager.load_cookies_to_driver(self.driver)
            
        except Exception as e:
            raise CFCJError(f"初始化Selenium驱动失败: {e}")
    
    def _init_drission_driver(self) -> None:
        """初始化DrissionPage驱动"""
        if not DRISSION_AVAILABLE:
            raise BrowserNotAvailableError("DrissionPage不可用")

        self.logger.info("正在配置Chrome选项...")
        co = ChromiumOptions()

        # 基础配置
        if self.config.get('browser.headless', True):
            co.set_argument('--headless')

        # 性能优化配置（移除可能导致问题的选项）
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--disable-extensions')

        # 添加GitHub Actions专用的Chrome选项
        chrome_options = self.config.get('browser.chrome_options', [])
        for option in chrome_options:
            co.set_argument(option)

        # 移除可能导致页面加载问题的选项
        # co.set_argument('--disable-images')
        # co.set_argument('--disable-javascript')

        # 设置用户代理
        user_agent = self.config.get('browser.user_agent')
        if user_agent:
            co.set_user_agent(user_agent)

        # 设置窗口大小
        window_size = self.config.get('browser.window_size', [1920, 1080])
        co.set_argument(f'--window-size={window_size[0]},{window_size[1]}')

        # 设置超时（减少超时时间）
        co.set_argument('--timeout=15000')

        try:
            self.logger.info("正在启动Chrome浏览器...")
            self.page = ChromiumPage(addr_or_opts=co)
            self.logger.info("Chrome浏览器启动成功")

            # 设置页面超时（减少超时时间避免卡住）
            self.page.set.timeouts(base=5, page_load=15, script=5)

            # 加载已保存的cookies（暂时不指定域名，在实际访问页面时再加载特定域名的cookies）
            self.logger.info("正在加载保存的cookies...")
            # 注意：这里不立即加载所有cookies，避免反复访问不同域名导致卡住
            # self.auth_manager.load_cookies_to_page(self.page)
            self.logger.info("Cookies加载准备完成")

        except Exception as e:
            self.logger.error(f"初始化DrissionPage驱动失败: {e}")
            raise CFCJError(f"初始化DrissionPage驱动失败: {e}")
    
    def start_browser(self) -> None:
        """启动浏览器"""
        self.logger.info(f"启动浏览器，使用驱动: {self.browser_type}")
        
        if self.browser_type == 'selenium':
            self._init_selenium_driver()
        elif self.browser_type == 'drission':
            self._init_drission_driver()
    
    def close_browser(self) -> None:
        """关闭浏览器"""
        try:
            if self.driver:
                # 保存cookies
                self.auth_manager.save_cookies_from_driver(self.driver)
                self.driver.quit()
                self.driver = None
            
            if self.page:
                # 保存cookies
                self.auth_manager.save_cookies_from_page(self.page)
                self.page.quit()
                self.page = None
                
            self.logger.info("浏览器已关闭")
        except Exception as e:
            self.logger.error(f"关闭浏览器时出错: {e}")
    
    def get_page(self, url: str, wait_for_cf: bool = True) -> str:
        """
        获取页面内容
        
        Args:
            url: 目标URL
            wait_for_cf: 是否等待Cloudflare验证
            
        Returns:
            页面HTML内容
        """
        if not self.driver and not self.page:
            self.start_browser()
        
        max_retries = self.config.get('crawler.max_retries', 3)
        retry_delay = self.config.get('crawler.retry_delay', 5)
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"正在访问: {url} (尝试 {attempt + 1}/{max_retries})")
                
                if self.browser_type == 'selenium':
                    return self._get_page_selenium(url, wait_for_cf)
                elif self.browser_type == 'drission':
                    return self._get_page_drission(url, wait_for_cf)
                    
            except CloudflareBlockedError:
                self.logger.warning(f"被Cloudflare阻止，尝试 {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                else:
                    raise
            except Exception as e:
                self.logger.error(f"获取页面失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise CFCJError(f"获取页面失败: {e}")
        
        raise CFCJError("达到最大重试次数")
    
    def _get_page_selenium(self, url: str, wait_for_cf: bool) -> str:
        """使用Selenium获取页面"""
        # 从URL中提取域名
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        target_domain = parsed_url.netloc

        # 加载特定域名的cookies
        self.logger.debug(f"为域名 {target_domain} 加载cookies")
        self.auth_manager.load_cookies_to_driver(self.driver, target_domain)

        self.driver.get(url)

        if wait_for_cf:
            self._wait_for_cloudflare_selenium()

        # 等待页面加载完成
        time.sleep(self.config.get('crawler.request_delay', 2))

        return self.driver.page_source
    
    def _get_page_drission(self, url: str, wait_for_cf: bool) -> str:
        """使用DrissionPage获取页面"""
        self.logger.info(f"正在访问页面: {url}")

        try:
            # 从URL中提取域名
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            target_domain = parsed_url.netloc

            # 加载特定域名的cookies
            self.logger.debug(f"为域名 {target_domain} 加载cookies")
            self.auth_manager.load_cookies_to_page(self.page, target_domain)

            # 访问页面
            self.page.get(url)
            self.logger.info("页面访问成功，正在检查Cloudflare...")

            if wait_for_cf:
                self._wait_for_cloudflare_drission()

            # 等待页面加载完成
            request_delay = self.config.get('crawler.request_delay', 2)
            self.logger.info(f"等待页面加载完成 ({request_delay}秒)...")
            time.sleep(request_delay)

            html_content = self.page.html
            self.logger.info(f"页面内容获取成功，长度: {len(html_content)} 字符")
            return html_content

        except Exception as e:
            self.logger.error(f"获取页面失败: {e}")
            raise
    
    def _wait_for_cloudflare_selenium(self) -> None:
        """等待Cloudflare验证完成 (Selenium)"""
        cf_wait_time = self.config.get('crawler.cf_wait_time', 10)
        
        # 检查是否有Cloudflare验证页面
        cf_indicators = [
            "Just a moment",
            "Checking your browser",
            "Please wait",
            "DDoS protection by Cloudflare"
        ]
        
        for indicator in cf_indicators:
            if indicator in self.driver.page_source:
                self.logger.info("检测到Cloudflare验证，等待完成...")
                time.sleep(cf_wait_time)
                break
        
        # 检查是否被阻止
        if "Access denied" in self.driver.page_source or "Error 1020" in self.driver.page_source:
            raise CloudflareBlockedError("被Cloudflare阻止访问")
    
    def _wait_for_cloudflare_drission(self) -> None:
        """等待Cloudflare验证完成 (DrissionPage)"""
        cf_wait_time = self.config.get('crawler.cf_wait_time', 10)

        self.logger.info("检查Cloudflare验证状态...")

        # 检查是否有Cloudflare验证页面（使用更短的超时）
        cf_indicators = [
            'Just a moment',
            'Checking your browser',
            'Please wait',
            'DDoS protection'
        ]

        has_cf_check = False
        for indicator in cf_indicators:
            try:
                if self.page.s_ele(f'text:{indicator}', timeout=2):
                    has_cf_check = True
                    break
            except Exception as e:
                self.logger.debug(f"检查CF指示器 '{indicator}' 时出错: {e}")
                continue

        if has_cf_check:
            self.logger.info(f"检测到Cloudflare验证，等待 {cf_wait_time} 秒...")
            time.sleep(cf_wait_time)
        else:
            self.logger.info("未检测到Cloudflare验证页面")

        # 检查是否被阻止
        try:
            if self.page.s_ele('text:Access denied', timeout=2) or self.page.s_ele('text:Error 1020', timeout=2):
                raise CloudflareBlockedError("被Cloudflare阻止访问")
        except CloudflareBlockedError:
            raise
        except Exception as e:
            self.logger.debug(f"检查CF阻止状态时出错: {e}")
            # 如果检查失败，假设没有被阻止，继续执行
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close_browser()
