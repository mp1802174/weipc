#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理器
负责协调整个自动化工作流的执行
"""

import json
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path

from .status_checker import StatusChecker
from .step_executor import StepExecutor
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)

class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self, config_file: str = "auto_workflow_config.json"):
        """
        初始化工作流管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        self.status_checker = StatusChecker()
        self.step_executor = StepExecutor()
        self.progress_tracker = ProgressTracker()
        
        self.interrupted = False
        self.current_execution_id = None
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"配置文件加载成功: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "steps": {
                "link_crawl": {
                    "enabled": True,
                    "timeout": 600,
                    "retry_count": 2,
                    "params": {
                        "limit_per_account": 10,
                        "total_limit": 50,
                        "accounts": ["all"]
                    }
                },
                "content_crawl": {
                    "enabled": True,
                    "timeout": 1800,
                    "retry_count": 1,
                    "params": {
                        "limit": 50,
                        "batch_size": 5
                    }
                },
                "forum_publish": {
                    "enabled": True,
                    "timeout": 3600,
                    "retry_count": 1,
                    "params": {
                        "limit": 100,
                        "interval_min": 60,
                        "interval_max": 120
                    }
                }
            }
        }
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，准备安全停止...")
        self.interrupted = True
    
    def check_status(self) -> Dict:
        """检查所有步骤的状态"""
        logger.info("检查工作流状态...")
        return self.status_checker.get_overall_status(self.config)
    
    def execute_workflow(self, 
                        steps: Optional[List[str]] = None,
                        from_step: Optional[str] = None,
                        execution_id: Optional[str] = None,
                        progress_callback: Optional[Callable] = None) -> Dict:
        """
        执行完整工作流
        
        Args:
            steps: 要执行的步骤列表，None表示执行所有启用的步骤
            from_step: 从指定步骤开始执行
            execution_id: 执行ID，用于恢复中断的执行
            progress_callback: 进度回调函数
            
        Returns:
            Dict: 执行结果
        """
        # 开始或恢复执行
        if execution_id:
            if not self.progress_tracker.load_execution(execution_id):
                logger.error(f"无法加载执行进度: {execution_id}")
                return {'success': False, 'message': '无法加载执行进度'}
            self.current_execution_id = execution_id
            logger.info(f"恢复执行: {execution_id}")
        else:
            self.current_execution_id = self.progress_tracker.start_execution()
            logger.info(f"开始新执行: {self.current_execution_id}")
        
        try:
            # 获取要执行的步骤
            steps_config = self.config.get('steps', {})
            
            if steps is None:
                # 执行所有启用的步骤
                execution_steps = [name for name, config in steps_config.items() 
                                 if config.get('enabled', True)]
            else:
                execution_steps = steps
            
            # 如果指定了起始步骤，从该步骤开始
            if from_step:
                try:
                    start_index = execution_steps.index(from_step)
                    execution_steps = execution_steps[start_index:]
                except ValueError:
                    logger.error(f"起始步骤不存在: {from_step}")
                    return {'success': False, 'message': f'起始步骤不存在: {from_step}'}
            
            logger.info(f"将执行步骤: {execution_steps}")
            
            # 检查状态
            overall_status = self.status_checker.get_overall_status(self.config)
            
            # 执行各个步骤
            for step_name in execution_steps:
                if self.interrupted:
                    logger.info("执行被中断")
                    break
                
                if step_name not in steps_config:
                    logger.warning(f"步骤配置不存在: {step_name}")
                    continue
                
                step_config = steps_config[step_name]
                
                # 检查步骤是否启用
                if not step_config.get('enabled', True):
                    logger.info(f"步骤已禁用，跳过: {step_name}")
                    self.progress_tracker.update_step_status(step_name, 'skipped', 
                                                           reason='步骤已禁用')
                    continue
                
                # 检查是否需要执行
                step_status = overall_status['steps'].get(step_name, {})
                if not step_status.get('should_execute', False):
                    logger.info(f"步骤无需执行，跳过: {step_name} - {step_status.get('reason', '')}")
                    self.progress_tracker.update_step_status(step_name, 'skipped',
                                                           reason=step_status.get('reason', '无需执行'))
                    continue
                
                # 执行步骤
                self._execute_single_step(step_name, step_config, progress_callback)
            
            # 完成执行
            final_status = 'interrupted' if self.interrupted else 'completed'
            self.progress_tracker.finish_execution(final_status)
            
            # 获取最终结果
            final_progress = self.progress_tracker.get_progress()
            
            return {
                'success': not self.interrupted,
                'execution_id': self.current_execution_id,
                'status': final_status,
                'summary': final_progress.get('summary', {}),
                'steps': final_progress.get('steps', {})
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            self.progress_tracker.finish_execution('failed')
            return {
                'success': False,
                'execution_id': self.current_execution_id,
                'error': str(e)
            }
    
    def _execute_single_step(self, step_name: str, step_config: Dict, progress_callback: Optional[Callable]):
        """执行单个步骤"""
        logger.info(f"开始执行步骤: {step_name}")
        
        # 更新步骤状态为运行中
        self.progress_tracker.update_step_status(step_name, 'running')
        
        if progress_callback:
            try:
                progress_callback('step_start', step_name, {})
            except Exception as e:
                logger.warning(f"进度回调失败: {e}")
        
        # 执行步骤
        retry_count = step_config.get('retry_count', 1)
        timeout = step_config.get('timeout', 3600)
        
        for attempt in range(retry_count + 1):
            if self.interrupted:
                break
            
            try:
                if attempt > 0:
                    logger.info(f"重试步骤 {step_name}，第 {attempt} 次")
                
                result = self.step_executor.execute_step(step_name, step_config, timeout)
                
                if result.get('success', False):
                    # 步骤执行成功
                    self.progress_tracker.update_step_status(step_name, 'completed', 
                                                           result=result)
                    logger.info(f"步骤 {step_name} 执行成功: {result.get('message', '')}")
                    
                    if progress_callback:
                        try:
                            progress_callback('step_complete', step_name, result)
                        except Exception as e:
                            logger.warning(f"进度回调失败: {e}")
                    
                    break
                else:
                    # 步骤执行失败
                    if attempt < retry_count:
                        logger.warning(f"步骤 {step_name} 执行失败，将重试: {result.get('message', '')}")
                        continue
                    else:
                        self.progress_tracker.update_step_status(step_name, 'failed',
                                                               result=result,
                                                               error=result.get('message', ''))
                        logger.error(f"步骤 {step_name} 执行失败: {result.get('message', '')}")
                        
                        if progress_callback:
                            try:
                                progress_callback('step_failed', step_name, result)
                            except Exception as e:
                                logger.warning(f"进度回调失败: {e}")
                        
                        break
                        
            except Exception as e:
                if attempt < retry_count:
                    logger.warning(f"步骤 {step_name} 执行异常，将重试: {e}")
                    continue
                else:
                    self.progress_tracker.update_step_status(step_name, 'failed',
                                                           error=str(e))
                    logger.error(f"步骤 {step_name} 执行异常: {e}")
                    break
    
    def resume_execution(self, execution_id: str, progress_callback: Optional[Callable] = None) -> Dict:
        """恢复中断的执行"""
        logger.info(f"恢复执行: {execution_id}")
        return self.execute_workflow(execution_id=execution_id, progress_callback=progress_callback)
    
    def get_resumable_executions(self) -> List[Dict]:
        """获取可恢复的执行列表"""
        return self.progress_tracker.get_resumable_executions()
