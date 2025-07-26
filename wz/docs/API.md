# WZ内容管理系统 - API文档

## 概述

WZ内容管理系统提供了丰富的API接口，支持内容采集、数据管理、系统配置等功能。本文档详细介绍了所有可用的API接口。

## 目录

- [统一数据库管理器 API](#统一数据库管理器-api)
- [集成采集器 API](#集成采集器-api)
- [配置管理 API](#配置管理-api)
- [CFCJ采集引擎 API](#cfcj采集引擎-api)
- [微信认证 API](#微信认证-api)
- [Web界面 API](#web界面-api)
- [数据模型](#数据模型)
- [错误处理](#错误处理)

## 统一数据库管理器 API

### 初始化

```python
from core.database import UnifiedDatabaseManager, get_db_manager

# 方式1: 直接创建实例
db_manager = UnifiedDatabaseManager()
db_manager.connect()

# 方式2: 使用全局实例
db_manager = get_db_manager()

# 方式3: 使用上下文管理器（推荐）
with UnifiedDatabaseManager() as db:
    # 在这里执行数据库操作
    pass
```

### 文章管理

#### save_article(article: Article) -> int
保存文章（插入或更新）

```python
from core.database import Article, SourceType, CrawlStatus

article = Article(
    source_type=SourceType.WECHAT.value,
    source_name="测试公众号",
    title="测试文章",
    article_url="https://example.com/article",
    content="文章内容",
    crawl_status=CrawlStatus.COMPLETED.value
)

article_id = db_manager.save_article(article)
print(f"文章ID: {article_id}")
```

#### get_article_by_id(article_id: int) -> Optional[Article]
根据ID获取文章

```python
article = db_manager.get_article_by_id(123)
if article:
    print(f"标题: {article.title}")
    print(f"来源: {article.source_name}")
```

#### get_article_by_url(source_type: str, article_url: str) -> Optional[Article]
根据URL获取文章

```python
article = db_manager.get_article_by_url("wechat", "https://example.com/article")
if article:
    print(f"文章已存在: {article.title}")
```

#### get_pending_articles(source_type: Optional[str] = None, limit: int = 100) -> List[Article]
获取待采集的文章列表

```python
# 获取所有待采集文章
pending_articles = db_manager.get_pending_articles(limit=50)

# 获取特定类型的待采集文章
wechat_articles = db_manager.get_pending_articles(source_type="wechat", limit=20)

for article in pending_articles:
    print(f"待采集: {article.title}")
```

#### update_crawl_status(article_id: int, status: str, **kwargs)
更新文章采集状态

```python
# 更新为采集成功
db_manager.update_crawl_status(
    article_id=123,
    status=CrawlStatus.COMPLETED.value,
    content="采集到的内容",
    content_html="<p>采集到的内容</p>",
    word_count=500,
    images=[{"url": "https://example.com/image.jpg", "alt": "图片"}]
)

# 更新为采集失败
db_manager.update_crawl_status(
    article_id=124,
    status=CrawlStatus.FAILED.value,
    error_message="网络连接超时"
)
```

### 发布任务管理

#### create_publish_task(task: PublishTask) -> int
创建发布任务

```python
from core.database import PublishTask, PublishStatus

task = PublishTask(
    article_id=123,
    target_platform="8wf_net",
    target_forum_id="1",
    status=PublishStatus.PENDING.value,
    priority=5
)

task_id = db_manager.create_publish_task(task)
print(f"任务ID: {task_id}")
```

#### get_pending_publish_tasks(platform: Optional[str] = None, limit: int = 50) -> List[PublishTask]
获取待处理的发布任务

```python
# 获取所有待处理任务
pending_tasks = db_manager.get_pending_publish_tasks(limit=20)

# 获取特定平台的任务
platform_tasks = db_manager.get_pending_publish_tasks(platform="8wf_net", limit=10)

for task in pending_tasks:
    print(f"待发布: 文章ID {task.article_id} -> {task.target_platform}")
```

### 统计信息

#### get_crawl_statistics() -> Dict[str, Any]
获取采集统计信息

```python
stats = db_manager.get_crawl_statistics()

for source_type, stat in stats.items():
    print(f"{source_type}:")
    print(f"  总计: {stat['total_articles']}")
    print(f"  已完成: {stat['completed']}")
    print(f"  待处理: {stat['pending']}")
    print(f"  失败: {stat['failed']}")
```

#### get_publish_statistics() -> Dict[str, Any]
获取发布统计信息

```python
stats = db_manager.get_publish_statistics()

for platform, stat in stats.items():
    print(f"{platform}:")
    print(f"  总任务: {stat['total_tasks']}")
    print(f"  已完成: {stat['completed']}")
    print(f"  待处理: {stat['pending']}")
```

## 集成采集器 API

### 初始化

```python
from core.integrated_crawler import IntegratedCrawler, create_integrated_crawler

# 方式1: 直接创建
crawler = IntegratedCrawler()
crawler.initialize()

# 方式2: 使用工厂函数
crawler = create_integrated_crawler()

# 方式3: 使用上下文管理器（推荐）
with IntegratedCrawler() as crawler:
    # 在这里执行采集操作
    pass
```

### 批量采集

#### batch_crawl(source_type: Optional[str] = None, limit: int = 100, batch_size: int = 5) -> Dict[str, Any]
从数据库批量采集文章

```python
with IntegratedCrawler() as crawler:
    # 采集所有待处理文章
    result = crawler.batch_crawl(limit=50, batch_size=5)
    
    # 采集特定类型文章
    result = crawler.batch_crawl(source_type="wechat", limit=20, batch_size=3)
    
    print(f"处理结果:")
    print(f"  总计: {result['total_processed']}")
    print(f"  成功: {result['successful']}")
    print(f"  失败: {result['failed']}")
    print(f"  耗时: {result.get('duration', 0):.2f}秒")
```

### URL采集

#### crawl_by_urls(urls: List[str], source_type: str = "external", source_name: str = "手动导入") -> Dict[str, Any]
根据URL列表采集文章

```python
urls = [
    "https://linux.do/t/topic/123456",
    "https://linux.do/t/topic/789012",
    "https://example.com/article"
]

with IntegratedCrawler() as crawler:
    result = crawler.crawl_by_urls(
        urls=urls,
        source_type="external",
        source_name="批量导入"
    )
    
    print(f"采集结果:")
    print(f"  总计: {result['total']}")
    print(f"  成功: {result['summary']['success']}")
    print(f"  失败: {result['summary']['failed']}")
    print(f"  跳过: {result['summary']['skipped']}")
    
    # 查看详细结果
    for item in result['results']:
        print(f"  {item['url']}: {item['status']}")
```

### 单篇采集

#### crawl_single_article(article: Article) -> bool
采集单篇文章

```python
from core.database import Article

article = Article(
    id=123,
    title="测试文章",
    article_url="https://linux.do/t/topic/123456",
    source_type="linux_do"
)

with IntegratedCrawler() as crawler:
    success = crawler.crawl_single_article(article)
    if success:
        print("采集成功")
    else:
        print("采集失败")
```

### 统计信息

#### get_crawl_statistics() -> Dict[str, Any]
获取采集统计信息

```python
with IntegratedCrawler() as crawler:
    stats = crawler.get_crawl_statistics()
    
    print("数据库统计:")
    for source_type, stat in stats['database_stats'].items():
        print(f"  {source_type}: {stat['total_articles']} 篇文章")
    
    print("会话统计:")
    session_stats = stats['session_stats']
    print(f"  本次处理: {session_stats.get('total_processed', 0)}")
    print(f"  成功: {session_stats.get('successful', 0)}")
    print(f"  失败: {session_stats.get('failed', 0)}")
```

## 配置管理 API

### 基本操作

```python
from core.config import get_config, set_config_file, reload_config

# 获取全局配置
config = get_config()

# 设置配置文件路径
set_config_file("/path/to/custom/config.json")

# 重新加载配置
reload_config()
```

### 读取配置

#### get(key: str, default: Any = None) -> Any
获取配置值

```python
# 获取数据库主机
db_host = config.get("database.host")

# 获取配置值，提供默认值
batch_size = config.get("wechat.batch_size", 10)

# 获取复杂配置
platforms = config.get("publisher.platforms", {})
```

### 设置配置

#### set(key: str, value: Any) -> bool
设置配置值

```python
# 设置简单值
config.set("wechat.batch_size", 20)

# 设置布尔值
config.set("cfcj.enabled", True)

# 保存配置到文件
config.save_config()
```

### 配置验证

#### validate_config() -> Dict[str, list]
验证配置的有效性

```python
errors = config.validate_config()

if errors:
    print("配置验证失败:")
    for section, error_list in errors.items():
        for error in error_list:
            print(f"  [{section}] {error}")
else:
    print("配置验证通过")
```

### 路径管理

```python
# 获取数据文件路径
data_path = config.get_data_path("test.json")
print(f"数据文件路径: {data_path}")

# 获取日志文件路径
log_path = config.get_logs_path("app.log")
print(f"日志文件路径: {log_path}")

# 获取临时文件路径
temp_path = config.get_temp_path("temp_file.txt")
print(f"临时文件路径: {temp_path}")
```

## CFCJ采集引擎 API

### 单篇文章采集

```python
from cfcj.api import crawl_single_article, CFCJAPI

# 方式1: 使用便捷函数
result = crawl_single_article("https://linux.do/t/topic/123456")

if result:
    print(f"标题: {result.get('title')}")
    print(f"内容长度: {len(result.get('content', ''))}")
    print(f"字数: {result.get('word_count', 0)}")
    print(f"图片数量: {len(result.get('images', []))}")
else:
    print("采集失败")

# 方式2: 使用API类
api = CFCJAPI()
result = api.crawl_article("https://linux.do/t/topic/123456")
```

### 批量采集

```python
urls = [
    "https://linux.do/t/topic/123456",
    "https://linux.do/t/topic/789012"
]

api = CFCJAPI()
results = api.crawl_articles_batch(urls)

for i, result in enumerate(results):
    print(f"文章 {i+1}:")
    if result:
        print(f"  标题: {result.get('title')}")
        print(f"  状态: 成功")
    else:
        print(f"  状态: 失败")
```

### 站点检测

```python
from cfcj.core.site_detector import SiteDetector

detector = SiteDetector()

# 检测站点类型
site_info = detector.detect_site("https://linux.do/t/topic/123456")
print(f"站点类型: {site_info['site_type']}")
print(f"需要登录: {site_info['requires_login']}")

# 获取支持的站点列表
supported_sites = detector.get_supported_sites()
for site in supported_sites:
    print(f"支持站点: {site}")
```

## 微信认证 API

### 登录管理

```python
from wechat_mp_auth.auth import WeChatAuth

# 初始化认证
auth = WeChatAuth()

# 检查登录状态
if auth.check_login_status():
    print("✅ 微信登录状态有效")
else:
    print("❌ 微信登录状态无效")

# 执行登录
success = auth.login()
if success:
    print("✅ 登录成功")
else:
    print("❌ 登录失败")

# 获取认证信息
auth_info = auth.get_auth_info()
print(f"Token: {auth_info.get('token', 'N/A')}")
```

### Cookie管理

```python
# 保存Cookie
auth.save_cookies()

# 加载Cookie
auth.load_cookies()

# 清除Cookie
auth.clear_cookies()
```

## Web界面 API

### Flask路由

WZ系统的Web界面提供了RESTful API接口：

#### GET /api/status
获取系统状态

```bash
curl http://localhost:5000/api/status
```

响应示例：
```json
{
  "status": "ok",
  "database": "connected",
  "crawl_stats": {
    "wechat": {"total": 150, "completed": 120, "pending": 30},
    "linux_do": {"total": 50, "completed": 45, "pending": 5}
  }
}
```

#### POST /api/crawl
触发采集任务

```bash
curl -X POST http://localhost:5000/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"source_type": "wechat", "limit": 10}'
```

#### GET /api/articles
获取文章列表

```bash
curl "http://localhost:5000/api/articles?page=1&limit=20&source_type=wechat"
```

#### POST /api/articles
添加新文章

```bash
curl -X POST http://localhost:5000/api/articles \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "article_url": "https://example.com/article",
    "source_type": "external",
    "source_name": "外部导入"
  }'
```

## 数据模型

### Article 模型

```python
@dataclass
class Article:
    id: Optional[int] = None
    source_type: str = ""                    # 来源类型: wechat, linux_do, nodeseek, external
    source_name: str = ""                    # 来源名称
    source_id: Optional[str] = None          # 来源平台ID
    title: str = ""                          # 文章标题
    article_url: str = ""                    # 文章URL
    author: Optional[str] = None             # 作者
    publish_timestamp: Optional[datetime] = None  # 发布时间
    crawl_status: str = "pending"            # 采集状态
    crawl_attempts: int = 0                  # 采集尝试次数
    crawl_error: Optional[str] = None        # 采集错误信息
    crawled_at: Optional[datetime] = None    # 采集完成时间
    content: Optional[str] = None            # 文章内容（纯文本）
    content_html: Optional[str] = None       # 文章内容（HTML）
    word_count: int = 0                      # 字数统计
    images: Optional[List[Dict]] = None      # 图片信息
    links: Optional[List[Dict]] = None       # 链接信息
    tags: Optional[List[str]] = None         # 标签
    ai_title: Optional[str] = None           # AI改写标题
    ai_content: Optional[str] = None         # AI改写内容
    ai_summary: Optional[str] = None         # AI生成摘要
    publish_status: Optional[Dict[str, str]] = None  # 发布状态
    fetched_at: Optional[datetime] = None    # 链接获取时间
    updated_at: Optional[datetime] = None    # 最后更新时间
    created_at: Optional[datetime] = None    # 记录创建时间
```

### PublishTask 模型

```python
@dataclass
class PublishTask:
    id: Optional[int] = None
    article_id: int = 0                      # 关联文章ID
    target_platform: str = ""               # 目标平台: 8wf_net, 00077_top, 1rmb_net
    target_forum_id: Optional[str] = None   # 目标版块ID
    target_category: Optional[str] = None   # 目标分类
    status: str = "pending"                  # 任务状态
    priority: int = 5                        # 优先级(1-10)
    attempts: int = 0                        # 尝试次数
    max_attempts: int = 3                    # 最大尝试次数
    published_url: Optional[str] = None      # 发布后的URL
    published_id: Optional[str] = None       # 发布后的帖子ID
    error_message: Optional[str] = None      # 错误信息
    response_data: Optional[Dict] = None     # 发布响应数据
    custom_title: Optional[str] = None       # 自定义标题
    custom_content: Optional[str] = None     # 自定义内容
    publish_config: Optional[Dict] = None    # 发布配置
    scheduled_at: Optional[datetime] = None  # 计划发布时间
    started_at: Optional[datetime] = None    # 开始处理时间
    completed_at: Optional[datetime] = None  # 完成时间
    created_at: Optional[datetime] = None    # 创建时间
    updated_at: Optional[datetime] = None    # 更新时间
```

## 错误处理

### 异常类型

```python
from cfcj.utils.exceptions import CFCJError

# CFCJ相关异常
try:
    result = crawl_single_article(url)
except CFCJError as e:
    print(f"采集错误: {e}")
    print(f"错误类型: {type(e).__name__}")

# 数据库相关异常
try:
    db_manager.connect()
except Exception as e:
    print(f"数据库错误: {e}")

# 配置相关异常
try:
    config.load_config()
except Exception as e:
    print(f"配置错误: {e}")
```

### 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| DB_CONNECTION_ERROR | 数据库连接失败 | 检查数据库服务和配置 |
| CRAWL_TIMEOUT | 采集超时 | 增加超时时间或检查网络 |
| SITE_NOT_SUPPORTED | 不支持的站点 | 添加站点配置或使用通用提取器 |
| LOGIN_REQUIRED | 需要登录 | 检查登录状态或重新登录 |
| RATE_LIMIT_EXCEEDED | 请求频率过高 | 增加请求间隔 |

### 重试机制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise e
                    print(f"尝试 {attempt + 1} 失败: {e}")
                    time.sleep(delay * (attempt + 1))
            return None
        return wrapper
    return decorator

# 使用重试装饰器
@retry(max_attempts=3, delay=2)
def crawl_with_retry(url):
    return crawl_single_article(url)
```

---

*API文档最后更新: 2025-07-09*
