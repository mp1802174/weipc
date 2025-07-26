#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛发布器
负责将微信文章发布到Discuz论坛
"""

import mysql.connector
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

# 添加config目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from config_manager import get_database_config, get_forum_config

try:
    from .discuz_client import DiscuzClient
except ImportError:
    from discuz_client import DiscuzClient

logger = logging.getLogger(__name__)

class ForumPublisher:
    """论坛发布器"""
    
    def __init__(self):
        """初始化发布器"""
        try:
            self.wz_config = get_database_config('wz_database')
            forum_config = get_forum_config()

            # 发布配置
            self.publish_config = {
                'fid': forum_config.get('target_forum_id', 2),
                'author': forum_config.get('publisher_username', '砂鱼'),
                'authorid': forum_config.get('publisher_user_id', 4)
            }
        except Exception as e:
            logger.warning(f"无法加载配置文件，使用默认配置: {e}")
            # 使用默认配置作为备用
            self.wz_config = {
                'host': '140.238.201.162',
                'port': 3306,
                'user': 'cj',
                'password': '760516',
                'database': 'cj',
                'charset': 'utf8mb4'
            }

            # 发布配置
            self.publish_config = {
                'fid': 2,           # 目标版块ID
                'author': '砂鱼',    # 发布用户名
                'authorid': 4       # 发布用户ID
            }
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict]:
        """从WZ数据库获取文章信息"""
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor(dictionary=True)
            
            sql = """
            SELECT id, title, content, article_url, account_name, publish_timestamp
            FROM wechat_articles 
            WHERE id = %s AND forum_published IS NULL
            """
            
            cursor.execute(sql, (article_id,))
            article = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return article
            
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return None
    
    def mark_as_published(self, article_id: int) -> bool:
        """标记文章为已发布"""
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE wechat_articles SET forum_published = 1 WHERE id = %s",
                (article_id,)
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"文章ID={article_id}已标记为已发布")
            return True
            
        except Exception as e:
            logger.error(f"标记文章发布状态失败: {e}")
            return False
    
    def prepare_content(self, article: Dict) -> str:
        """准备发布内容"""
        content = article.get('content', '')

        # 如果没有内容，使用标题
        if not content or content.strip() == '':
            content = f"文章标题：{article['title']}"

        # 直接返回内容，不添加来源信息
        return content
    
    def publish_single_article(self, article_id: int) -> Dict:
        """
        发布单篇文章
        
        Args:
            article_id: 文章ID
            
        Returns:
            Dict: 发布结果
        """
        result = {
            'success': False,
            'article_id': article_id,
            'message': '',
            'tid': None,
            'pid': None
        }
        
        try:
            # 1. 获取文章信息
            article = self.get_article_by_id(article_id)
            if not article:
                result['message'] = '文章不存在或已发布'
                return result
            
            # 2. 准备发布数据
            publish_data = {
                'fid': self.publish_config['fid'],
                'author': self.publish_config['author'],
                'authorid': self.publish_config['authorid'],
                'title': article['title'],
                'content': self.prepare_content(article)
            }
            
            # 3. 发布到论坛
            with DiscuzClient() as discuz:
                if discuz.publish_article(publish_data):
                    # 4. 标记为已发布
                    if self.mark_as_published(article_id):
                        result['success'] = True
                        result['message'] = '发布成功'
                        logger.info(f"文章发布成功: ID={article_id}, 标题={article['title']}")
                    else:
                        result['message'] = '发布成功但标记状态失败'
                else:
                    result['message'] = '发布到论坛失败'
            
        except Exception as e:
            result['message'] = f'发布过程中出错: {str(e)}'
            logger.error(f"发布文章失败: {e}")
        
        return result
    
    def get_pending_articles(self, limit: int = 100) -> list:
        """获取待发布的文章列表"""
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor(dictionary=True)
            
            sql = """
            SELECT id, title, account_name, publish_timestamp
            FROM wechat_articles 
            WHERE forum_published IS NULL
            ORDER BY publish_timestamp DESC
            LIMIT %s
            """
            
            cursor.execute(sql, (limit,))
            articles = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return articles
            
        except Exception as e:
            logger.error(f"获取待发布文章列表失败: {e}")
            return []
