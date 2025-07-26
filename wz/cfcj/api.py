"""
CFCJ主要API接口
提供统一的内容采集接口
"""
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .core.crawler import CFContentCrawler
from .core.extractor import ContentExtractor
from .core.multi_site_extractor import MultiSiteExtractor
from .core.site_detector import SiteDetector
from .core.database_manager import CFCJDatabaseManager
from .auth.manager import AuthManager
from .auth.multi_site_auth import MultiSiteAuthManager
from .config.settings import CFCJConfig
from .utils.exceptions import CFCJError, AuthenticationError
from .utils.helpers import is_valid_url, batch_process


class CFCJAPI:
    """CFCJ主要API类"""
    
    def __init__(self, config: Optional[CFCJConfig] = None, use_database: bool = True):
        """
        初始化API

        Args:
            config: 配置管理器
            use_database: 是否使用数据库存储
        """
        self.config = config or CFCJConfig()
        self.use_database = use_database
        self.auth_manager = AuthManager(self.config)
        self.multi_site_auth = MultiSiteAuthManager(self.config)
        self.extractor = ContentExtractor(self.config)
        self.multi_site_extractor = MultiSiteExtractor(self.config)
        self.site_detector = SiteDetector(self.config)
        self.crawler = None
        self.logger = self._setup_logger()

        # 初始化数据库管理器
        if self.use_database:
            try:
                self.db_manager = CFCJDatabaseManager()
                self.logger.info("数据库管理器初始化成功")
            except Exception as e:
                self.logger.warning(f"数据库管理器初始化失败: {e}")
                self.db_manager = None
                self.use_database = False
        else:
            self.db_manager = None

    def _create_crawler(self):
        """创建爬虫实例"""
        return CFContentCrawler(self.config, self.multi_site_auth)

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.api')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def crawl_article(self, url: str, login_required: bool = False, 
                     login_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        采集单篇文章
        
        Args:
            url: 文章URL
            login_required: 是否需要登录
            login_credentials: 登录凭据 {'username': '', 'password': '', 'login_url': ''}
            
        Returns:
            文章数据字典
        """
        if not is_valid_url(url):
            raise CFCJError(f"无效的URL: {url}")
        
        self.logger.info(f"开始采集文章: {url}")
        
        try:
            # 初始化爬虫
            if not self.crawler:
                self.crawler = self._create_crawler()
            
            # 启动浏览器
            self.crawler.start_browser()

            # 自动检测是否需要登录
            auto_login_required = self.multi_site_auth.is_login_required(url)

            # 如果需要登录
            if (login_required and login_credentials) or (auto_login_required and login_credentials):
                self._handle_multi_site_login(url, login_credentials)

            # 获取页面内容
            html_content = self.crawler.get_page(url)

            # 使用多站点提取器
            article_data = self.multi_site_extractor.extract_article(html_content, url)

            # 保存到数据库
            if self.use_database and self.db_manager:
                try:
                    self.db_manager.save_article_content(article_data)
                    self.logger.info("文章已保存到数据库")
                except Exception as e:
                    self.logger.error(f"保存到数据库失败: {e}")

            # 简化返回结果，只保留核心字段
            core_result = {
                "url": article_data.get('url', url),
                "title": article_data.get('title', ''),
                "content": article_data.get('content', ''),
                "author": article_data.get('author', ''),
                "publish_time": article_data.get('publish_time', ''),
                "word_count": article_data.get('word_count', 0),
                "site_name": article_data.get('site_name', '')
            }

            self.logger.info(f"文章采集成功: {core_result.get('title', 'Unknown')}")
            return core_result
            
        except Exception as e:
            self.logger.error(f"采集文章失败: {e}")

            # 标记采集失败到数据库
            if self.use_database and self.db_manager:
                try:
                    self.db_manager.mark_article_failed(url, str(e))
                except Exception as db_e:
                    self.logger.error(f"标记失败状态到数据库失败: {db_e}")

            raise CFCJError(f"采集文章失败: {e}")
        finally:
            if self.crawler:
                self.crawler.close_browser()
    
    def crawl_articles_batch(self, urls: List[str], login_required: bool = False,
                           login_credentials: Optional[Dict[str, str]] = None,
                           batch_size: int = 5) -> List[Dict[str, Any]]:
        """
        批量采集文章
        
        Args:
            urls: URL列表
            login_required: 是否需要登录
            login_credentials: 登录凭据
            batch_size: 批次大小
            
        Returns:
            文章数据列表
        """
        self.logger.info(f"开始批量采集 {len(urls)} 篇文章")
        
        results = []
        failed_urls = []
        
        try:
            # 初始化爬虫
            if not self.crawler:
                self.crawler = self._create_crawler()
            
            self.crawler.start_browser()
            
            # 如果需要登录
            if login_required and login_credentials:
                self._handle_login(login_credentials)
            
            # 批量处理
            for batch_urls in batch_process(urls, batch_size):
                for url in batch_urls:
                    try:
                        if not is_valid_url(url):
                            self.logger.warning(f"跳过无效URL: {url}")
                            failed_urls.append({'url': url, 'error': 'Invalid URL'})
                            continue
                        
                        # 获取页面内容
                        html_content = self.crawler.get_page(url)
                        
                        # 提取文章数据
                        article_data = self.extractor.extract_article(html_content, url)
                        results.append(article_data)
                        
                        self.logger.info(f"采集成功: {article_data.get('title', url)}")
                        
                    except Exception as e:
                        self.logger.error(f"采集失败 {url}: {e}")
                        failed_urls.append({'url': url, 'error': str(e)})
                        continue
            
            self.logger.info(f"批量采集完成: 成功 {len(results)}, 失败 {len(failed_urls)}")
            
            return {
                'success': results,
                'failed': failed_urls,
                'total': len(urls),
                'success_count': len(results),
                'failed_count': len(failed_urls)
            }
            
        except Exception as e:
            self.logger.error(f"批量采集失败: {e}")
            raise CFCJError(f"批量采集失败: {e}")
        finally:
            if self.crawler:
                self.crawler.close_browser()
    
    def _handle_login(self, login_credentials: Dict[str, str]) -> None:
        """处理登录"""
        required_fields = ['username', 'password', 'login_url']
        for field in required_fields:
            if field not in login_credentials:
                raise AuthenticationError(f"缺少登录凭据字段: {field}")
        
        # 获取登录选择器（可以从配置中获取或使用默认值）
        username_selector = login_credentials.get('username_selector', 'input[name="username"]')
        password_selector = login_credentials.get('password_selector', 'input[name="password"]')
        submit_selector = login_credentials.get('submit_selector', 'button[type="submit"]')
        
        # 执行登录
        driver_or_page = self.crawler.driver or self.crawler.page
        success = self.auth_manager.login_with_credentials(
            driver_or_page,
            login_credentials['username'],
            login_credentials['password'],
            login_credentials['login_url'],
            username_selector,
            password_selector,
            submit_selector
        )
        
        if not success:
            raise AuthenticationError("登录失败")

    def _handle_multi_site_login(self, url: str, login_credentials: Dict[str, str]) -> None:
        """处理多站点登录"""
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in login_credentials:
                raise AuthenticationError(f"缺少登录凭据字段: {field}")

        # 获取浏览器驱动
        driver_or_page = self.crawler.driver or self.crawler.page

        # 使用多站点认证管理器进行登录
        success = self.multi_site_auth.login(
            url,
            driver_or_page,
            login_credentials['username'],
            login_credentials['password']
        )

        if not success:
            raise AuthenticationError(f"多站点登录失败: {url}")
    
    def crawl_uncrawled_articles(self, limit: int = 100, login_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        采集数据库中未采集的文章

        Args:
            limit: 限制采集数量
            login_credentials: 登录凭据

        Returns:
            采集结果统计
        """
        if not self.use_database or not self.db_manager:
            raise CFCJError("数据库功能未启用")

        self.logger.info(f"开始采集数据库中未采集的文章，限制数量: {limit}")

        # 获取未采集的文章列表
        uncrawled_articles = self.db_manager.get_uncrawled_articles(limit)

        if not uncrawled_articles:
            self.logger.info("没有找到未采集的文章")
            return {
                'total': 0,
                'success_count': 0,
                'failed_count': 0,
                'success': [],
                'failed': []
            }

        self.logger.info(f"找到 {len(uncrawled_articles)} 篇未采集的文章")

        success_results = []
        failed_results = []

        try:
            # 初始化爬虫
            if not self.crawler:
                self.crawler = self._create_crawler()

            self.crawler.start_browser()

            for article in uncrawled_articles:
                url = article['article_url']
                try:
                    self.logger.info(f"正在采集: {article['title']} - {url}")

                    # 自动检测是否需要登录
                    auto_login_required = self.multi_site_auth.is_login_required(url)

                    # 如果需要登录且提供了凭据
                    if auto_login_required and login_credentials:
                        self._handle_multi_site_login(url, login_credentials)

                    # 获取页面内容
                    html_content = self.crawler.get_page(url)

                    # 使用多站点提取器
                    article_data = self.multi_site_extractor.extract_article(html_content, url)

                    # 保存到数据库
                    self.db_manager.save_article_content(article_data)

                    success_results.append({
                        'id': article['id'],
                        'title': article_data.get('title', ''),
                        'url': url,
                        'word_count': article_data.get('word_count', 0)
                    })

                    self.logger.info(f"采集成功: {article_data.get('title', 'Unknown')}")

                except Exception as e:
                    self.logger.error(f"采集失败 {url}: {e}")

                    # 标记失败到数据库
                    self.db_manager.mark_article_failed(url, str(e))

                    failed_results.append({
                        'id': article['id'],
                        'title': article['title'],
                        'url': url,
                        'error': str(e)
                    })

            result = {
                'total': len(uncrawled_articles),
                'success_count': len(success_results),
                'failed_count': len(failed_results),
                'success': success_results,
                'failed': failed_results
            }

            self.logger.info(f"批量采集完成: 成功 {len(success_results)}, 失败 {len(failed_results)}")
            return result

        except Exception as e:
            self.logger.error(f"批量采集未采集文章失败: {e}")
            raise CFCJError(f"批量采集未采集文章失败: {e}")
        finally:
            if self.crawler:
                self.crawler.close_browser()

    def get_config(self) -> CFCJConfig:
        """获取配置管理器"""
        return self.config
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        self.config.set(key, value)
    
    def clear_auth_data(self) -> None:
        """清除认证数据"""
        self.auth_manager.clear_auth_data()
    
    def test_connection(self, url: str) -> Dict[str, Any]:
        """
        测试连接
        
        Args:
            url: 测试URL
            
        Returns:
            测试结果
        """
        try:
            if not self.crawler:
                self.crawler = self._create_crawler()
            
            self.crawler.start_browser()
            html_content = self.crawler.get_page(url, wait_for_cf=True)
            
            result = {
                'success': True,
                'url': url,
                'content_length': len(html_content),
                'has_cloudflare': 'cloudflare' in html_content.lower(),
                'title': self.extractor._extract_title(
                    self.extractor._parse_html(html_content)
                ) if hasattr(self.extractor, '_parse_html') else 'N/A'
            }
            
            self.logger.info(f"连接测试成功: {url}")
            return result
            
        except Exception as e:
            result = {
                'success': False,
                'url': url,
                'error': str(e)
            }
            self.logger.error(f"连接测试失败: {url} - {e}")
            return result
        finally:
            if self.crawler:
                self.crawler.close_browser()


# 便捷函数
def crawl_single_article(url: str, config: Optional[CFCJConfig] = None,
                        login_credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    便捷函数：采集单篇文章
    
    Args:
        url: 文章URL
        config: 配置管理器
        login_credentials: 登录凭据
        
    Returns:
        文章数据
    """
    api = CFCJAPI(config)
    return api.crawl_article(url, bool(login_credentials), login_credentials)


def crawl_multiple_articles(urls: List[str], config: Optional[CFCJConfig] = None,
                          login_credentials: Optional[Dict[str, str]] = None,
                          batch_size: int = 5) -> Dict[str, Any]:
    """
    便捷函数：批量采集文章
    
    Args:
        urls: URL列表
        config: 配置管理器
        login_credentials: 登录凭据
        batch_size: 批次大小
        
    Returns:
        采集结果
    """
    api = CFCJAPI(config)
    return api.crawl_articles_batch(urls, bool(login_credentials), login_credentials, batch_size)
