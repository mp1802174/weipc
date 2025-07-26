#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目统一数据库管理器
提供标准化的数据库操作接口，支持所有模块的数据库需求
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union, Tuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum

# 尝试导入mysql-connector-python或PyMySQL
try:
    import mysql.connector
    from mysql.connector import Error
    USING_PYMYSQL = False
except ImportError:
    # 如果mysql-connector-python不可用，尝试导入PyMySQL
    try:
        import pymysql as mysql
        from pymysql import Error
        mysql.connector = mysql  # 兼容性处理
        USING_PYMYSQL = True
    except ImportError:
        raise ImportError("请安装MySQL连接器库：pip install mysql-connector-python==8.0.32 或 pip install PyMySQL")

from .config import get_config

logger = logging.getLogger(__name__)

class SourceType(Enum):
    """内容来源类型"""
    WECHAT = "wechat"
    LINUX_DO = "linux_do"
    NODESEEK = "nodeseek"
    EXTERNAL = "external"

class CrawlStatus(Enum):
    """采集状态"""
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class PublishStatus(Enum):
    """发布状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Article:
    """文章数据模型"""
    id: Optional[int] = None
    source_type: str = ""
    source_name: str = ""
    source_id: Optional[str] = None
    title: str = ""
    article_url: str = ""
    author: Optional[str] = None
    publish_timestamp: Optional[datetime] = None
    crawl_status: str = CrawlStatus.PENDING.value
    crawl_attempts: int = 0
    crawl_error: Optional[str] = None
    crawled_at: Optional[datetime] = None
    content: Optional[str] = None
    content_html: Optional[str] = None
    word_count: int = 0
    images: Optional[List[Dict]] = None
    links: Optional[List[Dict]] = None
    tags: Optional[List[str]] = None
    ai_title: Optional[str] = None
    ai_content: Optional[str] = None
    ai_summary: Optional[str] = None
    publish_status: Optional[Dict[str, str]] = None
    fetched_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

@dataclass
class PublishTask:
    """发布任务数据模型"""
    id: Optional[int] = None
    article_id: int = 0
    target_platform: str = ""
    target_forum_id: Optional[str] = None
    target_category: Optional[str] = None
    status: str = PublishStatus.PENDING.value
    priority: int = 5
    attempts: int = 0
    max_attempts: int = 3
    published_url: Optional[str] = None
    published_id: Optional[str] = None
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None
    custom_title: Optional[str] = None
    custom_content: Optional[str] = None
    publish_config: Optional[Dict] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UnifiedDatabaseManager:
    """统一数据库管理器"""
    
    def __init__(self, config=None):
        """
        初始化数据库管理器
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or get_config()
        self.connection = None
        self._connection_pool = []
        self._pool_size = self.config.database.pool_size
        
    def connect(self) -> bool:
        """
        连接数据库

        Returns:
            bool: 是否连接成功
        """
        try:
            db_config = self.config.database

            if USING_PYMYSQL:
                # 使用PyMySQL
                self.connection = mysql.connect(
                    host=db_config.host,
                    port=db_config.port,
                    user=db_config.user,
                    password=db_config.password,
                    database=db_config.database,
                    charset=db_config.charset,
                    autocommit=db_config.autocommit,
                    cursorclass=mysql.cursors.DictCursor
                )
            else:
                # 使用mysql-connector-python
                self.connection = mysql.connector.connect(
                    host=db_config.host,
                    port=db_config.port,
                    user=db_config.user,
                    password=db_config.password,
                    database=db_config.database,
                    charset=db_config.charset,
                    autocommit=db_config.autocommit
                )

            logger.info(f"数据库连接成功: {db_config.host}:{db_config.port}/{db_config.database}")
            return True

        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("数据库连接已关闭")
            except Exception as e:
                logger.error(f"关闭数据库连接失败: {e}")
            finally:
                self.connection = None
    
    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        if not self.connection:
            if not self.connect():
                raise Exception("无法连接到数据库")

        if USING_PYMYSQL:
            cursor = self.connection.cursor()
        else:
            cursor = self.connection.cursor(dictionary=True)

        try:
            yield cursor
        except Exception as e:
            if not USING_PYMYSQL or not self.config.database.autocommit:
                self.connection.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        执行查询SQL
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            List[Dict]: 查询结果
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def execute_update(self, sql: str, params: Optional[Tuple] = None) -> int:
        """
        执行更新SQL

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            int: 影响的行数
        """
        with self.get_cursor() as cursor:
            result = cursor.execute(sql, params)
            if not self.config.database.autocommit:
                self.connection.commit()
            return result
    
    def execute_insert(self, sql: str, params: Optional[Tuple] = None) -> int:
        """
        执行插入SQL

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            int: 插入记录的ID
        """
        with self.get_cursor() as cursor:
            cursor.execute(sql, params)
            if not self.config.database.autocommit:
                self.connection.commit()
            return cursor.lastrowid
    
    # ========== 文章管理方法 ==========
    
    def save_article(self, article: Article) -> int:
        """
        保存文章
        
        Args:
            article: 文章对象
            
        Returns:
            int: 文章ID
        """
        if article.id:
            return self.update_article(article)
        else:
            return self.insert_article(article)
    
    def insert_article(self, article: Article) -> int:
        """插入新文章"""
        sql = """
        INSERT INTO articles (
            source_type, source_name, source_id, title, article_url, author,
            publish_timestamp, crawl_status, crawl_attempts, crawl_error,
            crawled_at, content, content_html, word_count, images, links, tags,
            ai_title, ai_content, ai_summary, publish_status, fetched_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        params = (
            article.source_type, article.source_name, article.source_id,
            article.title, article.article_url, article.author,
            article.publish_timestamp, article.crawl_status, article.crawl_attempts,
            article.crawl_error, article.crawled_at, article.content,
            article.content_html, article.word_count,
            json.dumps(article.images) if article.images else None,
            json.dumps(article.links) if article.links else None,
            json.dumps(article.tags) if article.tags else None,
            article.ai_title, article.ai_content, article.ai_summary,
            json.dumps(article.publish_status) if article.publish_status else None,
            article.fetched_at or datetime.now()
        )
        
        return self.execute_insert(sql, params)
    
    def update_article(self, article: Article) -> int:
        """更新文章"""
        sql = """
        UPDATE articles SET
            source_type = %s, source_name = %s, source_id = %s, title = %s,
            article_url = %s, author = %s, publish_timestamp = %s,
            crawl_status = %s, crawl_attempts = %s, crawl_error = %s,
            crawled_at = %s, content = %s, content_html = %s, word_count = %s,
            images = %s, links = %s, tags = %s, ai_title = %s, ai_content = %s,
            ai_summary = %s, publish_status = %s, updated_at = NOW()
        WHERE id = %s
        """
        
        params = (
            article.source_type, article.source_name, article.source_id,
            article.title, article.article_url, article.author,
            article.publish_timestamp, article.crawl_status, article.crawl_attempts,
            article.crawl_error, article.crawled_at, article.content,
            article.content_html, article.word_count,
            json.dumps(article.images) if article.images else None,
            json.dumps(article.links) if article.links else None,
            json.dumps(article.tags) if article.tags else None,
            article.ai_title, article.ai_content, article.ai_summary,
            json.dumps(article.publish_status) if article.publish_status else None,
            article.id
        )
        
        return self.execute_update(sql, params)
    
    def get_article_by_id(self, article_id: int) -> Optional[Article]:
        """根据ID获取文章"""
        sql = "SELECT * FROM articles WHERE id = %s"
        results = self.execute_query(sql, (article_id,))
        
        if results:
            return self._dict_to_article(results[0])
        return None
    
    def get_article_by_url(self, source_type: str, article_url: str) -> Optional[Article]:
        """根据URL获取文章"""
        sql = "SELECT * FROM articles WHERE source_type = %s AND article_url = %s"
        results = self.execute_query(sql, (source_type, article_url))
        
        if results:
            return self._dict_to_article(results[0])
        return None
    
    def get_pending_articles(self, source_type: Optional[str] = None, limit: int = 100) -> List[Article]:
        """获取待采集的文章列表"""
        sql = "SELECT * FROM articles WHERE crawl_status = %s"
        params = [CrawlStatus.PENDING.value]
        
        if source_type:
            sql += " AND source_type = %s"
            params.append(source_type)
        
        sql += " ORDER BY fetched_at ASC LIMIT %s"
        params.append(limit)
        
        results = self.execute_query(sql, tuple(params))
        return [self._dict_to_article(row) for row in results]
    
    def update_crawl_status(self, article_id: int, status: str, content: Optional[str] = None,
                           content_html: Optional[str] = None, word_count: int = 0,
                           images: Optional[List[Dict]] = None, error_message: Optional[str] = None):
        """更新文章采集状态"""
        sql = """
        UPDATE articles SET
            crawl_status = %s,
            crawl_attempts = crawl_attempts + 1,
            crawled_at = %s,
            content = %s,
            content_html = %s,
            word_count = %s,
            images = %s,
            crawl_error = %s,
            updated_at = NOW()
        WHERE id = %s
        """
        
        crawled_at = datetime.now() if status == CrawlStatus.COMPLETED.value else None
        
        params = (
            status, crawled_at, content, content_html, word_count,
            json.dumps(images) if images else None,
            error_message, article_id
        )
        
        return self.execute_update(sql, params)
    
    def get_articles_for_publish(self, platform: Optional[str] = None, limit: int = 100) -> List[Article]:
        """获取待发布的文章"""
        sql = """
        SELECT * FROM articles 
        WHERE crawl_status = %s 
        AND (publish_status IS NULL OR JSON_EXTRACT(publish_status, '$."{}") IS NULL OR JSON_EXTRACT(publish_status, '$."{}") = 'pending')
        ORDER BY crawled_at ASC 
        LIMIT %s
        """.format(platform or "all", platform or "all")
        
        results = self.execute_query(sql, (CrawlStatus.COMPLETED.value, limit))
        return [self._dict_to_article(row) for row in results]
    
    def update_publish_status(self, article_id: int, platform: str, status: str):
        """更新发布状态"""
        # 先获取当前的发布状态
        article = self.get_article_by_id(article_id)
        if not article:
            return False
        
        publish_status = article.publish_status or {}
        publish_status[platform] = status
        
        sql = "UPDATE articles SET publish_status = %s, updated_at = NOW() WHERE id = %s"
        return self.execute_update(sql, (json.dumps(publish_status), article_id))
    
    # ========== 发布任务管理方法 ==========
    
    def create_publish_task(self, task: PublishTask) -> int:
        """创建发布任务"""
        sql = """
        INSERT INTO publish_tasks (
            article_id, target_platform, target_forum_id, target_category,
            status, priority, max_attempts, custom_title, custom_content,
            publish_config, scheduled_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        params = (
            task.article_id, task.target_platform, task.target_forum_id,
            task.target_category, task.status, task.priority, task.max_attempts,
            task.custom_title, task.custom_content,
            json.dumps(task.publish_config) if task.publish_config else None,
            task.scheduled_at
        )
        
        return self.execute_insert(sql, params)
    
    def get_pending_publish_tasks(self, platform: Optional[str] = None, limit: int = 50) -> List[PublishTask]:
        """获取待处理的发布任务"""
        sql = """
        SELECT * FROM publish_tasks 
        WHERE status = %s 
        AND attempts < max_attempts
        AND (scheduled_at IS NULL OR scheduled_at <= NOW())
        """
        params = [PublishStatus.PENDING.value]
        
        if platform:
            sql += " AND target_platform = %s"
            params.append(platform)
        
        sql += " ORDER BY priority ASC, created_at ASC LIMIT %s"
        params.append(limit)
        
        results = self.execute_query(sql, tuple(params))
        return [self._dict_to_publish_task(row) for row in results]
    
    def update_publish_task_status(self, task_id: int, status: str, 
                                 published_url: Optional[str] = None,
                                 published_id: Optional[str] = None,
                                 error_message: Optional[str] = None,
                                 response_data: Optional[Dict] = None):
        """更新发布任务状态"""
        sql = """
        UPDATE publish_tasks SET
            status = %s,
            attempts = attempts + 1,
            published_url = %s,
            published_id = %s,
            error_message = %s,
            response_data = %s,
            started_at = CASE WHEN status = 'processing' THEN NOW() ELSE started_at END,
            completed_at = CASE WHEN status IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE completed_at END,
            updated_at = NOW()
        WHERE id = %s
        """
        
        params = (
            status, published_url, published_id, error_message,
            json.dumps(response_data) if response_data else None,
            task_id
        )
        
        return self.execute_update(sql, params)
    
    # ========== 统计和监控方法 ==========
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        sql = """
        SELECT 
            source_type,
            COUNT(*) as total_articles,
            SUM(CASE WHEN crawl_status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN crawl_status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) as failed,
            AVG(word_count) as avg_word_count,
            MAX(crawled_at) as last_crawl_time
        FROM articles 
        GROUP BY source_type
        """
        
        results = self.execute_query(sql)
        return {row['source_type']: row for row in results}
    
    def get_publish_statistics(self) -> Dict[str, Any]:
        """获取发布统计信息"""
        sql = """
        SELECT 
            target_platform,
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            AVG(attempts) as avg_attempts
        FROM publish_tasks 
        GROUP BY target_platform
        """
        
        results = self.execute_query(sql)
        return {row['target_platform']: row for row in results}
    
    # ========== 辅助方法 ==========
    
    def _dict_to_article(self, data: Dict) -> Article:
        """将字典转换为Article对象"""
        # 处理JSON字段
        if data.get('images'):
            data['images'] = json.loads(data['images']) if isinstance(data['images'], str) else data['images']
        if data.get('links'):
            data['links'] = json.loads(data['links']) if isinstance(data['links'], str) else data['links']
        if data.get('tags'):
            data['tags'] = json.loads(data['tags']) if isinstance(data['tags'], str) else data['tags']
        if data.get('publish_status'):
            data['publish_status'] = json.loads(data['publish_status']) if isinstance(data['publish_status'], str) else data['publish_status']
        
        return Article(**data)
    
    def _dict_to_publish_task(self, data: Dict) -> PublishTask:
        """将字典转换为PublishTask对象"""
        # 处理JSON字段
        if data.get('response_data'):
            data['response_data'] = json.loads(data['response_data']) if isinstance(data['response_data'], str) else data['response_data']
        if data.get('publish_config'):
            data['publish_config'] = json.loads(data['publish_config']) if isinstance(data['publish_config'], str) else data['publish_config']
        
        return PublishTask(**data)
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()

# ========== 兼容性方法 ==========

def migrate_from_wechat_articles(db_manager: UnifiedDatabaseManager) -> int:
    """
    从wechat_articles表迁移数据到新表结构

    Args:
        db_manager: 数据库管理器实例

    Returns:
        int: 迁移的记录数
    """
    try:
        # 检查原表是否存在
        check_sql = "SHOW TABLES LIKE 'wechat_articles'"
        results = db_manager.execute_query(check_sql)

        if not results:
            logger.info("原表wechat_articles不存在，跳过迁移")
            return 0

        # 获取原表数据
        select_sql = """
        SELECT
            account_name, title, article_url, publish_timestamp,
            crawl_status, content, word_count, images, error_message,
            crawled_at, fetched_at
        FROM wechat_articles
        WHERE article_url IS NOT NULL AND article_url != ''
        AND title IS NOT NULL AND title != ''
        """

        old_articles = db_manager.execute_query(select_sql)
        migrated_count = 0

        for old_article in old_articles:
            # 检查是否已存在
            existing = db_manager.get_article_by_url('wechat', old_article['article_url'])
            if existing:
                continue

            # 转换状态
            crawl_status = CrawlStatus.PENDING.value
            if old_article.get('crawl_status') == 1:
                crawl_status = CrawlStatus.COMPLETED.value
            elif old_article.get('crawl_status') == 2:
                crawl_status = CrawlStatus.FAILED.value

            # 创建新文章对象
            article = Article(
                source_type=SourceType.WECHAT.value,
                source_name=old_article['account_name'],
                title=old_article['title'],
                article_url=old_article['article_url'],
                publish_timestamp=old_article.get('publish_timestamp'),
                crawl_status=crawl_status,
                content=old_article.get('content'),
                content_html=old_article.get('content'),
                word_count=old_article.get('word_count', 0),
                images=json.loads(old_article['images']) if old_article.get('images') else None,
                crawl_error=old_article.get('error_message'),
                crawled_at=old_article.get('crawled_at'),
                fetched_at=old_article.get('fetched_at')
            )

            # 插入新表
            db_manager.insert_article(article)
            migrated_count += 1

        logger.info(f"成功迁移{migrated_count}条记录")
        return migrated_count

    except Exception as e:
        logger.error(f"数据迁移失败: {e}")
        return 0

# 全局数据库管理器实例
_global_db_manager = None

def get_db_manager() -> UnifiedDatabaseManager:
    """获取全局数据库管理器实例"""
    global _global_db_manager
    if _global_db_manager is None:
        _global_db_manager = UnifiedDatabaseManager()
    return _global_db_manager
