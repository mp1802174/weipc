#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WZ系统自动化工作流主脚本
提供命令行界面执行全自动的微信采集 → 内容采集 → 论坛发布流程
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from auto.workflow_manager import WorkflowManager

def setup_logging(level: str = "INFO", log_file: bool = True):
    """设置日志"""
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # 文件处理器
    handlers = [console_handler]
    if log_file:
        log_filename = log_dir / f"auto_workflow_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True
    )

def print_banner():
    """打印横幅"""
    banner = """
🚀 WZ系统自动化工作流 - {}
================================================================
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print(banner)

def print_status_overview(status: dict):
    """打印状态概览"""
    print("\n📊 执行概览:")
    
    steps = status.get('steps', {})
    for step_name, step_info in steps.items():
        enabled = step_info.get('enabled', False)
        should_execute = step_info.get('should_execute', False)
        reason = step_info.get('reason', '')
        
        if not enabled:
            status_icon = "❌"
            status_text = "已禁用"
        elif should_execute:
            status_icon = "✅"
            status_text = "待执行"
        else:
            status_icon = "⏭️"
            status_text = "跳过"
        
        step_display_name = {
            'link_crawl': '微信链接采集',
            'content_crawl': '内容采集',
            'forum_publish': '论坛发布'
        }.get(step_name, step_name)
        
        print(f"   {status_icon} {step_display_name} - {status_text}")
        if reason:
            print(f"      原因: {reason}")

def progress_callback(event_type: str, step_name: str, data: dict):
    """进度回调函数"""
    step_display_name = {
        'link_crawl': '微信链接采集',
        'content_crawl': '内容采集', 
        'forum_publish': '论坛发布'
    }.get(step_name, step_name)
    
    if event_type == 'step_start':
        print(f"\n🔄 开始执行: {step_display_name}")
        print(f"   ⏱️  开始时间: {datetime.now().strftime('%H:%M:%S')}")
    
    elif event_type == 'step_complete':
        execution_time = data.get('execution_time', 0)
        message = data.get('message', '')
        print(f"✅ 完成: {step_display_name}")
        print(f"   ⏱️  耗时: {execution_time:.1f}秒")
        print(f"   📝 结果: {message}")
    
    elif event_type == 'step_failed':
        execution_time = data.get('execution_time', 0)
        message = data.get('message', '')
        print(f"❌ 失败: {step_display_name}")
        print(f"   ⏱️  耗时: {execution_time:.1f}秒")
        print(f"   ❗ 错误: {message}")

def print_final_summary(result: dict):
    """打印最终总结"""
    print("\n" + "="*64)
    print("📋 执行总结:")
    
    execution_id = result.get('execution_id', 'unknown')
    status = result.get('status', 'unknown')
    summary = result.get('summary', {})
    
    print(f"   执行ID: {execution_id}")
    print(f"   最终状态: {status}")
    print(f"   总步骤数: {summary.get('total_steps', 0)}")
    print(f"   完成步骤: {summary.get('completed_steps', 0)}")
    print(f"   失败步骤: {summary.get('failed_steps', 0)}")
    print(f"   跳过步骤: {summary.get('skipped_steps', 0)}")
    
    # 显示各步骤详情
    steps = result.get('steps', {})
    if steps:
        print("\n📝 步骤详情:")
        for step_name, step_info in steps.items():
            step_display_name = {
                'link_crawl': '微信链接采集',
                'content_crawl': '内容采集',
                'forum_publish': '论坛发布'
            }.get(step_name, step_name)
            
            status = step_info.get('status', 'unknown')
            duration = step_info.get('duration', 0)
            
            status_icon = {
                'completed': '✅',
                'failed': '❌',
                'skipped': '⏭️',
                'running': '🔄'
            }.get(status, '❓')
            
            print(f"   {status_icon} {step_display_name}: {status}")
            if duration:
                print(f"      耗时: {duration:.1f}秒")
            
            # 显示结果信息
            step_result = step_info.get('result', {})
            if step_result:
                if step_name == 'link_crawl':
                    new_articles = step_result.get('new_articles', 0)
                    print(f"      新增文章: {new_articles}篇")
                elif step_name == 'content_crawl':
                    processed = step_result.get('processed_articles', 0)
                    print(f"      处理文章: {processed}篇")
                elif step_name == 'forum_publish':
                    published = step_result.get('published_articles', 0)
                    print(f"      发布文章: {published}篇")
    
    print("="*64)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='WZ系统自动化工作流')
    
    # 基本参数
    parser.add_argument('--config', default='auto_workflow_config.json',
                       help='配置文件路径')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别')
    
    # 执行控制
    parser.add_argument('--steps', 
                       help='要执行的步骤，用逗号分隔 (link_crawl,content_crawl,forum_publish)')
    parser.add_argument('--from', dest='from_step',
                       help='从指定步骤开始执行')
    parser.add_argument('--resume',
                       help='恢复指定ID的执行')
    
    # 功能选项
    parser.add_argument('--status', action='store_true',
                       help='只检查状态，不执行')
    parser.add_argument('--list-resumable', action='store_true',
                       help='列出可恢复的执行')
    parser.add_argument('--github-actions', action='store_true',
                       help='GitHub Actions模式，使用环境变量配置')
    
    # 数量控制
    parser.add_argument('--link-limit', type=int,
                       help='链接采集数量限制')
    parser.add_argument('--content-limit', type=int,
                       help='内容采集数量限制')
    parser.add_argument('--publish-limit', type=int,
                       help='论坛发布数量限制')
    parser.add_argument('--accounts',
                       help='要采集的公众号，用逗号分隔')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    
    # 打印横幅
    print_banner()
    
    try:
        # GitHub Actions模式处理
        if args.github_actions:
            # 使用GitHub Actions专用脚本
            import subprocess

            github_script = Path(__file__).parent / "github_auto_workflow.py"
            cmd = [sys.executable, str(github_script)]

            if args.steps:
                cmd.extend(['--steps', args.steps])
            if args.link_limit:
                cmd.extend(['--link-limit', str(args.link_limit)])
            if args.content_limit:
                cmd.extend(['--content-limit', str(args.content_limit)])
            if args.publish_limit:
                cmd.extend(['--publish-limit', str(args.publish_limit)])
            if args.status:
                cmd.append('--dry-run')

            print(f"🚀 启动GitHub Actions模式: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            sys.exit(result.returncode)

        # 创建工作流管理器
        workflow_manager = WorkflowManager(args.config)
        
        # 处理命令行参数覆盖配置
        if args.link_limit:
            workflow_manager.config['steps']['link_crawl']['params']['total_limit'] = args.link_limit
        if args.content_limit:
            workflow_manager.config['steps']['content_crawl']['params']['limit'] = args.content_limit
        if args.publish_limit:
            workflow_manager.config['steps']['forum_publish']['params']['limit'] = args.publish_limit
        if args.accounts:
            accounts = [acc.strip() for acc in args.accounts.split(',')]
            workflow_manager.config['steps']['link_crawl']['params']['accounts'] = accounts
        
        # 处理不同的命令
        if args.list_resumable:
            resumable = workflow_manager.get_resumable_executions()
            if resumable:
                print("📋 可恢复的执行:")
                for execution in resumable:
                    print(f"   ID: {execution['execution_id']}")
                    print(f"   开始时间: {execution['start_time']}")
                    print(f"   当前步骤: {execution.get('current_step', '未知')}")
                    print()
            else:
                print("没有可恢复的执行")
            return
        
        if args.status:
            # 只检查状态
            print("🔍 检查工作流状态...")
            status = workflow_manager.check_status()
            print_status_overview(status)
            return
        
        # 执行工作流
        steps = None
        if args.steps:
            steps = [step.strip() for step in args.steps.split(',')]
        
        if args.resume:
            print(f"🔄 恢复执行: {args.resume}")
            result = workflow_manager.resume_execution(args.resume, progress_callback)
        else:
            # 先检查状态
            print("🔍 检查工作流状态...")
            status = workflow_manager.check_status()
            print_status_overview(status)
            
            # 询问是否继续
            if not any(step.get('should_execute', False) for step in status.get('steps', {}).values()):
                print("\n💡 所有步骤都无需执行")
                return
            
            print(f"\n💡 按 Ctrl+C 可安全停止 (当前步骤完成后)")
            print("="*64)
            
            result = workflow_manager.execute_workflow(
                steps=steps,
                from_step=args.from_step,
                progress_callback=progress_callback
            )
        
        # 打印最终总结
        print_final_summary(result)
        
        # 设置退出码
        if result.get('success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        logging.exception("执行异常")
        sys.exit(1)

if __name__ == "__main__":
    main()
