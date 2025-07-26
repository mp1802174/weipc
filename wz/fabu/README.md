# WZ系统论坛发布模块

## 功能概述

本模块负责将WZ系统采集的微信公众号文章自动发布到Discuz X3.5论坛。

## 模块结构

```
fabu/
├── __init__.py              # 模块初始化
├── README.md               # 模块说明文档
├── config.py               # 发布配置管理
├── discuz_client.py        # Discuz数据库客户端
├── forum_publisher.py      # 单篇文章发布器
├── batch_publisher.py      # 批量发布器
├── utils.py               # 工具函数
└── tests/                 # 测试文件
    ├── __init__.py
    ├── test_discuz_client.py
    ├── test_forum_publisher.py
    └── test_batch_publisher.py
```

## 核心功能

### 1. 单篇文章发布 (ForumPublisher)
- 将单篇微信文章发布到指定Discuz论坛版块
- 支持标题和内容的自动处理
- 自动更新论坛统计信息

### 2. 批量发布 (BatchPublisher)
- 一次性发布所有未发布的文章
- 实时进度显示
- 错误处理和重试机制
- 发布间隔控制

### 3. Discuz数据库操作 (DiscuzClient)
- 安全的数据库事务操作
- 自动ID生成
- 统计信息更新

## 发布流程

1. 查询待发布文章 (`forum_published IS NULL`)
2. 为每篇文章执行：
   - 生成新的TID和PID
   - 插入 `pre_forum_thread` 记录
   - 插入 `pre_forum_post` 记录
   - 更新 `pre_forum_forum` 统计
   - 更新 `pre_common_member` 统计
   - 标记 `wechat_articles.forum_published = 1`
3. 提供发布结果统计

## 配置参数

- **目标版块**: FID = 2 (砂舞分享)
- **发布用户**: UID = 4 (砂鱼)
- **发布间隔**: 60-120秒随机
- **数据库**: 140.238.201.162:3306/00077

## 使用示例

```python
from fabu import BatchPublisher

# 批量发布
publisher = BatchPublisher()
result = publisher.publish_all()
print(f"发布完成: 成功{result['success']}篇, 失败{result['failed']}篇")
```
