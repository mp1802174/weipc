"""
CFCJ数据库管理器
处理采集数据的数据库存储
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import sys
import os

# 添加wzzq模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wzzq'))

try:
    from db import DatabaseManager as BaseDBManager
except ImportError:
    # 如果导入失败，提供一个基础实现
    class BaseDBManager:
        def __init__(self, **kwargs):
            raise ImportError("无法导入数据库管理器，请检查wzzq/db.py文件")


class CFCJDatabaseManager(BaseDBManager):
    """CFCJ专用数据库管理器"""
    
    def __init__(self, **kwargs):
        """
        初始化数据库管理器
        
        Args:
            **kwargs: 数据库连接参数
        """
        super().__init__(**kwargs)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('cfcj.database')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def ensure_extended_table_structure(self):
        """确保表结构包含扩展字段"""
        try:
            if not self.conn or not self.cursor:
                self.connect()
            
            # 检查扩展字段是否存在
            check_columns_sql = """
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'wechat_articles'
            """
            self.cursor.execute(check_columns_sql, (self.config['database'],))
            columns = [row['COLUMN_NAME'] if isinstance(row, dict) else row[0] for row in self.cursor.fetchall()]
            
            # 需要添加的字段
            required_fields = {
                'content': "LONGTEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '文章完整内容'",
                'ai_title': "VARCHAR(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI改写后的标题'",
                'ai_content': "LONGTEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'AI改写后的内容'",
                'images': "JSON DEFAULT NULL COMMENT '文章图片信息(JSON格式)'",
                'crawl_status': "TINYINT(1) DEFAULT 0 COMMENT '采集状态: 0-未采集, 1-已采集, 2-采集失败'",
                'error_message': "TEXT COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '采集错误信息'",
                'site_name': "VARCHAR(100) COLLATE utf8mb4_unicode_ci DEFAULT 'wechat' COMMENT '站点名称'",
                'word_count': "INT DEFAULT 0 COMMENT '文章字数'",
                'crawled_at': "TIMESTAMP NULL DEFAULT NULL COMMENT '内容采集完成时间'"
            }
            
            # 添加缺失的字段
            for field_name, field_definition in required_fields.items():
                if field_name not in columns:
                    alter_sql = f"ALTER TABLE wechat_articles ADD COLUMN {field_name} {field_definition}"
                    self.logger.info(f"添加字段: {field_name}")
                    self.cursor.execute(alter_sql)
            
            # 创建索引
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_crawl_status ON wechat_articles (crawl_status)",
                "CREATE INDEX IF NOT EXISTS idx_site_name ON wechat_articles (site_name)",
                "CREATE INDEX IF NOT EXISTS idx_crawled_at ON wechat_articles (crawled_at)"
            ]
            
            for index_sql in indexes:
                try:
                    self.cursor.execute(index_sql)
                except Exception as e:
                    # 索引可能已存在，忽略错误
                    pass
            
            self.logger.info("数据库表结构检查完成")
            
        except Exception as e:
            self.logger.error(f"检查表结构时出错: {e}")
    
    def save_article_content(self, article_data: Dict[str, Any]) -> bool:
        """
        保存采集到的文章内容
        
        Args:
            article_data: 文章数据字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.conn or not self.cursor:
                self.connect()
            
            # 确保表结构正确
            self.ensure_extended_table_structure()
            
            # 准备数据
            url = article_data.get('url', '')
            title = article_data.get('title', '')
            content = article_data.get('content', '')
            author = article_data.get('author', '')
            publish_time = article_data.get('publish_time', '')
            site_name = article_data.get('site_name', 'unknown')
            word_count = article_data.get('word_count', 0)

            # 图片已集成在content中，不再单独处理
            # images = article_data.get('images', [])
            # images_json = json.dumps(images, ensure_ascii=False) if images else None
            
            # 处理发布时间
            if publish_time:
                try:
                    if isinstance(publish_time, str):
                        # 尝试解析时间字符串
                        publish_timestamp = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                    else:
                        publish_timestamp = publish_time
                except:
                    publish_timestamp = datetime.now()
            else:
                publish_timestamp = datetime.now()
            
            # 检查文章是否已存在
            check_sql = "SELECT id, crawl_status FROM wechat_articles WHERE article_url = %s"
            self.cursor.execute(check_sql, (url,))
            existing = self.cursor.fetchone()
            
            if existing:
                # 文章已存在，更新内容
                article_id = existing['id'] if isinstance(existing, dict) else existing[0]
                crawl_status = existing['crawl_status'] if isinstance(existing, dict) else existing[1]
                
                # 如果已经采集过且有内容，可以选择跳过或更新
                if crawl_status == 1:
                    self.logger.info(f"文章已采集过，跳过: {url}")
                    return True
                
                update_sql = """
                UPDATE wechat_articles SET
                    title = %s,
                    content = %s,
                    site_name = %s,
                    word_count = %s,
                    crawl_status = 1,
                    crawled_at = CURRENT_TIMESTAMP,
                    error_message = NULL
                WHERE id = %s
                """

                self.cursor.execute(update_sql, (
                    title, content, site_name, word_count, article_id
                ))
                
                self.logger.info(f"更新文章内容: {title}")
                
            else:
                # 新文章，插入记录
                insert_sql = """
                INSERT INTO wechat_articles
                (account_name, title, article_url, publish_timestamp, content,
                 site_name, word_count, crawl_status, crawled_at, source_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1, CURRENT_TIMESTAMP, %s)
                """

                self.cursor.execute(insert_sql, (
                    author or site_name,  # account_name
                    title,
                    url,
                    publish_timestamp,
                    content,
                    site_name,
                    word_count,
                    'multi_site'  # source_type
                ))
                
                self.logger.info(f"插入新文章: {title}")
            
            if not self.config.get('autocommit', False):
                self.conn.commit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存文章内容失败: {e}")
            if not self.config.get('autocommit', False):
                self.conn.rollback()
            return False
    
    def mark_article_failed(self, url: str, error_message: str) -> bool:
        """
        标记文章采集失败
        
        Args:
            url: 文章URL
            error_message: 错误信息
            
        Returns:
            bool: 标记是否成功
        """
        try:
            if not self.conn or not self.cursor:
                self.connect()
            
            # 确保表结构正确
            self.ensure_extended_table_structure()
            
            # 检查文章是否存在
            check_sql = "SELECT id FROM wechat_articles WHERE article_url = %s"
            self.cursor.execute(check_sql, (url,))
            existing = self.cursor.fetchone()
            
            if existing:
                # 更新失败状态
                article_id = existing['id'] if isinstance(existing, dict) else existing[0]
                update_sql = """
                UPDATE wechat_articles SET 
                    crawl_status = 2,
                    error_message = %s,
                    crawled_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                self.cursor.execute(update_sql, (error_message, article_id))
            else:
                # 插入失败记录
                insert_sql = """
                INSERT INTO wechat_articles 
                (account_name, title, article_url, publish_timestamp, 
                 crawl_status, error_message, crawled_at, source_type) 
                VALUES (%s, %s, %s, %s, 2, %s, CURRENT_TIMESTAMP, %s)
                """
                self.cursor.execute(insert_sql, (
                    'unknown', 'Failed to crawl', url, datetime.now(),
                    error_message, 'multi_site'
                ))
            
            if not self.config.get('autocommit', False):
                self.conn.commit()
            
            self.logger.warning(f"标记文章采集失败: {url} - {error_message}")
            return True
            
        except Exception as e:
            self.logger.error(f"标记文章失败状态时出错: {e}")
            if not self.config.get('autocommit', False):
                self.conn.rollback()
            return False
    
    def get_uncrawled_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取未采集的文章列表
        
        Args:
            limit: 限制返回数量
            
        Returns:
            List[Dict]: 未采集的文章列表
        """
        try:
            if not self.conn or not self.cursor:
                self.connect()
            
            # 确保表结构正确
            self.ensure_extended_table_structure()
            
            sql = """
            SELECT id, account_name, title, article_url, publish_timestamp, site_name
            FROM wechat_articles 
            WHERE (crawl_status = 0 OR crawl_status IS NULL OR content IS NULL OR content = '')
            ORDER BY publish_timestamp DESC 
            LIMIT %s
            """
            
            self.cursor.execute(sql, (limit,))
            results = self.cursor.fetchall()
            
            # 转换为字典列表
            articles = []
            for row in results:
                if isinstance(row, dict):
                    articles.append(row)
                else:
                    # 如果是元组，转换为字典
                    articles.append({
                        'id': row[0],
                        'account_name': row[1],
                        'title': row[2],
                        'article_url': row[3],
                        'publish_timestamp': row[4],
                        'site_name': row[5]
                    })
            
            self.logger.info(f"找到 {len(articles)} 篇未采集的文章")
            return articles
            
        except Exception as e:
            self.logger.error(f"获取未采集文章列表失败: {e}")
            return []
