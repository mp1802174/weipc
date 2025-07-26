"""
CFCJ配置管理模块
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


class CFCJConfig:
    """CFCJ配置管理类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前模块的data目录
        """
        if config_dir is None:
            self.config_dir = Path(__file__).parent.parent / "data"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "cfcj_config.json"
        
        # 默认配置
        self.default_config = {
            "browser": {
                "headless": True,
                "window_size": [1920, 1080],
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "timeout": 30,
                "page_load_timeout": 60,
                "implicit_wait": 10
            },
            "crawler": {
                "max_retries": 2,
                "retry_delay": 3,
                "cf_wait_time": 8,
                "request_delay": 1
            },
            "auth": {
                "cookie_file": "cookies.json",
                "session_timeout": 3600,
                "auto_login": True
            },
            "extraction": {
                "content_selectors": [
                    ".post-content",
                    ".article-content",
                    ".content",
                    "[data-post-content]"
                ],
                "title_selectors": [
                    "h1.title",
                    ".post-title",
                    "h1",
                    ".article-title"
                ],
                "author_selectors": [
                    ".author",
                    ".post-author",
                    "[data-author]"
                ],
                "time_selectors": [
                    ".post-time",
                    ".publish-time",
                    "time",
                    "[datetime]"
                ],
                "linux_do": {
                    "title_selectors": [
                        "a.fancy-title span[dir='auto']",
                        ".fancy-title span[dir='auto']",
                        "h1"
                    ],
                    "main_post_selector": "#post_1, .topic-post:first-child, [data-post-number='1']",
                    "content_selectors": [
                        ".cooked"
                    ],
                    "exclude_selectors": [
                        ".nav",
                        ".header",
                        ".footer",
                        ".sidebar",
                        ".aside",
                        ".comments",
                        ".replies",
                        ".user-info",
                        ".avatar",
                        ".controls",
                        ".buttons",
                        ".topic-meta-data",
                        ".topic-map",
                        ".suggested-topics",
                        ".topic-footer-buttons",
                        ".post-menu-area",
                        ".topic-navigation",
                        ".quote-controls",
                        ".post-controls",
                        ".user-card",
                        ".topic-status-info",
                        ".topic-post:not(:first-child)",
                        "[data-post-number]:not([data-post-number='1'])",
                        ".post-stream .topic-post:not(:first-child)",
                        ".timeline-container",
                        ".topic-timeline",
                        ".progress-wrapper",
                        ".topic-footer-main-buttons",
                        ".suggested-topics-wrapper",
                        ".more-topics"
                    ],
                    "author_selectors": [
                        ".topic-meta-data .creator a",
                        ".names .first a",
                        ".topic-avatar .username",
                        ".post .username"
                    ],
                    "time_selectors": [
                        ".topic-meta-data .created-at",
                        ".post-date",
                        ".relative-date",
                        "time.relative-date"
                    ]
                }
            },
            "sites": {
                "linux.do": {
                    "name": "Linux.do",
                    "domain": "linux.do",
                    "requires_login": True,
                    "login_config": {
                        "login_url": "https://linux.do/login",
                        "username_selector": "#login-account-name",
                        "password_selector": "#login-account-password",
                        "submit_selector": "#login-button",
                        "success_indicators": [
                            ".header-dropdown-toggle",
                            ".current-user",
                            ".user-menu"
                        ]
                    },
                    "extraction": {
                        "title_selectors": [
                            "a.fancy-title span[dir='auto']",
                            ".fancy-title span[dir='auto']",
                            "h1"
                        ],
                        "main_post_selector": "#post_1, .topic-post:first-child, [data-post-number='1']",
                        "content_selectors": [
                            ".cooked"
                        ],
                        "author_selectors": [
                            ".topic-meta-data .creator a",
                            ".names .first a",
                            ".topic-avatar .username",
                            ".post .username"
                        ],
                        "time_selectors": [
                            ".topic-meta-data .created-at",
                            ".post-date",
                            ".relative-date",
                            "time.relative-date"
                        ],
                        "exclude_selectors": [
                            ".nav",
                            ".header",
                            ".footer",
                            ".sidebar",
                            ".aside",
                            ".comments",
                            ".replies",
                            ".user-info",
                            ".avatar",
                            ".controls",
                            ".buttons",
                            ".topic-meta-data",
                            ".topic-map",
                            ".suggested-topics",
                            ".topic-footer-buttons",
                            ".post-menu-area",
                            ".topic-navigation",
                            ".quote-controls",
                            ".post-controls",
                            ".user-card",
                            ".topic-status-info",
                            ".topic-post:not(:first-child)",
                            "[data-post-number]:not([data-post-number='1'])",
                            ".post-stream .topic-post:not(:first-child)",
                            ".timeline-container",
                            ".topic-timeline",
                            ".progress-wrapper",
                            ".topic-footer-main-buttons",
                            ".suggested-topics-wrapper",
                            ".more-topics"
                        ]
                    }
                },
                "nodeseek.com": {
                    "name": "NodeSeek",
                    "domain": "nodeseek.com",
                    "requires_login": True,
                    "login_config": {
                        "login_url": "https://www.nodeseek.com/signIn.html",
                        "username_selector": "input[name='username']",
                        "password_selector": "input[name='password']",
                        "submit_selector": "button[type='submit']",
                        "success_indicators": [
                            ".user-menu",
                            ".logout",
                            ".user-avatar"
                        ]
                    },
                    "extraction": {
                        "content_selectors": [
                            ".post-content",
                            ".message-content",
                            ".content"
                        ],
                        "title_selectors": [
                            "h1.title",
                            ".post-title",
                            "h1"
                        ],
                        "author_selectors": [
                            ".author-name",
                            ".username",
                            ".user-info .name"
                        ],
                        "time_selectors": [
                            ".post-time",
                            ".created-time",
                            "time"
                        ],
                        "exclude_selectors": [
                            ".sidebar",
                            ".navigation",
                            ".footer",
                            ".ads",
                            ".comments-section"
                        ]
                    }
                },
                "mp.weixin.qq.com": {
                    "name": "微信公众号",
                    "domain": "mp.weixin.qq.com",
                    "requires_login": False,
                    "extraction": {
                        "content_selectors": [
                            "#js_content",
                            ".rich_media_content",
                            ".article-content"
                        ],
                        "title_selectors": [
                            "#activity-name",
                            ".rich_media_title",
                            "h1"
                        ],
                        "author_selectors": [
                            ".rich_media_meta_nickname",
                            ".author",
                            "#js_name"
                        ],
                        "time_selectors": [
                            "#publish_time",
                            ".rich_media_meta_text",
                            ".publish-time"
                        ],
                        "exclude_selectors": [
                            ".rich_media_tool",
                            ".share_media",
                            ".qr_code_pc",
                            ".reward_area",
                            ".comment_area"
                        ],
                        # 差异化内容采集规则
                        "author_based_rules": {
                            "舞林攻略指南": {
                                "content_start_marker": "下方小卡片关注 星标置顶",
                                "content_end_marker": "——节选自舞林攻略",
                                "include_markers": False,  # 是否包含标识符本身
                                "fallback_to_full": True   # 如果找不到标识符，是否回退到完整内容
                            }
                            # 可以继续添加其他公众号的规则
                        }
                    }
                }
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                return self._merge_config(self.default_config, config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return self.default_config.copy()
        else:
            # 创建默认配置文件
            self.save_config(self.default_config)
            return self.default_config.copy()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """保存配置文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()
    
    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置"""
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result
    
    @property
    def data_dir(self) -> Path:
        """获取数据目录路径"""
        return self.config_dir
    
    @property
    def cookie_file_path(self) -> Path:
        """获取Cookie文件路径"""
        return self.config_dir / self.get('auth.cookie_file', 'cookies.json')
