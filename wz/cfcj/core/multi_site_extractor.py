"""
多站点内容提取器
根据站点类型使用不同的提取策略
"""
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag
import logging
from urllib.parse import urljoin, urlparse

from .site_detector import SiteDetector
from .wechat_content_optimizer import optimize_wechat_content


class MultiSiteExtractor:
    """多站点内容提取器"""
    
    def __init__(self, config):
        """
        初始化多站点提取器
        
        Args:
            config: 配置管理器
        """
        self.config = config
        self.site_detector = SiteDetector(config)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.multi_site_extractor')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def extract_article(self, html: str, url: str) -> Dict[str, Any]:
        """
        从HTML中提取文章信息
        
        Args:
            html: 页面HTML内容
            url: 页面URL
            
        Returns:
            包含文章信息的字典
        """
        # 检测站点类型
        site_info = self.site_detector.detect_site(url)
        if not site_info:
            self.logger.warning(f"不支持的站点，使用通用提取器: {url}")
            return self._extract_generic(html, url)
        
        self.logger.info(f"使用 {site_info['site_name']} 专用提取器")
        
        # 根据站点类型选择提取方法
        site_key = site_info['site_key']
        
        if site_key == 'linux.do':
            return self._extract_linux_do(html, url, site_info)
        elif site_key == 'nodeseek.com':
            return self._extract_nodeseek(html, url, site_info)
        elif site_key == 'mp.weixin.qq.com':
            return self._extract_wechat_mp(html, url, site_info)
        else:
            return self._extract_with_config(html, url, site_info)
    
    def _extract_linux_do(self, html: str, url: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取Linux.do站点内容"""
        soup = BeautifulSoup(html, 'html.parser')
        extraction_config = site_info['extraction']
        
        # 移除无关元素
        self._remove_unwanted_elements(soup, extraction_config.get('exclude_selectors', []))
        
        # 提取基本信息
        article_data = {
            'url': url,
            'title': self._extract_title_with_selectors(soup, extraction_config.get('title_selectors', [])),
            'content': self._extract_linux_do_content(soup, extraction_config),
            'author': self._extract_author_with_selectors(soup, extraction_config.get('author_selectors', [])),
            'publish_time': self._extract_time_with_selectors(soup, extraction_config.get('time_selectors', [])),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'site_name': site_info['site_name']
        }

        # 不再单独提取图片信息，图片已集成在content中
        # article_data['images'] = self._extract_images(soup, url, extraction_config)

        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))

        return article_data
    
    def _extract_nodeseek(self, html: str, url: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取NodeSeek站点内容"""
        soup = BeautifulSoup(html, 'html.parser')
        extraction_config = site_info['extraction']
        
        # 移除无关元素
        self._remove_unwanted_elements(soup, extraction_config.get('exclude_selectors', []))
        
        article_data = {
            'url': url,
            'title': self._extract_title_with_selectors(soup, extraction_config.get('title_selectors', [])),
            'content': self._extract_content_with_selectors(soup, extraction_config.get('content_selectors', [])),
            'author': self._extract_author_with_selectors(soup, extraction_config.get('author_selectors', [])),
            'publish_time': self._extract_time_with_selectors(soup, extraction_config.get('time_selectors', [])),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'site_name': site_info['site_name']
        }

        # 不再单独提取图片信息，图片已集成在content中
        # article_data['images'] = self._extract_images(soup, url, extraction_config)

        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))

        return article_data
    
    def _extract_wechat_mp(self, html: str, url: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取微信公众号内容 - 使用优化的提取方法"""
        self.logger.info(f"使用优化的微信内容提取器: {url}")

        try:
            # 使用新的优化提取器
            result = optimize_wechat_content(url)

            if result['success']:
                # 转换为标准格式
                article_data = {
                    'url': url,
                    'title': result.get('title', ''),
                    'content': result.get('content', ''),
                    'author': '',  # 优化器暂时不提取作者信息
                    'publish_time': '',  # 优化器暂时不提取时间信息
                    'word_count': result.get('word_count', 0),
                    'extracted_at': datetime.now().isoformat(),
                    'site_name': site_info['site_name'],
                    'extraction_method': result.get('method', 'optimized'),
                    'original_word_count': result.get('original_word_count', 0),
                    'cleaning_ratio': result.get('cleaning_ratio', 0)
                }

                self.logger.info(f"优化提取成功: {article_data['word_count']} 字符 (清理率: {article_data['cleaning_ratio']*100:.1f}%)")
                return article_data
            else:
                # 优化提取失败，回退到原有方法
                self.logger.warning(f"优化提取失败，回退到原有方法: {result.get('error', '未知错误')}")
                return self._extract_wechat_mp_fallback(html, url, site_info)

        except Exception as e:
            # 异常情况，回退到原有方法
            self.logger.error(f"优化提取异常，回退到原有方法: {e}")
            return self._extract_wechat_mp_fallback(html, url, site_info)

    def _extract_wechat_mp_fallback(self, html: str, url: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """微信公众号内容提取的回退方法（原有逻辑）"""
        soup = BeautifulSoup(html, 'html.parser')
        extraction_config = site_info['extraction']

        # 移除无关元素
        self._remove_unwanted_elements(soup, extraction_config.get('exclude_selectors', []))

        # 先提取作者信息，用于后续的差异化处理
        author = self._extract_author_with_selectors(soup, extraction_config.get('author_selectors', []))

        # 提取内容，支持基于作者的差异化规则
        content = self._extract_wechat_content_with_author_rules(soup, extraction_config, author)

        article_data = {
            'url': url,
            'title': self._extract_title_with_selectors(soup, extraction_config.get('title_selectors', [])),
            'content': content,
            'author': author,
            'publish_time': self._extract_time_with_selectors(soup, extraction_config.get('time_selectors', [])),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'site_name': site_info['site_name'],
            'extraction_method': 'fallback'
        }

        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))

        return article_data
    
    def _extract_with_config(self, html: str, url: str, site_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用配置文件进行通用提取"""
        soup = BeautifulSoup(html, 'html.parser')
        extraction_config = site_info['extraction']
        
        # 移除无关元素
        self._remove_unwanted_elements(soup, extraction_config.get('exclude_selectors', []))
        
        article_data = {
            'url': url,
            'title': self._extract_title_with_selectors(soup, extraction_config.get('title_selectors', [])),
            'content': self._extract_content_with_selectors(soup, extraction_config.get('content_selectors', [])),
            'author': self._extract_author_with_selectors(soup, extraction_config.get('author_selectors', [])),
            'publish_time': self._extract_time_with_selectors(soup, extraction_config.get('time_selectors', [])),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'site_name': site_info['site_name']
        }

        # 不再单独提取图片信息，图片已集成在content中
        # article_data['images'] = self._extract_images(soup, url, extraction_config)

        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))

        return article_data
    
    def _extract_generic(self, html: str, url: str) -> Dict[str, Any]:
        """通用提取器，用于不支持的站点"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 使用默认配置
        default_config = self.config.get('extraction', {})
        
        article_data = {
            'url': url,
            'title': self._extract_title_with_selectors(soup, default_config.get('title_selectors', [])),
            'content': self._extract_content_with_selectors(soup, default_config.get('content_selectors', [])),
            'author': self._extract_author_with_selectors(soup, default_config.get('author_selectors', [])),
            'publish_time': self._extract_time_with_selectors(soup, default_config.get('time_selectors', [])),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'site_name': 'Unknown'
        }

        # 不再单独提取图片信息，图片已集成在content中
        # article_data['images'] = self._extract_images(soup, url)

        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))

        return article_data

    def _extract_title_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """使用选择器列表提取标题"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        # 回退到通用选择器
        fallback_selectors = ['h1', 'title', '.title', '.post-title']
        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        return ""

    def _extract_content_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """使用选择器列表提取内容"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content(element)

        # 回退到通用选择器
        fallback_selectors = ['.content', '.post-content', '.article-content', 'article', '.post']
        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content(element)

        return ""

    def _extract_content_with_selectors_preserve_html(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """使用选择器列表提取内容，保留HTML结构"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content_preserve_html(element)

        # 回退到通用选择器
        fallback_selectors = ['.content', '.post-content', '.article-content', 'article', '.post']
        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content_preserve_html(element)

        return ""

    def _extract_author_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """使用选择器列表提取作者"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        return ""

    def _extract_time_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """使用选择器列表提取时间"""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # 尝试获取datetime属性
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    return datetime_attr

                # 获取文本内容
                text = element.get_text(strip=True)
                if text:
                    return text

        return ""

    def _extract_linux_do_content(self, soup: BeautifulSoup, extraction_config: Dict[str, Any]) -> str:
        """提取Linux.do的主贴内容"""
        # 找到主贴容器
        main_post_selector = extraction_config.get('main_post_selector', '#post_1')
        main_post = soup.select_one(main_post_selector)

        if not main_post:
            self.logger.warning("未找到Linux.do主贴容器")
            return self._extract_content_with_selectors(soup, extraction_config.get('content_selectors', []))

        # 在主贴中查找内容
        content_selectors = extraction_config.get('content_selectors', [])
        for selector in content_selectors:
            content_element = main_post.select_one(selector)
            if content_element:
                return self._clean_content(content_element)

        # 如果没找到，返回主贴的文本内容
        return self._clean_content(main_post)

    def _extract_wechat_content_with_author_rules(self, soup: BeautifulSoup, extraction_config: Dict[str, Any], author: str) -> str:
        """提取微信公众号内容，支持基于作者的差异化规则"""
        # 先使用常规方法提取内容，保留HTML结构
        content = self._extract_content_with_selectors_preserve_html(soup, extraction_config.get('content_selectors', []))

        # 检查是否有基于作者的差异化规则
        author_rules = extraction_config.get('author_based_rules', {})
        if author and author in author_rules:
            content = self._apply_author_based_content_extraction(content, author_rules[author])

        return content

    def _apply_author_based_content_extraction(self, content: str, rules: Dict[str, Any]) -> str:
        """应用基于作者的内容提取规则"""
        start_marker = rules.get('content_start_marker')
        end_marker = rules.get('content_end_marker')
        include_markers = rules.get('include_markers', False)
        fallback_to_full = rules.get('fallback_to_full', True)

        if not start_marker or not end_marker:
            self.logger.warning("作者规则缺少开始或结束标识符")
            return content

        # 查找开始和结束位置
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)

        if start_pos == -1 or end_pos == -1:
            self.logger.warning(f"未找到内容标识符: start='{start_marker}', end='{end_marker}'")
            if fallback_to_full:
                self.logger.info("回退到完整内容")
                return content
            else:
                return ""

        if start_pos >= end_pos:
            self.logger.warning("开始标识符位置在结束标识符之后")
            if fallback_to_full:
                return content
            else:
                return ""

        # 提取指定范围的内容
        if include_markers:
            extracted_content = content[start_pos:end_pos + len(end_marker)]
        else:
            extracted_content = content[start_pos + len(start_marker):end_pos]

        # 清理提取的内容
        extracted_content = extracted_content.strip()

        self.logger.info(f"基于作者规则提取内容: {len(extracted_content)} 字符")
        return extracted_content

    def _clean_content(self, element: Tag) -> str:
        """清理内容元素"""
        if not element:
            return ""

        # 移除脚本和样式
        for script in element(["script", "style"]):
            script.decompose()

        # 移除一些常见的无用元素
        unwanted_selectors = [
            '.ads', '.advertisement', '.share', '.social',
            '.related', '.sidebar', '.footer', '.header'
        ]

        for selector in unwanted_selectors:
            for unwanted in element.select(selector):
                unwanted.decompose()

        # 获取文本内容，保持基本格式
        text = element.get_text(separator='\n', strip=True)

        # 清理多余的空行
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)

    def _clean_content_preserve_html(self, element: Tag) -> str:
        """清理内容元素，保留HTML结构"""
        if not element:
            return ""

        # 创建元素的副本以避免修改原始DOM
        element_copy = element.__copy__()

        # 移除脚本和样式
        for script in element_copy(["script", "style"]):
            script.decompose()

        # 移除一些常见的无用元素
        unwanted_selectors = [
            '.ads', '.advertisement', '.share', '.social',
            '.related', '.sidebar', '.footer', '.header'
        ]

        for selector in unwanted_selectors:
            for unwanted in element_copy.select(selector):
                unwanted.decompose()

        # 处理图片URL，确保是绝对URL
        for img in element_copy.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src:
                # 处理相对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    # 这里需要基础URL，暂时保持原样
                    pass
                elif not src.startswith(('http://', 'https://')):
                    # 相对路径，暂时保持原样
                    pass

                # 更新src属性
                img['src'] = src

                # 移除懒加载属性，使用实际src
                if img.get('data-src'):
                    img['src'] = img['data-src']
                    del img['data-src']
                if img.get('data-original'):
                    img['src'] = img['data-original']
                    del img['data-original']

        # 返回HTML内容
        return str(element_copy)

    def _remove_unwanted_elements(self, soup: BeautifulSoup, exclude_selectors: List[str]) -> None:
        """移除不需要的元素"""
        for selector in exclude_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

    def _extract_images(self, soup: BeautifulSoup, base_url: str, extraction_config: Dict[str, Any] = None) -> List[Dict[str, str]]:
        """提取文章中的图片信息"""
        images = []

        # 获取内容区域，如果有配置的话
        content_area = soup
        if extraction_config:
            content_selectors = extraction_config.get('content_selectors', [])
            main_post_selector = extraction_config.get('main_post_selector')

            # 优先使用主贴选择器
            if main_post_selector:
                main_post = soup.select_one(main_post_selector)
                if main_post:
                    content_area = main_post
            # 否则使用内容选择器
            elif content_selectors:
                for selector in content_selectors:
                    content_element = soup.select_one(selector)
                    if content_element:
                        content_area = content_element
                        break

        # 查找所有图片
        img_tags = content_area.find_all('img')

        for img in img_tags:
            img_info = {}

            # 获取图片URL
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            if src:
                # 处理相对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    parsed_base = urlparse(base_url)
                    src = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                img_info['url'] = src

                # 获取alt文本
                alt = img.get('alt', '').strip()
                if alt:
                    img_info['alt'] = alt

                # 获取title属性
                title = img.get('title', '').strip()
                if title:
                    img_info['title'] = title

                # 获取图片尺寸信息
                width = img.get('width')
                height = img.get('height')
                if width:
                    img_info['width'] = width
                if height:
                    img_info['height'] = height

                # 获取图片的父元素文本作为描述
                parent = img.parent
                if parent and parent.name not in ['body', 'html']:
                    parent_text = parent.get_text(strip=True)
                    # 如果父元素文本不是太长且不包含太多其他内容
                    if parent_text and len(parent_text) < 200 and parent_text != alt:
                        img_info['description'] = parent_text

                images.append(img_info)

        self.logger.info(f"提取到 {len(images)} 张图片")
        return images
