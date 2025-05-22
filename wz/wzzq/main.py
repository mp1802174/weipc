#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取主程序
"""

import argparse
from tqdm import tqdm
import sys
import os
import datetime

# 确保此脚本的父目录（WZ）在 sys.path 中
current_script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from wzzq.wechat_crawler import WechatCrawler
from wzzq.db import DatabaseManager


def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='微信公众号文章抓取工具')
    parser.add_argument('--account', '-a', help='指定抓取单个公众号，默认抓取所有已配置的公众号')
    parser.add_argument('--limit', '-l', type=int, default=10, help='每个公众号抓取的文章数量限制，默认10篇')
    parser.add_argument('--debug', '-d', action='store_true', help='启用调试模式，只打印不保存到数据库')
    
    args = parser.parse_args()
    
    # 创建抓取器
    crawler = WechatCrawler()
    
    # 检查认证状态
    if not crawler.is_authenticated():
        print("错误: 未找到有效的认证信息，请确保WZ/data/id_info.json文件存在且包含有效的token和cookie。")
        return 1
    
    # 抓取文章
    if args.account:
        print(f"正在抓取公众号【{args.account}】的文章...")
        articles = crawler.get_articles(args.account, limit=args.limit)
    else:
        print(f"正在抓取所有配置的公众号文章...")
        articles = crawler.crawl_all_accounts(limit_per_account=args.limit)
    
    print(f"共抓取到 {len(articles)} 篇文章")
    
    # 调试模式下只打印不保存
    if args.debug:
        print("\n调试模式：文章列表")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['account_name']} - {article['title']} - {article['publish_timestamp']}")
        return 0
    
    # 保存到数据库
    if articles:
        print("正在保存文章到数据库...")
        with DatabaseManager() as db:
            if not db.conn:
                print("数据库连接失败，无法保存文章")
                return 1
            
            success_count = db.save_articles_batch(articles)
            print(f"成功保存 {success_count} 篇文章到数据库")
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"程序运行错误: {e}")
        sys.exit(1) 