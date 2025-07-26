#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量发布器
负责批量发布微信文章到Discuz论坛
"""

import time
import random
import logging
from typing import Dict, List, Callable, Optional

try:
    from .forum_publisher import ForumPublisher
except ImportError:
    from forum_publisher import ForumPublisher

logger = logging.getLogger(__name__)

class BatchPublisher:
    """批量发布器"""
    
    def __init__(self):
        """初始化批量发布器"""
        self.publisher = ForumPublisher()
        self.min_interval = 60   # 最小间隔60秒
        self.max_interval = 120  # 最大间隔120秒
    
    def publish_all(self, progress_callback: Optional[Callable] = None) -> Dict:
        """
        批量发布所有待发布文章
        
        Args:
            progress_callback: 进度回调函数，接收(current, total, article_info, result)
            
        Returns:
            Dict: 发布结果统计
        """
        result = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': [],
            'start_time': time.time(),
            'end_time': None
        }
        
        try:
            # 1. 获取待发布文章列表
            pending_articles = self.publisher.get_pending_articles()
            result['total'] = len(pending_articles)
            
            if result['total'] == 0:
                result['message'] = '没有待发布的文章'
                result['end_time'] = time.time()
                return result
            
            logger.info(f"开始批量发布，共{result['total']}篇文章")
            
            # 2. 逐篇发布
            for i, article in enumerate(pending_articles, 1):
                article_info = {
                    'id': article['id'],
                    'title': article['title'],
                    'account_name': article['account_name']
                }
                
                # 发布单篇文章
                publish_result = self.publisher.publish_single_article(article['id'])
                
                # 更新统计
                if publish_result['success']:
                    result['success'] += 1
                else:
                    result['failed'] += 1
                
                # 记录详细结果
                detail = {
                    'article_id': article['id'],
                    'title': article['title'],
                    'success': publish_result['success'],
                    'message': publish_result['message'],
                    'timestamp': time.time()
                }
                result['details'].append(detail)
                
                # 调用进度回调
                if progress_callback:
                    try:
                        progress_callback(i, result['total'], article_info, publish_result)
                    except Exception as e:
                        logger.error(f"进度回调函数出错: {e}")
                
                # 如果不是最后一篇，等待随机间隔
                if i < result['total']:
                    interval = random.randint(self.min_interval, self.max_interval)
                    logger.info(f"等待{interval}秒后发布下一篇...")
                    time.sleep(interval)
            
            result['end_time'] = time.time()
            duration = result['end_time'] - result['start_time']
            
            logger.info(f"批量发布完成: 总计{result['total']}篇, 成功{result['success']}篇, 失败{result['failed']}篇, 耗时{duration:.1f}秒")
            
        except Exception as e:
            result['end_time'] = time.time()
            result['error'] = str(e)
            logger.error(f"批量发布过程中出错: {e}")
        
        return result
    
    def get_publish_status(self) -> Dict:
        """获取发布状态统计"""
        try:
            pending_articles = self.publisher.get_pending_articles()
            
            return {
                'pending_count': len(pending_articles),
                'pending_articles': [
                    {
                        'id': article['id'],
                        'title': article['title'],
                        'account_name': article['account_name']
                    }
                    for article in pending_articles[:10]  # 只返回前10篇
                ]
            }
            
        except Exception as e:
            logger.error(f"获取发布状态失败: {e}")
            return {
                'pending_count': 0,
                'pending_articles': [],
                'error': str(e)
            }
