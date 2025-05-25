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
import logging

# 确保此脚本的父目录（WZ）在 sys.path 中
current_script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from wzzq.wechat_crawler import WechatCrawler, CredentialsExpiredError, RateLimitError
from wzzq.db import DatabaseManager

# 新增: 配置日志
logger = logging.getLogger(__name__)
# (通常由调用此脚本的环境配置，或在此处添加基本配置)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        print("错误: 未找到有效的认证信息，请确保WZ/data/id_info.json文件存在且包含有效的token和cookie。", file=sys.stderr)
        return 1
    
    # 抓取文章
    articles = []
    try:
        if args.account:
            print(f"正在抓取公众号【{args.account}】的文章...")
            articles = crawler.get_articles(args.account, limit=args.limit)
        else:
            print(f"正在抓取所有配置的公众号文章...")
            articles = crawler.crawl_all_accounts(limit_per_account=args.limit)
    
        print(f"共抓取到 {len(articles)} 篇文章")

    # 2.2. 捕获新异常并处理
    except CredentialsExpiredError as e:
        logger.error(f"捕获到凭据失效错误: {e}")
        print("错误: 微信凭证已失效，请更新凭证后重试。", file=sys.stderr)
        print("CREDENTIALS_EXPIRED_FLAG", file=sys.stdout) # 特殊标记
        return 2 # 特定退出码表示凭据失效
    except RateLimitError as e:
        logger.error(f"捕获到请求频率控制错误: {e}")
        print(f"错误: 请求频率过快 - {e}。请稍后再试。", file=sys.stderr)
        return 3 # 特定退出码表示频率控制
    except Exception as e: # 其他通用抓取异常
        logger.error(f"抓取文章过程中发生未知错误: {e}", exc_info=True)
        print(f"错误: 抓取文章过程中发生未知错误 - {e}", file=sys.stderr)
        return 1 # 通用错误退出码

    # 调试模式下只打印不保存
    if args.debug:
        print("\n调试模式：文章列表")
        for i, article in enumerate(articles, 1):
            print(f"{i}. {article['account_name']} - {article['title']} - {article['publish_timestamp']}")
        return 0
    
    # 保存到数据库
    if articles:
        print("正在保存文章到数据库...")
        try: # 为数据库操作也添加 try-except
            with DatabaseManager() as db:
                if not db.conn: # connect() 内部会打印错误，这里可以简化
                    print("数据库连接失败，无法保存文章", file=sys.stderr)
                    return 1 # 或其他特定数据库错误码
                
                success_count = db.save_articles_batch(articles)
                print(f"成功保存 {success_count} 篇文章到数据库")
        except Exception as e:
            logger.error(f"保存文章到数据库时发生错误: {e}", exc_info=True)
            print(f"错误: 保存文章到数据库时发生错误 - {e}", file=sys.stderr)
            return 1 # 通用错误退出码（或特定数据库错误码）
    
    return 0


if __name__ == '__main__':
    # 基本日志配置示例 (如果需要独立运行此脚本并查看日志)
    # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    exit_code = 0
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n程序被用户中断", file=sys.stderr)
        exit_code = 130 # SIGINT 通常是 130
    except Exception as e: # 捕获 main() 中未被捕获的意外错误
        # logger 已在 main 内部使用，这里主要确保程序以错误码退出
        print(f"程序运行顶层错误: {e}", file=sys.stderr)
        exit_code = 1
    finally:
        sys.exit(exit_code) 