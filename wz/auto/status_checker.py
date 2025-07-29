#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
状态检测器
负责检测各个步骤的执行条件和待处理数据状态
"""

import mysql.connector
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加config目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from config_manager import get_database_config, get_forum_config

logger = logging.getLogger(__name__)

class StatusChecker:
    """状态检测器"""
    
    def __init__(self):
        """初始化状态检测器"""
        try:
            # 从配置文件加载数据库配置
            self.wz_config = get_database_config('wz_database')
            self.discuz_config = get_database_config('discuz_database')
            self.forum_config = get_forum_config('discuz_forum')
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

            # Discuz数据库配置
            self.discuz_config = {
                'host': '140.238.201.162',
                'port': 3306,
                'user': '00077',
                'password': '760516',
                'database': '00077',
                'charset': 'utf8mb4'
            }

            self.forum_config = {
                'target_forum_id': 2,
                'publisher_user_id': 4,
                'publisher_username': '砂鱼'
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
                # 检查该公众号的采集情况
                cursor.execute("""
                    SELECT MAX(fetched_at) as last_fetch_time,
                           COUNT(*) as total_articles
                    FROM wechat_articles
                    WHERE account_name = %s
                """, (account,))

                account_info = cursor.fetchone()
                last_fetch_time = account_info['last_fetch_time'] if account_info else None
                total_articles = account_info['total_articles'] if account_info else 0

                # 简化判断逻辑：每天执行一次，就尝试采集
                limit_per_account = config.get('limit_per_account', 3)
                current_time = datetime.now()

                # 判断是否需要采集
                should_crawl = False
                reason = ""

                if total_articles == 0:
                    # 从未采集过该公众号
                    should_crawl = True
                    reason = "首次采集该公众号"
                elif last_fetch_time is None:
                    # 没有采集时间记录
                    should_crawl = True
                    reason = "无采集记录，需要采集"
                else:
                    # 检查距离上次采集的时间
                    time_since_last_fetch = current_time - last_fetch_time
                    hours_since_last = time_since_last_fetch.total_seconds() / 3600

                    if hours_since_last >= 12:  # 超过12小时就尝试采集
                        should_crawl = True
                        reason = f"距离上次采集已过{hours_since_last:.1f}小时，尝试获取新文章"
                    else:
                        should_crawl = False
                        reason = f"距离上次采集仅{hours_since_last:.1f}小时，暂不采集"

                estimated_new = limit_per_account if should_crawl else 0

                account_details[account] = {
                    'total_articles': total_articles,
                    'last_fetch_time': last_fetch_time.isoformat() if last_fetch_time else None,
                    'estimated_new': estimated_new,
                    'reason': reason
                }

                total_estimated += estimated_new
            
            # 检查总数限制
            total_limit = config.get('total_limit', 50)
            if total_estimated > total_limit:
                total_estimated = total_limit
            
            # 决定是否执行
            if total_estimated > 0:
                result['should_execute'] = True
                result['reason'] = f'有{len([a for a in account_details.values() if a["estimated_new"] > 0])}个公众号需要检查新文章，预计最多采集{total_estimated}篇'
            else:
                result['should_execute'] = False
                result['reason'] = '所有公众号都是最近12小时内采集过的，暂不需要重复采集'
            
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
            
            # 查询待采集内容的文章（crawl_status = 0 表示未采集内容）
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM wechat_articles
                WHERE crawl_status = 0
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
