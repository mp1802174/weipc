#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目集成主程序
提供统一的命令行接口，整合所有模块功能
"""

import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.integrated_crawler import IntegratedCrawler, batch_crawl_from_database, crawl_urls
from core.database import UnifiedDatabaseManager, get_db_manager
from core.config import get_config, set_config_file
from wzzq.wechat_crawler import WechatCrawler
from wechat_mp_auth.auth import WeChatAuth

def setup_logging(verbose: bool = False):
    """设置日志"""
    import logging
    
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('wz_integrated.log', encoding='utf-8')
        ]
    )

def cmd_crawl_database(args):
    """从数据库采集文章命令"""
    print("=== 从数据库采集文章 ===")
    
    result = batch_crawl_from_database(
        source_type=args.source_type,
        limit=args.limit,
        batch_size=args.batch_size
    )
    
    print(f"采集完成:")
    print(f"  总计处理: {result.get('total_processed', 0)}")
    print(f"  成功: {result.get('successful', 0)}")
    print(f"  失败: {result.get('failed', 0)}")
    print(f"  跳过: {result.get('skipped', 0)}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"结果已保存到: {args.output}")

def cmd_crawl_urls(args):
    """根据URL列表采集命令"""
    print("=== 根据URL列表采集 ===")
    
    urls = []
    if args.urls:
        urls.extend(args.urls)
    
    if args.url_file:
        with open(args.url_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    
    if not urls:
        print("错误: 没有提供URL")
        return
    
    print(f"准备采集 {len(urls)} 个URL")
    
    result = crawl_urls(
        urls=urls,
        source_type=args.source_type or "external",
        source_name=args.source_name or "手动导入"
    )
    
    print(f"采集完成:")
    print(f"  总计: {result['total']}")
    print(f"  成功: {result['summary']['success']}")
    print(f"  失败: {result['summary']['failed']}")
    print(f"  跳过: {result['summary']['skipped']}")
    print(f"  错误: {result['summary']['error']}")
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"结果已保存到: {args.output}")

def cmd_fetch_wechat_links(args):
    """获取微信公众号链接命令"""
    print("=== 获取微信公众号链接 ===")
    
    try:
        # 初始化微信认证
        auth = WeChatAuth()
        if not auth.check_login_status():
            print("微信登录状态无效，请先登录")
            return
        
        # 初始化微信爬虫
        crawler = WechatCrawler()
        
        # 获取账号列表
        if args.account_name:
            accounts = [args.account_name]
        else:
            # 从配置文件获取所有账号
            config = get_config()
            accounts_file = config.get_data_path(config.wechat.accounts_file)
            
            if accounts_file.exists():
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    accounts_data = json.load(f)
                accounts = list(accounts_data.keys())
            else:
                print("错误: 未找到账号配置文件")
                return
        
        print(f"准备获取 {len(accounts)} 个账号的文章链接")
        
        total_fetched = 0
        for account in accounts:
            print(f"正在处理账号: {account}")
            try:
                count = crawler.crawl_account_articles(account, limit=args.limit_per_account)
                total_fetched += count
                print(f"  获取到 {count} 篇文章链接")
            except Exception as e:
                print(f"  处理账号失败: {e}")
        
        print(f"总计获取 {total_fetched} 篇文章链接")
        
    except Exception as e:
        print(f"获取微信链接失败: {e}")

def cmd_status(args):
    """查看系统状态命令"""
    print("=== WZ系统状态 ===")
    
    try:
        db_manager = get_db_manager()
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            return
        
        print("✅ 数据库连接正常")
        
        # 获取统计信息
        crawl_stats = db_manager.get_crawl_statistics()
        
        print("\n📊 采集统计:")
        for source_type, stats in crawl_stats.items():
            print(f"  {source_type}:")
            print(f"    总计: {stats['total_articles']}")
            print(f"    已完成: {stats['completed']}")
            print(f"    待处理: {stats['pending']}")
            print(f"    失败: {stats['failed']}")
            print(f"    平均字数: {stats['avg_word_count']:.0f}" if stats['avg_word_count'] else "    平均字数: 0")
        
        # 检查配置
        config = get_config()
        print(f"\n⚙️ 配置状态:")
        print(f"  微信采集: {'启用' if config.wechat.enabled else '禁用'}")
        print(f"  CFCJ采集: {'启用' if config.cfcj.enabled else '禁用'}")
        print(f"  自动发布: {'启用' if config.publisher.enabled else '禁用'}")
        
        db_manager.disconnect()
        
    except Exception as e:
        print(f"获取状态失败: {e}")

def cmd_config(args):
    """配置管理命令"""
    print("=== 配置管理 ===")
    
    config = get_config()
    
    if args.show:
        print("当前配置:")
        config_dict = config.to_dict()
        print(json.dumps(config_dict, indent=2, ensure_ascii=False))
    
    elif args.set_key and args.set_value:
        if config.set(args.set_key, args.set_value):
            config.save_config()
            print(f"配置已更新: {args.set_key} = {args.set_value}")
        else:
            print(f"配置更新失败: {args.set_key}")
    
    elif args.get_key:
        value = config.get(args.get_key)
        print(f"{args.get_key} = {value}")
    
    else:
        print("请指定配置操作 (--show, --set-key/--set-value, --get-key)")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='WZ项目集成管理工具')
    
    # 全局参数
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    parser.add_argument('--output', '-o', help='输出文件路径')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 从数据库采集命令
    crawl_db_parser = subparsers.add_parser('crawl-db', help='从数据库采集文章')
    crawl_db_parser.add_argument('--source-type', help='源类型过滤 (wechat, linux_do, nodeseek)')
    crawl_db_parser.add_argument('--limit', type=int, default=100, help='限制采集数量')
    crawl_db_parser.add_argument('--batch-size', type=int, default=5, help='批次大小')
    
    # URL采集命令
    crawl_urls_parser = subparsers.add_parser('crawl-urls', help='根据URL列表采集')
    crawl_urls_parser.add_argument('urls', nargs='*', help='URL列表')
    crawl_urls_parser.add_argument('--url-file', help='包含URL的文件')
    crawl_urls_parser.add_argument('--source-type', default='external', help='源类型')
    crawl_urls_parser.add_argument('--source-name', default='手动导入', help='源名称')
    
    # 微信链接获取命令
    wechat_parser = subparsers.add_parser('fetch-wechat', help='获取微信公众号链接')
    wechat_parser.add_argument('--account-name', help='指定账号名称')
    wechat_parser.add_argument('--limit-per-account', type=int, default=20, help='每个账号的文章数量限制')
    
    # 状态查看命令
    status_parser = subparsers.add_parser('status', help='查看系统状态')
    
    # 配置管理命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--get-key', help='获取配置值')
    config_parser.add_argument('--set-key', help='设置配置键')
    config_parser.add_argument('--set-value', help='设置配置值')
    
    # 解析参数
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    # 设置配置文件
    if args.config:
        set_config_file(args.config)
    
    # 执行命令
    if args.command == 'crawl-db':
        cmd_crawl_database(args)
    elif args.command == 'crawl-urls':
        cmd_crawl_urls(args)
    elif args.command == 'fetch-wechat':
        cmd_fetch_wechat_links(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'config':
        cmd_config(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
