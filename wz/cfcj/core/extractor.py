"""
CFCJ内容提取模块
从HTML中提取结构化的文章数据
"""
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urljoin

try:
    from bs4 import BeautifulSoup, Tag
except ImportError:
    raise ImportError("请安装 beautifulsoup4: pip install beautifulsoup4")

from ..config.settings import CFCJConfig


class ContentExtractor:
    """内容提取器"""

    def __init__(self, config: Optional[CFCJConfig] = None):
        """
        初始化内容提取器

        Args:
            config: 配置管理器
        """
        self.config = config or CFCJConfig()
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """设置日志记录器"""
        import logging
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def extract_article(self, html: str, url: str) -> Dict[str, Any]:
        """
        从HTML中提取文章信息
        
        Args:
            html: 页面HTML内容
            url: 页面URL
            
        Returns:
            包含文章信息的字典
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取基本信息
        article_data = {
            'url': url,
            'title': self._extract_title(soup, url),
            'content': self._extract_content(soup, url),
            'author': self._extract_author(soup),
            'publish_time': self._extract_publish_time(soup),
            'tags': self._extract_tags(soup),
            'images': self._extract_images(soup, url),
            'links': self._extract_links(soup, url),
            'word_count': 0,
            'extracted_at': datetime.now().isoformat()
        }
        
        # 计算字数
        if article_data['content']:
            article_data['word_count'] = len(re.sub(r'\s+', '', article_data['content']))
        
        # 针对linux.do网站的特殊处理
        if 'linux.do' in url:
            article_data.update(self._extract_linux_do_specific(soup))

        return article_data

    def _parse_html(self, html: str) -> BeautifulSoup:
        """解析HTML字符串"""
        return BeautifulSoup(html, 'html.parser')
    
    def _extract_title(self, soup: BeautifulSoup, url: str = "") -> str:
        """提取标题"""
        # 针对linux.do网站的特殊处理
        if 'linux.do' in url:
            return self._extract_linux_do_title(soup)

        selectors = self.config.get('extraction.title_selectors', [])

        # 尝试配置的选择器
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        # 通用选择器
        title_selectors = [
            'h1',
            '.title',
            '.post-title',
            '.article-title',
            '[data-title]',
            'title'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        return ""
    
    def _extract_content(self, soup: BeautifulSoup, url: str = "") -> str:
        """提取正文内容"""
        # 针对linux.do网站的特殊处理
        if 'linux.do' in url:
            return self._extract_linux_do_content(soup)

        selectors = self.config.get('extraction.content_selectors', [])

        # 尝试配置的选择器
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content(element)

        # 通用选择器
        content_selectors = [
            '.post-content',
            '.article-content',
            '.content',
            '.post-body',
            '.entry-content',
            '[data-content]',
            'article',
            '.post'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                return self._clean_content(element)

        # 如果都没找到，尝试找最大的文本块
        return self._extract_main_content(soup)
    
    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        selectors = self.config.get('extraction.author_selectors', [])
        
        # 尝试配置的选择器
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # 通用选择器
        author_selectors = [
            '.author',
            '.post-author',
            '.by-author',
            '[data-author]',
            '.username',
            '.user-name'
        ]
        
        for selector in author_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> str:
        """提取发布时间"""
        selectors = self.config.get('extraction.time_selectors', [])
        
        # 尝试配置的选择器
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                time_text = self._extract_time_from_element(element)
                if time_text:
                    return time_text
        
        # 通用选择器
        time_selectors = [
            'time',
            '.time',
            '.date',
            '.publish-time',
            '.post-time',
            '.created-at',
            '[datetime]',
            '[data-time]'
        ]
        
        for selector in time_selectors:
            element = soup.select_one(selector)
            if element:
                time_text = self._extract_time_from_element(element)
                if time_text:
                    return time_text
        
        return ""
    
    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """提取标签"""
        tags = []
        
        tag_selectors = [
            '.tags a',
            '.tag',
            '.post-tags a',
            '.categories a',
            '[data-tag]'
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text(strip=True)
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)
        
        return tags
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取图片"""
        images = []

        # 针对linux.do网站，只提取主贴中的图片
        if 'linux.do' in base_url:
            return self._extract_linux_do_images(soup, base_url)

        img_elements = soup.find_all('img')
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src:
                # 转换为绝对URL
                absolute_url = urljoin(base_url, src)
                images.append({
                    'url': absolute_url,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })

        return images

    def _extract_linux_do_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取linux.do主贴中的图片"""
        images = []

        # 找到主贴容器
        main_post_selector = self.config.get('extraction.linux_do.main_post_selector', '#post_1')
        main_post = soup.select_one(main_post_selector)

        if not main_post:
            # 备用选择器
            backup_selectors = ['#post_1', '.topic-post:first-child', '[data-post-number="1"]']
            for selector in backup_selectors:
                main_post = soup.select_one(selector)
                if main_post:
                    break

        if not main_post:
            self.logger.warning("未找到主贴容器，无法提取图片")
            return images

        # 在主贴中查找图片
        img_elements = main_post.find_all('img')
        for img in img_elements:
            src = img.get('src') or img.get('data-src')
            if src:
                # 过滤掉头像等无关图片
                if self._is_content_image(img, src):
                    absolute_url = urljoin(base_url, src)
                    images.append({
                        'url': absolute_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })

        return images

    def _is_content_image(self, img_element, src: str) -> bool:
        """判断是否是内容图片（非头像、表情等）"""
        # 排除头像图片
        if 'avatar' in src.lower() or 'user_avatar' in src.lower():
            return False

        # 排除小尺寸的表情图片
        if 'emoji' in src.lower() and ('24' in src or '48' in src):
            return False

        # 排除letter_avatar
        if 'letter_avatar' in src.lower():
            return False

        # 检查父元素，排除在用户信息区域的图片
        parent_classes = []
        parent = img_element.parent
        while parent and len(parent_classes) < 5:  # 最多检查5层父元素
            if hasattr(parent, 'get') and parent.get('class'):
                parent_classes.extend(parent.get('class'))
            parent = parent.parent

        # 如果在用户信息相关的容器中，则不是内容图片
        user_related_classes = ['avatar', 'user-info', 'names', 'username', 'user-card']
        if any(cls in parent_classes for cls in user_related_classes):
            return False

        return True
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取链接"""
        links = []
        
        link_elements = soup.find_all('a', href=True)
        for link in link_elements:
            href = link.get('href')
            if href and not href.startswith('#'):
                # 转换为绝对URL
                absolute_url = urljoin(base_url, href)
                links.append({
                    'url': absolute_url,
                    'text': link.get_text(strip=True),
                    'title': link.get('title', '')
                })
        
        return links
    
    def _extract_linux_do_title(self, soup: BeautifulSoup) -> str:
        """提取linux.do网站的标题"""
        # 优先使用linux.do特定的选择器
        linux_do_selectors = self.config.get('extraction.linux_do.title_selectors', [])

        for selector in linux_do_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        # 回退到通用选择器
        fallback_selectors = [
            'h1',
            '.title',
            '.topic-title',
            '.post-title'
        ]

        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)

        return ""

    def _extract_linux_do_content(self, soup: BeautifulSoup) -> str:
        """提取linux.do网站的主贴内容 - 精确定位，只提取核心内容"""
        self.logger.debug("开始提取linux.do主贴核心内容")

        # 首先移除所有回复帖子和无关元素
        self._remove_replies_and_navigation(soup)

        # 找到主贴容器 - 使用更精确的选择器
        main_post = self._find_main_post(soup)

        if not main_post:
            self.logger.error("无法找到主贴容器")
            return ""

        self.logger.debug("找到主贴容器，开始提取核心内容")

        # 在主贴中查找.cooked内容（这是主要内容区域）
        content_element = main_post.select_one('.cooked')

        if not content_element:
            self.logger.warning("未找到.cooked内容区域")
            return ""

        # 提取纯净的主贴内容
        return self._extract_pure_main_content(content_element)

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """移除linux.do页面中的无关元素"""
        exclude_selectors = self.config.get('extraction.linux_do.exclude_selectors', [])

        for selector in exclude_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()

    def _remove_unwanted_elements_from_post(self, post_element) -> None:
        """从主贴元素中移除无关的子元素"""
        # 移除主贴内的控制元素和用户信息
        unwanted_selectors = [
            '.quote-controls',
            '.post-controls',
            '.user-card',
            '.avatar',
            '.user-info',
            '.post-menu-area',
            '.topic-meta-data',
            '.names',
            '.username',
            '.user-title',
            '.post-date',
            '.post-number',
            '.controls',
            '.actions'
        ]

        for selector in unwanted_selectors:
            elements = post_element.select(selector)
            for element in elements:
                element.decompose()

    def _clean_linux_do_content(self, element) -> str:
        """清理linux.do的内容元素"""
        # 移除内部的控制元素和无关信息
        unwanted_selectors = [
            '.quote-controls',
            '.post-controls',
            '.user-card',
            '.avatar',
            '.user-info',
            '.names',
            '.username',
            '.user-title',
            '.post-date',
            '.post-number',
            '.controls',
            '.actions',
            '.lightbox-wrapper .meta'  # 图片元数据
        ]

        for selector in unwanted_selectors:
            for unwanted in element.select(selector):
                unwanted.decompose()

        # 保留文本和基本格式，但保持换行
        return self._clean_content_preserve_format(element)

    def _extract_raw_linux_do_content(self, element) -> str:
        """提取linux.do的原始内容，保持所有元素"""
        # 只移除控制元素，保留所有内容元素（包括图片、链接、代码等）
        unwanted_selectors = [
            '.quote-controls',
            '.post-controls',
            '.user-card',
            '.avatar',
            '.user-info',
            '.names',
            '.username',
            '.user-title',
            '.post-date',
            '.post-number',
            '.controls',
            '.actions'
            # 注意：不移除 .lightbox-wrapper .meta，保留图片相关信息
        ]

        # 创建元素副本以避免修改原始元素
        import copy
        element_copy = copy.copy(element)

        for selector in unwanted_selectors:
            for unwanted in element_copy.select(selector):
                unwanted.decompose()

        # 使用原始内容提取，保持HTML结构
        return self._extract_raw_content(element_copy)

    def _remove_replies_and_navigation(self, soup: BeautifulSoup) -> None:
        """移除所有回复帖子和导航元素"""
        # 移除所有非第一个帖子（即回复）
        reply_selectors = [
            '.topic-post:not(:first-child)',
            '[data-post-number]:not([data-post-number="1"])',
            '.post-stream .topic-post:not(:first-child)'
        ]

        for selector in reply_selectors:
            for element in soup.select(selector):
                element.decompose()

        # 移除导航和UI元素
        navigation_selectors = [
            '.topic-navigation',
            '.topic-map',
            '.suggested-topics',
            '.topic-footer-buttons',
            '.timeline-container',
            '.topic-timeline',
            '.progress-wrapper',
            '.topic-footer-main-buttons',
            '.suggested-topics-wrapper',
            '.more-topics',
            '.nav',
            '.header',
            '.footer',
            '.sidebar'
        ]

        for selector in navigation_selectors:
            for element in soup.select(selector):
                element.decompose()

    def _find_main_post(self, soup: BeautifulSoup):
        """精确找到主贴容器"""
        # 按优先级尝试不同的选择器
        main_post_selectors = [
            '#post_1',
            '[data-post-number="1"]',
            '.topic-post:first-child',
            '.post-stream .topic-post:first-child'
        ]

        for selector in main_post_selectors:
            main_post = soup.select_one(selector)
            if main_post:
                self.logger.debug(f"使用选择器找到主贴: {selector}")
                return main_post

        return None

    def _extract_pure_main_content(self, content_element) -> str:
        """提取纯净的主贴内容，保持原始格式"""
        # 创建副本避免修改原始元素
        import copy
        element_copy = copy.deepcopy(content_element)

        # 只移除控制元素，保留所有内容元素
        control_selectors = [
            '.quote-controls',
            '.post-controls',
            '.user-card',
            '.avatar',
            '.user-info',
            '.names',
            '.username',
            '.user-title',
            '.post-date',
            '.post-number',
            '.controls',
            '.actions'
        ]

        for selector in control_selectors:
            for element in element_copy.select(selector):
                element.decompose()

        # 返回完整的HTML内容，包括所有文字、图片、链接、代码等
        return str(element_copy)

    def _extract_linux_do_specific(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """针对linux.do网站的特殊提取逻辑"""
        data = {}

        # 提取回复数
        reply_element = soup.select_one('.replies')
        if reply_element:
            reply_text = reply_element.get_text(strip=True)
            reply_match = re.search(r'(\d+)', reply_text)
            if reply_match:
                data['reply_count'] = int(reply_match.group(1))

        # 提取浏览数
        view_element = soup.select_one('.views')
        if view_element:
            view_text = view_element.get_text(strip=True)
            view_match = re.search(r'(\d+)', view_text)
            if view_match:
                data['view_count'] = int(view_match.group(1))

        # 提取分类
        category_element = soup.select_one('.category-name')
        if category_element:
            data['category'] = category_element.get_text(strip=True)

        return data
    
    def _clean_content(self, element: Tag) -> str:
        """清理内容"""
        # 移除脚本和样式
        for script in element(["script", "style"]):
            script.decompose()

        # 获取文本内容
        text = element.get_text()

        # 清理空白字符
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def _clean_content_preserve_format(self, element: Tag) -> str:
        """清理内容但保持基本格式"""
        # 移除脚本和样式
        for script in element(["script", "style"]):
            script.decompose()

        # 获取文本内容，保持换行
        text = element.get_text()

        # 清理多余的空白字符，但保持换行
        lines = []
        for line in text.splitlines():
            cleaned_line = line.strip()
            if cleaned_line:  # 只保留非空行
                lines.append(cleaned_line)

        # 用双换行分隔段落，单换行分隔行
        return '\n\n'.join(lines) if lines else ""

    def _extract_raw_content(self, element: Tag) -> str:
        """提取原始内容，保持所有元素信息"""
        # 只移除脚本和样式，保留其他所有内容
        for script in element(["script", "style"]):
            script.decompose()

        # 获取内部HTML，保持所有标签和格式
        content_html = str(element)

        # 如果需要纯文本版本，也可以提供
        content_text = element.get_text(separator='\n', strip=True)

        # 返回包含更多信息的内容
        if content_html.strip():
            return content_html
        else:
            return content_text
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容（当找不到特定选择器时）"""
        # 移除不需要的元素
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # 找到文本最多的元素
        max_text_length = 0
        main_element = None
        
        for element in soup.find_all(['div', 'article', 'section', 'main']):
            text_length = len(element.get_text(strip=True))
            if text_length > max_text_length:
                max_text_length = text_length
                main_element = element
        
        if main_element:
            return self._clean_content(main_element)
        
        return ""
    
    def _extract_time_from_element(self, element: Tag) -> str:
        """从元素中提取时间"""
        # 尝试datetime属性
        datetime_attr = element.get('datetime')
        if datetime_attr:
            return datetime_attr
        
        # 尝试data-time属性
        data_time = element.get('data-time')
        if data_time:
            return data_time
        
        # 尝试文本内容
        text = element.get_text(strip=True)
        if text:
            # 简单的时间格式匹配
            time_patterns = [
                r'\d{4}-\d{2}-\d{2}',
                r'\d{4}/\d{2}/\d{2}',
                r'\d{2}-\d{2}-\d{4}',
                r'\d{2}/\d{2}/\d{4}'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group()
        
        return ""
