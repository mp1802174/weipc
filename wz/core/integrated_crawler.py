#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目集成采集器
整合CFCJ采集功能与统一数据库管理
"""

import logging
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database import UnifiedDatabaseManager, Article, CrawlStatus, SourceType
from core.config import get_config
from cfcj.api import CFCJAPI, crawl_single_article
from cfcj.utils.exceptions import CFCJError

logger = logging.getLogger(__name__)

class IntegratedCrawler:
    """集成采集器 - 连接CFCJ与统一数据库"""
    
    def __init__(self, config=None):
        """
        初始化集成采集器
        
        Args:
            config: 配置对象，如果为None则使用全局配置
        """
        self.config = config or get_config()
        self.db_manager = UnifiedDatabaseManager(self.config)
        self.cfcj_api = None
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def initialize(self) -> bool:
        """
        初始化采集器
        
        Returns:
            bool: 是否初始化成功
        """
        try:
            # 连接数据库
            if not self.db_manager.connect():
                logger.error("数据库连接失败")
                return False
            
            # 初始化CFCJ API
            self.cfcj_api = CFCJAPI()
            
            logger.info("集成采集器初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"集成采集器初始化失败: {e}")
            return False
    
    def get_pending_articles(self, source_type: Optional[str] = None, limit: int = 100) -> List[Article]:
        """
        获取待采集的文章列表 - 从wechat_articles表读取

        Args:
            source_type: 源类型过滤 (暂时忽略，因为wechat_articles主要是微信内容)
            limit: 限制数量

        Returns:
            List[Article]: 待采集文章列表
        """
        try:
            # 直接从wechat_articles表获取待采集文章
            articles = self._get_pending_from_wechat_articles(limit)
            logger.info(f"获取到{len(articles)}篇待采集文章")
            return articles

        except Exception as e:
            logger.error(f"获取待采集文章失败: {e}")
            return []

    def _get_pending_from_wechat_articles(self, limit: int = 100) -> List[Article]:
        """从wechat_articles表获取待采集文章"""
        import mysql.connector
        from datetime import datetime

        # 数据库配置
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
            from config_manager import get_database_config
            db_config = get_database_config('wz_database')
        except Exception as e:
            logger.warning(f"无法加载数据库配置，使用默认配置: {e}")
            db_config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'wz',
                'charset': 'utf8mb4'
            }

        articles = []

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)

            # 查询待采集的文章 (crawl_status = 0 或 NULL 表示未采集)
            sql = """
            SELECT id, account_name, title, article_url, publish_timestamp,
                   source_type, content, crawl_status, error_message,
                   word_count, images, crawled_at, fetched_at
            FROM wechat_articles
            WHERE (crawl_status = 0 OR crawl_status IS NULL OR content IS NULL OR content = '')
            ORDER BY publish_timestamp DESC
            LIMIT %s
            """

            cursor.execute(sql, (limit,))
            results = cursor.fetchall()

            # 转换为Article对象
            for row in results:
                article = Article(
                    id=row['id'],
                    source_type='wechat',
                    source_name=row['account_name'],
                    title=row['title'],
                    article_url=row['article_url'],
                    publish_timestamp=row['publish_timestamp'],
                    crawl_status='pending' if (row['crawl_status'] == 0 or row['crawl_status'] is None) else 'completed',
                    content=row['content'],
                    word_count=row['word_count'] or 0,
                    crawled_at=row['crawled_at'],
                    fetched_at=row['fetched_at']
                )
                articles.append(article)

        except Exception as e:
            logger.error(f"从wechat_articles表获取文章失败: {e}")

        finally:
            if 'conn' in locals():
                conn.close()

        return articles
    
    def crawl_single_article(self, article: Article) -> bool:
        """
        采集单篇文章
        
        Args:
            article: 文章对象
            
        Returns:
            bool: 是否采集成功
        """
        try:
            # 更新状态为采集中 - 直接操作wechat_articles表
            self._update_wechat_article_status(article.id, 'crawling')

            logger.info(f"开始采集文章: {article.title} ({article.article_url})")

            # 使用CFCJ采集内容
            result = crawl_single_article(article.article_url)

            if result and result.get('title'):
                # 采集成功，更新数据库
                content = result.get('content', '')
                word_count = len(content) if content else 0
                title = result.get('title', '')

                self._update_wechat_article_content(
                    article.id,
                    content=content,
                    word_count=word_count,
                    images=result.get('images', []),
                    status='completed',
                    title=title  # 传递采集到的真实标题
                )

                self.stats['successful'] += 1
                logger.info(f"文章采集成功: {article.title}")
                return True

            else:
                # 采集失败
                error_msg = result.get('error', '采集返回空结果或无标题') if result else '采集返回空结果'
                self._update_wechat_article_status(article.id, 'failed', error_msg)

                self.stats['failed'] += 1
                logger.error(f"文章采集失败: {article.title} - {error_msg}")
                return False

        except Exception as e:
            # 异常处理
            error_msg = f"采集过程异常: {str(e)}"

            try:
                self._update_wechat_article_status(article.id, 'failed', error_msg)
            except:
                pass

            self.stats['failed'] += 1
            logger.error(f"采集文章异常: {article.title} - {error_msg}")
            return False
        
        finally:
            self.stats['total_processed'] += 1

    def _update_wechat_article_status(self, article_id: int, status: str, error_msg: str = None):
        """更新wechat_articles表的采集状态"""
        import mysql.connector
        from datetime import datetime

        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
            from config_manager import get_database_config
            db_config = get_database_config('wz_database')
        except Exception as e:
            logger.warning(f"无法加载数据库配置，使用默认配置: {e}")
            db_config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'wz',
                'charset': 'utf8mb4'
            }

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # 状态映射：crawling=1, completed=1, failed=2
            status_value = 1 if status in ['crawling', 'completed'] else 2

            if error_msg:
                sql = "UPDATE wechat_articles SET crawl_status = %s, error_message = %s WHERE id = %s"
                cursor.execute(sql, (status_value, error_msg, article_id))
            else:
                sql = "UPDATE wechat_articles SET crawl_status = %s WHERE id = %s"
                cursor.execute(sql, (status_value, article_id))

            conn.commit()

        except Exception as e:
            logger.error(f"更新wechat_articles状态失败: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def _update_wechat_article_content(self, article_id: int, content: str, word_count: int, images: list, status: str, title: str = None):
        """更新wechat_articles表的内容信息"""
        import mysql.connector
        import json
        from datetime import datetime

        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
            from config_manager import get_database_config
            db_config = get_database_config('wz_database')
        except Exception as e:
            logger.warning(f"无法加载数据库配置，使用默认配置: {e}")
            db_config = {
                'host': 'localhost',
                'port': 3306,
                'user': 'root',
                'password': '',
                'database': 'wz',
                'charset': 'utf8mb4'
            }

        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            # 状态映射
            status_value = 1 if status == 'completed' else 2

            # 如果提供了标题，同时更新标题
            if title:
                sql = """
                UPDATE wechat_articles
                SET title = %s, content = %s, word_count = %s, images = %s, crawl_status = %s, crawled_at = %s
                WHERE id = %s
                """
                images_json = json.dumps(images) if images else None
                cursor.execute(sql, (title, content, word_count, images_json, status_value, datetime.now(), article_id))
            else:
                sql = """
                UPDATE wechat_articles
                SET content = %s, word_count = %s, images = %s, crawl_status = %s, crawled_at = %s
                WHERE id = %s
                """
                images_json = json.dumps(images) if images else None
                cursor.execute(sql, (content, word_count, images_json, status_value, datetime.now(), article_id))

            conn.commit()

        except Exception as e:
            logger.error(f"更新wechat_articles内容失败: {e}")
        finally:
            if 'conn' in locals():
                conn.close()
    
    def batch_crawl(self, source_type: Optional[str] = None, limit: int = 100, 
                   batch_size: int = 5) -> Dict[str, Any]:
        """
        批量采集文章
        
        Args:
            source_type: 源类型过滤
            limit: 总限制数量
            batch_size: 批次大小
            
        Returns:
            Dict[str, Any]: 采集结果统计
        """
        logger.info(f"开始批量采集 - 源类型: {source_type}, 限制: {limit}, 批次大小: {batch_size}")
        
        # 重置统计
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': datetime.now()
        }
        
        try:
            # 获取待采集文章
            pending_articles = self.get_pending_articles(source_type, limit)
            
            if not pending_articles:
                logger.info("没有待采集的文章")
                return self.stats
            
            # 分批处理
            for i in range(0, len(pending_articles), batch_size):
                batch = pending_articles[i:i + batch_size]
                logger.info(f"处理批次 {i//batch_size + 1}/{(len(pending_articles)-1)//batch_size + 1}")
                
                for article in batch:
                    self.crawl_single_article(article)
                    
                    # 批次间延迟
                    if self.config.cfcj.request_delay > 0:
                        import time
                        time.sleep(self.config.cfcj.request_delay)
            
            self.stats['end_time'] = datetime.now()
            self.stats['duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            logger.info(f"批量采集完成 - 总计: {self.stats['total_processed']}, "
                       f"成功: {self.stats['successful']}, 失败: {self.stats['failed']}")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"批量采集异常: {e}")
            self.stats['error'] = str(e)
            return self.stats
    
    def crawl_by_urls(self, urls: List[str], source_type: str = "external", 
                     source_name: str = "手动导入") -> Dict[str, Any]:
        """
        根据URL列表采集文章
        
        Args:
            urls: URL列表
            source_type: 源类型
            source_name: 源名称
            
        Returns:
            Dict[str, Any]: 采集结果
        """
        logger.info(f"开始根据URL列表采集 - 数量: {len(urls)}")
        
        results = []
        
        for url in urls:
            try:
                # 检查是否已存在
                existing_article = self.db_manager.get_article_by_url(source_type, url)
                if existing_article:
                    logger.info(f"文章已存在，跳过: {url}")
                    results.append({
                        'url': url,
                        'status': 'skipped',
                        'reason': '文章已存在'
                    })
                    continue
                
                # 创建新文章记录
                article = Article(
                    source_type=source_type,
                    source_name=source_name,
                    title=f"待采集文章 - {url}",
                    article_url=url,
                    crawl_status=CrawlStatus.PENDING.value
                )
                
                article_id = self.db_manager.insert_article(article)
                article.id = article_id
                
                # 立即采集
                success = self.crawl_single_article(article)
                
                results.append({
                    'url': url,
                    'status': 'success' if success else 'failed',
                    'article_id': article_id
                })
                
            except Exception as e:
                logger.error(f"处理URL失败: {url} - {e}")
                results.append({
                    'url': url,
                    'status': 'error',
                    'error': str(e)
                })
        
        return {
            'total': len(urls),
            'results': results,
            'summary': {
                'success': len([r for r in results if r['status'] == 'success']),
                'failed': len([r for r in results if r['status'] == 'failed']),
                'skipped': len([r for r in results if r['status'] == 'skipped']),
                'error': len([r for r in results if r['status'] == 'error'])
            }
        }
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """获取采集统计信息"""
        try:
            db_stats = self.db_manager.get_crawl_statistics()
            
            # 添加当前会话统计
            return {
                'database_stats': db_stats,
                'session_stats': self.stats,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.cfcj_api:
                # CFCJ API的清理
                pass
            
            if self.db_manager:
                self.db_manager.disconnect()
            
            logger.info("集成采集器资源清理完成")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        if self.initialize():
            return self
        else:
            raise Exception("集成采集器初始化失败")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup()

# 便捷函数
def create_integrated_crawler(config=None) -> IntegratedCrawler:
    """创建集成采集器实例"""
    return IntegratedCrawler(config)

def batch_crawl_from_database(source_type: Optional[str] = None, limit: int = 100, 
                             batch_size: int = 5) -> Dict[str, Any]:
    """
    从数据库批量采集文章的便捷函数
    
    Args:
        source_type: 源类型过滤
        limit: 限制数量
        batch_size: 批次大小
        
    Returns:
        Dict[str, Any]: 采集结果
    """
    with create_integrated_crawler() as crawler:
        return crawler.batch_crawl(source_type, limit, batch_size)

def crawl_urls(urls: List[str], source_type: str = "external", 
               source_name: str = "手动导入") -> Dict[str, Any]:
    """
    根据URL列表采集的便捷函数
    
    Args:
        urls: URL列表
        source_type: 源类型
        source_name: 源名称
        
    Returns:
        Dict[str, Any]: 采集结果
    """
    with create_integrated_crawler() as crawler:
        return crawler.crawl_by_urls(urls, source_type, source_name)
