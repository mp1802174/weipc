#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤执行器
负责执行各个工作流步骤
"""

import sys
import os
import time
import logging
import subprocess
import re
from typing import Dict, Any, Optional
from pathlib import Path

# 添加父目录到路径以便导入其他模块
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

class StepExecutor:
    """步骤执行器"""
    
    def __init__(self):
        """初始化步骤执行器"""
        self.current_step = None
        self.step_start_time = None
    
    def execute_link_crawl(self, params: Dict) -> Dict:
        """
        执行链接采集步骤
        
        Args:
            params: 采集参数
            
        Returns:
            Dict: 执行结果
        """
        result = {
            'success': False,
            'message': '',
            'details': {},
            'new_articles': 0
        }
        
        try:
            logger.info("开始执行链接采集...")
            
            # 使用与Web界面相同的方式调用微信采集脚本
            
            # 获取参数
            limit_per_account = params.get('limit_per_account', 10)

            # 构建命令行参数
            script_path = Path(__file__).parent.parent / 'crawl_wechat.py'
            cmd = [sys.executable, str(script_path), '--limit', str(limit_per_account)]

            logger.info(f"执行微信采集命令: {' '.join(cmd)}")

            try:
                # 执行采集脚本
                result_process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    timeout=300  # 5分钟超时
                )

                if result_process.returncode == 0:
                    # 解析输出获取采集数量
                    output = result_process.stdout
                    total_new = 0

                    # 从输出中提取采集数量
                    for line in output.split('\n'):
                        if '成功保存' in line and '篇文章到数据库' in line:
                            try:
                                # 提取数字
                                import re
                                match = re.search(r'成功保存 (\d+) 篇文章到数据库', line)
                                if match:
                                    total_new = int(match.group(1))
                                    break
                            except:
                                pass

                    logger.info(f"微信链接采集成功，共获取 {total_new} 篇新文章")

                    account_results = {
                        'total_new_articles': total_new,
                        'status': 'success',
                        'output': output
                    }

                else:
                    error_msg = result_process.stderr or result_process.stdout
                    logger.error(f"微信采集脚本执行失败: {error_msg}")
                    account_results = {
                        'total_new_articles': 0,
                        'status': 'failed',
                        'error': error_msg
                    }
                    total_new = 0

            except subprocess.TimeoutExpired:
                logger.error("微信采集脚本执行超时")
                account_results = {
                    'total_new_articles': 0,
                    'status': 'failed',
                    'error': '执行超时'
                }
                total_new = 0
            except Exception as e:
                logger.error(f"执行微信采集脚本失败: {e}")
                account_results = {
                    'total_new_articles': 0,
                    'status': 'failed',
                    'error': str(e)
                }
                total_new = 0
            
            result['success'] = True
            result['message'] = f'链接采集完成，共获取{total_new}篇新文章'
            result['new_articles'] = total_new
            result['details'] = {
                'accounts': account_results,
                'limit_per_account': limit_per_account
            }
            
        except Exception as e:
            logger.error(f"链接采集执行失败: {e}")
            result['message'] = f'链接采集执行失败: {str(e)}'
        
        return result
    
    def execute_content_crawl(self, params: Dict) -> Dict:
        """
        执行内容采集步骤
        
        Args:
            params: 采集参数
            
        Returns:
            Dict: 执行结果
        """
        result = {
            'success': False,
            'message': '',
            'details': {},
            'processed_articles': 0
        }
        
        try:
            logger.info("开始执行内容采集...")
            
            # 导入内容采集模块
            try:
                from core.integrated_crawler import IntegratedCrawler
            except ImportError as e:
                result['message'] = f'无法导入内容采集模块: {e}'
                return result
            
            # 获取参数
            limit = params.get('limit', 50)
            batch_size = params.get('batch_size', 5)
            source_types = params.get('source_types', ['wechat'])
            
            crawler = IntegratedCrawler()
            
            # 执行内容采集
            crawl_result = crawler.batch_crawl(
                source_type='wechat' if 'wechat' in source_types else None,
                limit=limit,
                batch_size=batch_size
            )
            
            # 判断采集是否成功（基于实际处理的文章数量）
            total_processed = crawl_result.get('total_processed', 0)
            successful = crawl_result.get('successful', 0)
            failed = crawl_result.get('failed', 0)

            if 'error' not in crawl_result:
                result['success'] = True
                result['message'] = f'内容采集完成，处理{total_processed}篇文章，成功{successful}篇，失败{failed}篇'
                result['processed_articles'] = total_processed
                result['details'] = {
                    'successful': successful,
                    'failed': failed,
                    'total_processed': total_processed,
                    'limit': limit,
                    'batch_size': batch_size
                }
            else:
                result['message'] = f'内容采集失败: {crawl_result.get("error", "未知错误")}'
            
        except Exception as e:
            logger.error(f"内容采集执行失败: {e}")
            result['message'] = f'内容采集执行失败: {str(e)}'
        
        return result
    
    def execute_forum_publish(self, params: Dict) -> Dict:
        """
        执行论坛发布步骤
        
        Args:
            params: 发布参数
            
        Returns:
            Dict: 执行结果
        """
        result = {
            'success': False,
            'message': '',
            'details': {},
            'published_articles': 0
        }
        
        try:
            logger.info("开始执行论坛发布...")
            
            # 导入论坛发布模块
            try:
                from fabu.batch_publisher import BatchPublisher
            except ImportError as e:
                result['message'] = f'无法导入论坛发布模块: {e}'
                return result
            
            # 获取参数
            limit = params.get('limit', 100)
            interval_min = params.get('interval_min', 60)
            interval_max = params.get('interval_max', 120)
            
            # 创建批量发布器
            publisher = BatchPublisher()
            
            # 设置发布间隔
            publisher.min_interval = interval_min
            publisher.max_interval = interval_max
            
            # 执行批量发布
            publish_result = publisher.publish_all()
            
            if publish_result.get('total', 0) > 0:
                success_count = publish_result.get('success', 0)
                failed_count = publish_result.get('failed', 0)
                
                result['success'] = True
                result['message'] = f'论坛发布完成，成功{success_count}篇，失败{failed_count}篇'
                result['published_articles'] = success_count
                result['details'] = {
                    'total': publish_result.get('total', 0),
                    'success': success_count,
                    'failed': failed_count,
                    'duration': publish_result.get('end_time', 0) - publish_result.get('start_time', 0)
                }
            else:
                result['success'] = True
                result['message'] = '没有待发布的文章'
                result['published_articles'] = 0
            
        except Exception as e:
            logger.error(f"论坛发布执行失败: {e}")
            result['message'] = f'论坛发布执行失败: {str(e)}'
        
        return result
    
    def execute_step(self, step_name: str, step_config: Dict, timeout: Optional[int] = None) -> Dict:
        """
        执行指定步骤
        
        Args:
            step_name: 步骤名称
            step_config: 步骤配置
            timeout: 超时时间（秒）
            
        Returns:
            Dict: 执行结果
        """
        self.current_step = step_name
        self.step_start_time = time.time()
        
        logger.info(f"开始执行步骤: {step_name}")
        
        try:
            # 获取步骤参数
            params = step_config.get('params', {})
            step_timeout = timeout or step_config.get('timeout', 3600)
            
            # 根据步骤名称执行相应的方法
            if step_name == 'link_crawl':
                result = self.execute_link_crawl(params)
            elif step_name == 'content_crawl':
                result = self.execute_content_crawl(params)
            elif step_name == 'forum_publish':
                result = self.execute_forum_publish(params)
            else:
                result = {
                    'success': False,
                    'message': f'未知步骤: {step_name}'
                }
            
            # 添加执行时间信息
            execution_time = time.time() - self.step_start_time
            result['execution_time'] = execution_time
            
            logger.info(f"步骤 {step_name} 执行完成，耗时 {execution_time:.1f} 秒")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - self.step_start_time
            logger.error(f"步骤 {step_name} 执行异常: {e}")
            
            return {
                'success': False,
                'message': f'步骤执行异常: {str(e)}',
                'execution_time': execution_time
            }
        
        finally:
            self.current_step = None
            self.step_start_time = None
