#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度跟踪器
负责跟踪和保存工作流执行进度，支持断点续传
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, progress_dir: str = "logs"):
        """
        初始化进度跟踪器
        
        Args:
            progress_dir: 进度文件存储目录
        """
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(exist_ok=True)
        
        self.current_execution = None
        self.progress_file = None
    
    def start_execution(self, execution_id: Optional[str] = None) -> str:
        """
        开始新的执行
        
        Args:
            execution_id: 执行ID，如果不提供则自动生成
            
        Returns:
            str: 执行ID
        """
        if execution_id is None:
            execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.current_execution = {
            'execution_id': execution_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'status': 'running',
            'current_step': None,
            'steps': {},
            'summary': {
                'total_steps': 0,
                'completed_steps': 0,
                'failed_steps': 0,
                'skipped_steps': 0
            },
            'logs': []
        }
        
        self.progress_file = self.progress_dir / f"progress_{execution_id}.json"
        self._save_progress()
        
        logger.info(f"开始新的执行: {execution_id}")
        return execution_id
    
    def load_execution(self, execution_id: str) -> bool:
        """
        加载已存在的执行进度
        
        Args:
            execution_id: 执行ID
            
        Returns:
            bool: 是否成功加载
        """
        progress_file = self.progress_dir / f"progress_{execution_id}.json"
        
        if not progress_file.exists():
            logger.error(f"进度文件不存在: {progress_file}")
            return False
        
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                self.current_execution = json.load(f)
            
            self.progress_file = progress_file
            logger.info(f"成功加载执行进度: {execution_id}")
            return True
            
        except Exception as e:
            logger.error(f"加载进度文件失败: {e}")
            return False
    
    def update_step_status(self, step_name: str, status: str, **kwargs):
        """
        更新步骤状态
        
        Args:
            step_name: 步骤名称
            status: 状态 (pending, running, completed, failed, skipped)
            **kwargs: 其他状态信息
        """
        if not self.current_execution:
            logger.warning("没有活动的执行，无法更新步骤状态")
            return
        
        timestamp = datetime.now().isoformat()
        
        if step_name not in self.current_execution['steps']:
            self.current_execution['steps'][step_name] = {
                'status': 'pending',
                'start_time': None,
                'end_time': None,
                'duration': None,
                'result': {},
                'error': None
            }
            self.current_execution['summary']['total_steps'] += 1
        
        step_info = self.current_execution['steps'][step_name]
        old_status = step_info['status']
        step_info['status'] = status
        
        # 更新时间戳
        if status == 'running' and old_status == 'pending':
            step_info['start_time'] = timestamp
            self.current_execution['current_step'] = step_name
        elif status in ['completed', 'failed', 'skipped']:
            step_info['end_time'] = timestamp
            if step_info['start_time']:
                start_time = datetime.fromisoformat(step_info['start_time'])
                end_time = datetime.fromisoformat(timestamp)
                step_info['duration'] = (end_time - start_time).total_seconds()
            
            # 更新统计
            if old_status != status:
                if status == 'completed':
                    self.current_execution['summary']['completed_steps'] += 1
                elif status == 'failed':
                    self.current_execution['summary']['failed_steps'] += 1
                elif status == 'skipped':
                    self.current_execution['summary']['skipped_steps'] += 1
        
        # 更新其他信息
        for key, value in kwargs.items():
            step_info[key] = value
        
        self._save_progress()
        
        # 添加日志
        self.add_log(f"步骤 {step_name}: {status}", level='info')
    
    def add_log(self, message: str, level: str = 'info', step: Optional[str] = None):
        """
        添加日志记录
        
        Args:
            message: 日志消息
            level: 日志级别
            step: 相关步骤
        """
        if not self.current_execution:
            return
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'step': step
        }
        
        self.current_execution['logs'].append(log_entry)
        
        # 保持日志数量在合理范围内
        if len(self.current_execution['logs']) > 1000:
            self.current_execution['logs'] = self.current_execution['logs'][-500:]
        
        self._save_progress()
    
    def finish_execution(self, status: str = 'completed'):
        """
        完成执行
        
        Args:
            status: 最终状态 (completed, failed, interrupted)
        """
        if not self.current_execution:
            return
        
        self.current_execution['end_time'] = datetime.now().isoformat()
        self.current_execution['status'] = status
        self.current_execution['current_step'] = None
        
        # 计算总耗时
        if self.current_execution['start_time']:
            start_time = datetime.fromisoformat(self.current_execution['start_time'])
            end_time = datetime.fromisoformat(self.current_execution['end_time'])
            self.current_execution['total_duration'] = (end_time - start_time).total_seconds()
        
        self._save_progress()
        
        logger.info(f"执行完成: {self.current_execution['execution_id']}, 状态: {status}")
    
    def get_progress(self) -> Optional[Dict]:
        """
        获取当前进度
        
        Returns:
            Dict: 进度信息
        """
        return self.current_execution.copy() if self.current_execution else None
    
    def get_resumable_executions(self) -> List[Dict]:
        """
        获取可恢复的执行列表
        
        Returns:
            List[Dict]: 可恢复的执行信息
        """
        resumable = []
        
        for progress_file in self.progress_dir.glob("progress_*.json"):
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    execution = json.load(f)
                
                # 只返回未完成的执行
                if execution.get('status') == 'running':
                    resumable.append({
                        'execution_id': execution['execution_id'],
                        'start_time': execution['start_time'],
                        'current_step': execution.get('current_step'),
                        'progress_file': str(progress_file)
                    })
                    
            except Exception as e:
                logger.warning(f"读取进度文件失败 {progress_file}: {e}")
        
        return sorted(resumable, key=lambda x: x['start_time'], reverse=True)
    
    def cleanup_old_progress(self, days: int = 30):
        """
        清理旧的进度文件
        
        Args:
            days: 保留天数
        """
        cutoff_time = time.time() - (days * 24 * 3600)
        
        for progress_file in self.progress_dir.glob("progress_*.json"):
            try:
                if progress_file.stat().st_mtime < cutoff_time:
                    progress_file.unlink()
                    logger.info(f"删除旧进度文件: {progress_file}")
            except Exception as e:
                logger.warning(f"删除进度文件失败 {progress_file}: {e}")
    
    def _save_progress(self):
        """保存进度到文件"""
        if not self.current_execution or not self.progress_file:
            return
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_execution, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存进度文件失败: {e}")
    
    def get_step_progress(self, step_name: str) -> Optional[Dict]:
        """
        获取特定步骤的进度
        
        Args:
            step_name: 步骤名称
            
        Returns:
            Dict: 步骤进度信息
        """
        if not self.current_execution:
            return None
        
        return self.current_execution['steps'].get(step_name)
