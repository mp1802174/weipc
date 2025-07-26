#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动化工作流
"""

import sys
import logging
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from auto.workflow_manager import WorkflowManager
from auto.status_checker import StatusChecker

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def test_status_checker():
    """测试状态检测器"""
    print("🔍 测试状态检测器...")
    
    try:
        checker = StatusChecker()
        
        # 测试链接采集状态检查
        print("\n📋 测试链接采集状态检查:")
        link_config = {
            'limit_per_account': 10,
            'total_limit': 50,
            'accounts': ['all']
        }
        link_status = checker.check_link_crawl_status(link_config)
        print(f"   应该执行: {link_status['should_execute']}")
        print(f"   原因: {link_status['reason']}")
        print(f"   预计新文章: {link_status['estimated_new_articles']}")
        
        # 测试内容采集状态检查
        print("\n📋 测试内容采集状态检查:")
        content_config = {
            'limit': 50,
            'batch_size': 5
        }
        content_status = checker.check_content_crawl_status(content_config)
        print(f"   应该执行: {content_status['should_execute']}")
        print(f"   原因: {content_status['reason']}")
        print(f"   待处理文章: {content_status['pending_articles']}")
        
        # 测试论坛发布状态检查
        print("\n📋 测试论坛发布状态检查:")
        publish_config = {
            'limit': 100,
            'interval_min': 60,
            'interval_max': 120
        }
        publish_status = checker.check_forum_publish_status(publish_config)
        print(f"   应该执行: {publish_status['should_execute']}")
        print(f"   原因: {publish_status['reason']}")
        print(f"   待发布文章: {publish_status['pending_articles']}")
        
        print("\n✅ 状态检测器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 状态检测器测试失败: {e}")
        return False

def test_workflow_manager():
    """测试工作流管理器"""
    print("\n🔧 测试工作流管理器...")
    
    try:
        manager = WorkflowManager()
        
        # 测试状态检查
        print("\n📋 测试整体状态检查:")
        overall_status = manager.check_status()
        
        print(f"   检查时间: {overall_status['timestamp']}")
        print(f"   总步骤数: {overall_status['summary']['total_steps']}")
        print(f"   启用步骤数: {overall_status['summary']['enabled_steps']}")
        print(f"   可执行步骤数: {overall_status['summary']['executable_steps']}")
        
        print("\n📝 各步骤状态:")
        for step_name, step_info in overall_status['steps'].items():
            step_display_name = {
                'link_crawl': '微信链接采集',
                'content_crawl': '内容采集',
                'forum_publish': '论坛发布'
            }.get(step_name, step_name)
            
            enabled = step_info.get('enabled', False)
            should_execute = step_info.get('should_execute', False)
            reason = step_info.get('reason', '')
            
            status_icon = "✅" if should_execute else "⏭️" if enabled else "❌"
            print(f"   {status_icon} {step_display_name}: {reason}")
        
        print("\n✅ 工作流管理器测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 工作流管理器测试失败: {e}")
        return False

def test_dry_run():
    """测试干运行（不实际执行步骤）"""
    print("\n🧪 测试干运行模式...")
    
    try:
        manager = WorkflowManager()
        
        # 检查可恢复的执行
        resumable = manager.get_resumable_executions()
        print(f"\n📋 可恢复的执行数量: {len(resumable)}")
        
        for execution in resumable:
            print(f"   - ID: {execution['execution_id']}")
            print(f"     开始时间: {execution['start_time']}")
            print(f"     当前步骤: {execution.get('current_step', '未知')}")
        
        print("\n✅ 干运行测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 干运行测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 自动化工作流测试")
    print("=" * 60)
    
    setup_logging()
    
    # 运行各项测试
    tests = [
        ("状态检测器", test_status_checker),
        ("工作流管理器", test_workflow_manager),
        ("干运行模式", test_dry_run)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🔬 测试: {test_name}")
        print("=" * 60)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            logging.exception(f"测试异常: {test_name}")
    
    # 总结
    print(f"\n{'='*60}")
    print(f"📊 测试总结: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！自动化工作流准备就绪")
        print("\n💡 使用方法:")
        print("   python auto_workflow.py --status          # 检查状态")
        print("   python auto_workflow.py                   # 执行完整流程")
        print("   python auto_workflow.py --steps link_crawl # 只执行链接采集")
    else:
        print("⚠️  部分测试失败，请检查配置和依赖")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
