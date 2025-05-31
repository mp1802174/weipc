# CFCJ - Cloudflare Content Crawler

CFCJ (Cloudflare Content Crawler) 是一个专门用于采集有Cloudflare保护的网站内容的Python模块。它能够绕过Cloudflare的反爬虫保护，提取结构化的文章数据。

## 功能特点

- ✅ **绕过Cloudflare保护**: 使用undetected-chromedriver和DrissionPage技术
- ✅ **登录认证支持**: 支持用户名密码登录和Cookie管理
- ✅ **结构化数据提取**: 自动提取标题、内容、作者、时间等信息
- ✅ **批量采集**: 支持批量处理多个URL
- ✅ **错误处理和重试**: 完善的错误处理和重试机制
- ✅ **模块化设计**: 清晰的模块结构，便于扩展和集成
- ✅ **配置管理**: 灵活的配置系统
- ✅ **测试覆盖**: 完整的测试用例

## 安装要求

### Python版本
- Python 3.7+

### 依赖安装

```bash
# 进入cfcj目录
cd wz/cfcj

# 安装依赖
pip install -r requirements.txt

# 或者手动安装核心依赖
pip install beautifulsoup4 lxml requests undetected-chromedriver DrissionPage selenium
```

### Chrome浏览器
需要安装Chrome浏览器，undetected-chromedriver会自动管理ChromeDriver。

## 快速开始

### 1. 基本用法

```python
from wz.cfcj.api import CFCJAPI

# 创建API实例
api = CFCJAPI()

# 采集单篇文章
result = api.crawl_article("https://linux.do/t/topic/690688/48")

print(f"标题: {result['title']}")
print(f"内容: {result['content'][:200]}...")
```

### 2. 命令行使用

```bash
# 采集单个URL
python main.py https://linux.do/t/topic/690688/48

# 批量采集
python main.py --urls https://linux.do/t/topic/690688/48 https://linux.do/

# 显示浏览器窗口（调试用）
python main.py --no-headless https://linux.do/t/topic/690688/48

# 测试连接
python main.py --test-connection https://linux.do/

# 交互模式
python main.py
```

### 3. 需要登录的网站

```python
from wz.cfcj.api import CFCJAPI

api = CFCJAPI()

# 登录凭据
login_credentials = {
    'username': 'your_username',
    'password': 'your_password',
    'login_url': 'https://example.com/login',
    'username_selector': '#username',  # 可选，默认会自动检测
    'password_selector': '#password',  # 可选
    'submit_selector': '#login-button'  # 可选
}

# 采集需要登录的文章
result = api.crawl_article(
    "https://example.com/protected-article",
    login_required=True,
    login_credentials=login_credentials
)
```

## 项目结构

```
wz/cfcj/
├── __init__.py              # 模块入口
├── main.py                  # 命令行主程序
├── api.py                   # 主要API接口
├── requirements.txt         # 依赖列表
├── README.md               # 说明文档
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py         # 配置管理
├── core/                   # 核心功能
│   ├── __init__.py
│   ├── crawler.py          # 爬虫核心
│   └── extractor.py        # 内容提取
├── auth/                   # 认证模块
│   ├── __init__.py
│   └── manager.py          # 认证管理
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── exceptions.py       # 异常定义
│   └── helpers.py          # 工具函数
├── tests/                  # 测试模块
│   ├── __init__.py
│   ├── test_crawler.py     # 爬虫测试
│   └── test_linux_do.py    # Linux.do专项测试
└── data/                   # 数据目录（自动创建）
    ├── cfcj_config.json    # 配置文件
    └── cookies.json        # Cookie存储
```

## 配置说明

CFCJ使用JSON格式的配置文件，支持以下配置项：

```json
{
  "browser": {
    "headless": true,
    "window_size": [1920, 1080],
    "user_agent": "Mozilla/5.0...",
    "timeout": 30,
    "page_load_timeout": 60,
    "implicit_wait": 10
  },
  "crawler": {
    "max_retries": 3,
    "retry_delay": 5,
    "cf_wait_time": 10,
    "request_delay": 2
  },
  "auth": {
    "cookie_file": "cookies.json",
    "session_timeout": 3600,
    "auto_login": true
  },
  "extraction": {
    "content_selectors": [".post-content", ".article-content"],
    "title_selectors": ["h1.title", ".post-title"],
    "author_selectors": [".author", ".post-author"],
    "time_selectors": [".post-time", "time"]
  }
}
```

## API参考

### CFCJAPI类

#### 主要方法

- `crawl_article(url, login_required=False, login_credentials=None)`: 采集单篇文章
- `crawl_articles_batch(urls, login_required=False, login_credentials=None, batch_size=5)`: 批量采集文章
- `test_connection(url)`: 测试连接
- `get_config()`: 获取配置
- `set_config(key, value)`: 设置配置
- `clear_auth_data()`: 清除认证数据

#### 返回数据格式

```python
{
    'url': 'https://example.com/article',
    'title': '文章标题',
    'content': '文章内容...',
    'author': '作者名',
    'publish_time': '2024-01-01',
    'tags': ['标签1', '标签2'],
    'images': [{'url': '图片URL', 'alt': '图片描述'}],
    'links': [{'url': '链接URL', 'text': '链接文本'}],
    'word_count': 1500,
    'extracted_at': '2024-01-01T12:00:00'
}
```

## 测试

### 运行所有测试

```bash
python main.py --test
```

### 运行特定测试

```bash
# 基础功能测试
python -m unittest wz.cfcj.tests.test_crawler

# Linux.do专项测试
python -m unittest wz.cfcj.tests.test_linux_do

# 手动测试（显示浏览器）
python wz/cfcj/tests/test_linux_do.py --manual
```

### 测试目标URL

项目包含对以下URL的专项测试：
- `https://linux.do/t/topic/690688/48`

## 故障排除

### 常见问题

1. **Chrome浏览器问题**
   ```bash
   # 确保Chrome已安装
   google-chrome --version
   
   # 或者手动指定ChromeDriver路径
   ```

2. **Cloudflare检测**
   - 尝试增加等待时间：`config.set('crawler.cf_wait_time', 20)`
   - 使用非无头模式：`config.set('browser.headless', False)`
   - 检查User-Agent设置

3. **登录失败**
   - 检查登录选择器是否正确
   - 确认用户名密码正确
   - 查看是否有验证码或其他验证机制

4. **内容提取不完整**
   - 检查网站的HTML结构
   - 自定义内容选择器
   - 增加页面加载等待时间

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者使用命令行
python main.py --verbose --no-headless <url>
```

## 扩展开发

### 添加新网站支持

1. 在`core/extractor.py`中添加特定网站的提取逻辑
2. 在`config/settings.py`中添加网站特定的选择器配置
3. 创建对应的测试用例

### 自定义认证方式

继承`AuthManager`类并重写相关方法：

```python
from wz.cfcj.auth.manager import AuthManager

class CustomAuthManager(AuthManager):
    def custom_login_method(self, driver_or_page):
        # 实现自定义登录逻辑
        pass
```

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request！

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持Cloudflare保护网站采集
- 支持登录认证
- 支持批量采集
- 完整的测试覆盖
