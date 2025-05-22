# 微信公众号文章抓取模块 (WZZQ)

WZZQ 是一个用于抓取微信公众号文章并存储到MySQL数据库的工具。

## 功能特点

- 从配置文件加载公众号列表
- 自动获取公众号文章列表
- 提取文章标题、链接、发布时间等信息
- 将文章信息存储到MySQL数据库

## 安装与环境要求

### 依赖库

```
requests>=2.28.1
lxml>=4.9.1
mysql-connector-python>=8.0.32
tqdm>=4.64.1
python-dateutil>=2.8.2
```

安装依赖：

```bash
pip install -r wz/wzzq/requirements.txt
```

### 认证配置

本工具需要从 `wz/data/id_info.json` 文件中读取微信公众平台的token和cookie信息。请确保该文件存在并包含有效的认证信息。

认证信息格式示例：

```json
{
    "token": "12345678",
    "cookie": "your_cookie_string_here"
}
```

### 公众号配置

公众号列表配置在 `wz/data/name2fakeid.json` 文件中，格式为公众号名称到fakeid的映射。

格式示例：

```json
{
    "公众号1": "fakeid1",
    "公众号2": "fakeid2"
}
```

## 使用方法

### 命令行运行

```bash
# 抓取所有已配置的公众号，每个公众号抓取10篇文章（默认）
python wz/crawl_wechat.py

# 抓取指定公众号
python wz/crawl_wechat.py --account "公众号名称"

# 指定每个公众号抓取的文章数量
python wz/crawl_wechat.py --limit 20

# 调试模式，只打印不保存到数据库
python wz/crawl_wechat.py --debug
```

### 作为模块导入

```python
from wz.wzzq import WechatCrawler, DatabaseManager

# 创建抓取器
crawler = WechatCrawler()

# 获取指定公众号的文章
articles = crawler.get_articles("公众号名称", limit=10)

# 或者获取所有已配置公众号的文章
all_articles = crawler.crawl_all_accounts(limit_per_account=10)

# 保存到数据库
with DatabaseManager() as db:
    db.save_articles_batch(articles)
```

## 数据库配置

默认数据库配置：

- 主机：140.238.201.162
- 端口：3306
- 用户名：cj
- 密码：760516
- 数据库名：cj
- 字符集：utf8mb4

表结构：

```sql
CREATE TABLE `wechat_articles` (
  `id` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `account_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公众号名称',
  `title` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文章标题',
  `article_url` varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文章链接',
  `publish_timestamp` datetime NOT NULL COMMENT '文章发布时间',
  `source_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'wechat' COMMENT '来源类型: wechat, external_link等',
  `Workspaceed_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取入库时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聚合的微信文章表';
``` 