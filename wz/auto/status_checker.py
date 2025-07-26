#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态检测器
负责检测各个步骤的执行条件和待处理数据状态
"""

import mysql.connector
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class StatusChecker:
    """状态检测器"""
    
    def __init__(self):
        """初始化状态检测器"""
        # WZ数据库配置
        self.wz_config = {
            'host': '140.238.201.162',
            'port': 3306,
            'user': 'cj',
            'password': '760516',
            'database': 'cj',
            'charset': 'utf8mb4'
        }
        
        # Discuz数据库配置
        self.discuz_config = {
            'host': '140.238.201.162',
            'port': 3306,
            'user': '00077',
            'password': '760516',
            'database': '00077',
            'charset': 'utf8mb4'
        }
    
    def check_link_crawl_status(self, config: Dict) -> Dict:
        """
        检查链接采集状态
        
        Args:
            config: 链接采集配置
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'should_execute': False,
            'reason': '',
            'details': {},
            'estimated_new_articles': 0
        }
        
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor(dictionary=True)
            
            # 检查配置的公众号
            accounts = config.get('accounts', ['all'])
            if 'all' in accounts:
                # 获取所有配置的公众号
                # 这里需要根据实际的公众号配置来获取
                accounts = ['舞林攻略指南', '人类砂舞行为研究', '砂砂之家']
            
            total_estimated = 0
            account_details = {}
            
            for account in accounts:
                # 检查该公众号最近的采集情况
                cursor.execute("""
                    SELECT COUNT(*) as count, MAX(fetched_at) as last_fetch
                    FROM wechat_articles 
                    WHERE account_name = %s AND fetched_at >= %s
                """, (account, datetime.now() - timedelta(hours=24)))
                
                account_info = cursor.fetchone()
                recent_count = account_info['count'] if account_info else 0
                last_fetch = account_info['last_fetch'] if account_info else None
                
                # 估算可能的新文章数量
                limit_per_account = config.get('limit_per_account', 10)
                estimated_new = min(limit_per_account, max(0, limit_per_account - recent_count))
                
                account_details[account] = {
                    'recent_articles': recent_count,
                    'last_fetch': last_fetch.isoformat() if last_fetch else None,
                    'estimated_new': estimated_new
                }
                
                total_estimated += estimated_new
            
            # 检查总数限制
            total_limit = config.get('total_limit', 50)
            if total_estimated > total_limit:
                total_estimated = total_limit
            
            # 决定是否执行
            if total_estimated > 0:
                result['should_execute'] = True
                result['reason'] = f'预计可采集{total_estimated}篇新文章'
            else:
                result['should_execute'] = False
                result['reason'] = '最近24小时内已采集足够文章，暂不需要采集'
            
            result['estimated_new_articles'] = total_estimated
            result['details'] = {
                'accounts': account_details,
                'total_limit': total_limit
            }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"检查链接采集状态失败: {e}")
            result['should_execute'] = True  # 出错时默认执行
            result['reason'] = f'状态检查失败，默认执行: {str(e)}'
        
        return result
    
    def check_content_crawl_status(self, config: Dict) -> Dict:
        """
        检查内容采集状态
        
        Args:
            config: 内容采集配置
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'should_execute': False,
            'reason': '',
            'details': {},
            'pending_articles': 0
        }
        
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor(dictionary=True)
            
            # 查询待采集内容的文章
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM wechat_articles 
                WHERE (content IS NULL OR content = '') 
                AND article_url IS NOT NULL
            """)
            
            pending_count = cursor.fetchone()['count']
            limit = config.get('limit', 50)
            
            # 实际需要处理的数量
            actual_pending = min(pending_count, limit)
            
            if actual_pending > 0:
                result['should_execute'] = True
                result['reason'] = f'发现{pending_count}篇待采集内容的文章，将处理{actual_pending}篇'
            else:
                result['should_execute'] = False
                result['reason'] = '没有待采集内容的文章'
            
            result['pending_articles'] = actual_pending
            result['details'] = {
                'total_pending': pending_count,
                'limit': limit,
                'batch_size': config.get('batch_size', 5)
            }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"检查内容采集状态失败: {e}")
            result['should_execute'] = False
            result['reason'] = f'状态检查失败: {str(e)}'
        
        return result
    
    def check_forum_publish_status(self, config: Dict) -> Dict:
        """
        检查论坛发布状态
        
        Args:
            config: 论坛发布配置
            
        Returns:
            Dict: 检测结果
        """
        result = {
            'should_execute': False,
            'reason': '',
            'details': {},
            'pending_articles': 0
        }
        
        try:
            conn = mysql.connector.connect(**self.wz_config)
            cursor = conn.cursor(dictionary=True)
            
            # 查询待发布的文章
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM wechat_articles 
                WHERE forum_published IS NULL 
                AND content IS NOT NULL 
                AND content != ''
            """)
            
            pending_count = cursor.fetchone()['count']
            limit = config.get('limit', 100)
            
            # 实际需要发布的数量
            actual_pending = min(pending_count, limit)
            
            if actual_pending > 0:
                result['should_execute'] = True
                result['reason'] = f'发现{pending_count}篇待发布文章，将发布{actual_pending}篇'
            else:
                result['should_execute'] = False
                result['reason'] = '没有待发布的文章'
            
            result['pending_articles'] = actual_pending
            result['details'] = {
                'total_pending': pending_count,
                'limit': limit,
                'interval_min': config.get('interval_min', 60),
                'interval_max': config.get('interval_max', 120)
            }
            
            conn.close()
            
        except Exception as e:
            logger.error(f"检查论坛发布状态失败: {e}")
            result['should_execute'] = False
            result['reason'] = f'状态检查失败: {str(e)}'
        
        return result
    
    def get_overall_status(self, config: Dict) -> Dict:
        """
        获取整体状态概览
        
        Args:
            config: 完整配置
            
        Returns:
            Dict: 整体状态
        """
        overall_status = {
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'summary': {
                'total_steps': 0,
                'enabled_steps': 0,
                'executable_steps': 0
            }
        }
        
        steps_config = config.get('steps', {})
        
        for step_name, step_config in steps_config.items():
            if not step_config.get('enabled', True):
                overall_status['steps'][step_name] = {
                    'enabled': False,
                    'should_execute': False,
                    'reason': '步骤已禁用'
                }
                continue
            
            # 检查各步骤状态
            if step_name == 'link_crawl':
                status = self.check_link_crawl_status(step_config.get('params', {}))
            elif step_name == 'content_crawl':
                status = self.check_content_crawl_status(step_config.get('params', {}))
            elif step_name == 'forum_publish':
                status = self.check_forum_publish_status(step_config.get('params', {}))
            else:
                status = {
                    'should_execute': False,
                    'reason': f'未知步骤: {step_name}'
                }
            
            status['enabled'] = True
            overall_status['steps'][step_name] = status
            
            # 更新统计
            overall_status['summary']['total_steps'] += 1
            overall_status['summary']['enabled_steps'] += 1
            if status['should_execute']:
                overall_status['summary']['executable_steps'] += 1
        
        return overall_status
