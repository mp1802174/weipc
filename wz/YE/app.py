#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取Web界面
基于Flask的交互界面，用于执行文章抓取、凭证更新和管理定期抓取任务
"""

import os
import sys
import json
import logging
import subprocess
import datetime
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.cron import CronTrigger

# 设置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WZ_DIR = os.path.dirname(BASE_DIR)
if WZ_DIR not in sys.path:
    sys.path.insert(0, WZ_DIR)

# 导入wechat_mp_auth模块
try:
    # 先尝试直接导入
    from wechat_mp_auth import WeChatAuth, LoginError
except ImportError:
    try:
        # 再尝试相对导入（假设wechat_mp_auth是wz下的模块）
        import sys
        from pathlib import Path
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from wechat_mp_auth import WeChatAuth, LoginError
    except ImportError as e:
        print(f"警告: 未找到wechat_mp_auth模块，凭证更新功能可能无法正常工作: {e}")
        WeChatAuth = None
        LoginError = Exception

# 导入集成采集器
try:
    from core.integrated_crawler import IntegratedCrawler
    from core.database import UnifiedDatabaseManager, CrawlStatus
except ImportError as e:
    print(f"警告: 未找到集成采集器模块，内容采集功能可能无法正常工作: {e}")
    IntegratedCrawler = None
    UnifiedDatabaseManager = None
    CrawlStatus = None

# 导入论坛发布模块
try:
    from fabu.batch_publisher import BatchPublisher
    from fabu.forum_publisher import ForumPublisher
except ImportError as e:
    print(f"警告: 未找到论坛发布模块，论坛发布功能可能无法正常工作: {e}")
    BatchPublisher = None
    ForumPublisher = None

# 配置日志
log_dir = os.path.join(BASE_DIR, 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logger = logging.getLogger('wechat_crawler_web')
logger.setLevel(logging.INFO)
# 修复编码问题，确保Windows系统下中文正常显示
file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 添加控制台输出
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# 计划任务配置文件
config_dir = os.path.join(BASE_DIR, 'config')
os.makedirs(config_dir, exist_ok=True)
SCHEDULE_CONFIG_FILE = os.path.join(config_dir, 'schedule.conf')

# 初始化Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = 'wechat_crawler_web_secret_key'
app.config['JSON_AS_ASCII'] = False

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.add_jobstore(MemoryJobStore(), 'default')

def load_schedule_config():
    """加载计划任务配置"""
    if not os.path.exists(SCHEDULE_CONFIG_FILE):
        return []
    
    try:
        with open(SCHEDULE_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载计划任务配置失败: {e}")
        return []

def save_schedule_config(config):
    """保存计划任务配置"""
    try:
        with open(SCHEDULE_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存计划任务配置失败: {e}")
        return False

def run_crawler(account=None, limit=10):
    """
    运行文章抓取脚本
    
    Args:
        account: 指定抓取的公众号，None表示抓取所有配置的公众号
        limit: 每个公众号抓取的文章数量
    
    Returns:
        tuple: (成功标志, 结果消息, 文章列表, 额外信息)
    """
    logger.info("开始抓取文章")
    
    # 1. 准备命令
    crawler_script = os.path.join(WZ_DIR, 'crawl_wechat.py')
    cmd_list = [sys.executable, crawler_script]
    
    if account:
        cmd_list.extend(['--account', account])
    
    cmd_list.extend(['--limit', str(limit)])
    
    # 2. 执行子进程
    process_result = None
    try:
        logger.info(f"执行命令: {' '.join(cmd_list)}")
        process_result = subprocess.run(
            cmd_list, 
            capture_output=True, 
            text=True, 
            cwd=WZ_DIR, 
            encoding='utf-8'
        )
    except Exception as process_err:
        logger.error(f"执行子进程时发生异常: {process_err}", exc_info=True)
        return False, f"执行抓取脚本时发生错误: {str(process_err)}", [], {"error_type": "SUBPROCESS_ERROR"}
    
    # 3. 检查子进程对象是否有效
    if process_result is None:
        logger.critical("subprocess.run 返回了 None，这是异常情况！")
        return False, "执行抓取脚本时内部错误 (subprocess返回None)", [], {"error_type": "INTERNAL_ERROR"}
    
    # 4. 安全获取子进程输出
    try:
        exit_code = process_result.returncode
        output_text = "" if process_result.stdout is None else process_result.stdout
        error_text = "" if process_result.stderr is None else process_result.stderr
        
        # 记录子进程信息（简化版本）
        logger.info(f"子进程完成，退出码: {exit_code}")
        if output_text:
            logger.debug(f"子进程输出 (前500字符): {output_text[:500]}")
        if error_text:
            logger.debug(f"子进程错误 (前500字符): {error_text[:500]}")
    except Exception as extract_err:
        logger.error(f"提取子进程结果时发生异常: {extract_err}", exc_info=True)
        return False, "处理子进程结果时发生错误", [], {"error_type": "RESULT_PROCESSING_ERROR"}
    
    # 5. 基于退出码处理特定情况
    try:
        # 5.1 凭证失效情况
        credential_expired = False
        if exit_code == 2:
            credential_expired = True
        else:
            # 安全检查输出中是否包含特定标记
            try:
                if output_text and "CREDENTIALS_EXPIRED_FLAG" in output_text:
                    credential_expired = True
            except Exception as text_check_err:
                logger.error(f"检查输出文本时发生异常: {text_check_err}", exc_info=True)
        
        if credential_expired:
            logger.warning("检测到微信凭证已失效 (来自抓取脚本)。")
            return False, '微信凭证已失效，请点击"更新凭证"按钮重新扫码登录。', [], {"error_type": "CREDENTIALS_EXPIRED"}
        
        # 5.2 频率限制情况
        if exit_code == 3:
            logger.warning("抓取脚本报告请求频率过快。")
            error_details = error_text or output_text
            error_details_clean = "\n".join([
                line for line in error_details.splitlines() 
                if "CREDENTIALS_EXPIRED_FLAG" not in line
            ])
            return False, f'抓取请求过于频繁，请稍后再试。详情: {error_details_clean.strip()}', [], {"error_type": "RATE_LIMITED"}
        
        # 5.3 成功情况
        if exit_code == 0:
            return process_success_case(output_text, error_text)
        
        # 5.4 其他错误情况
        error_msg = error_text or output_text or "未知子进程错误"
        error_msg_clean = "\n".join([
            line for line in error_msg.splitlines() 
            if "CREDENTIALS_EXPIRED_FLAG" not in line
        ])
        logger.error(f"抓取脚本执行失败 (退出码: {exit_code}): {error_msg_clean.strip()}")
        return False, f'抓取失败: {error_msg_clean.strip()}', [], {"error_type": "CRAWLER_SCRIPT_FAILED", "exit_code": exit_code}
    
    except Exception as logic_err:
        logger.error(f"处理子进程结果逻辑时发生异常: {logic_err}", exc_info=True)
        return False, f"处理抓取结果时发生内部错误: {str(logic_err)}", [], {"error_type": "PROCESSING_ERROR"}

def process_success_case(output_text, error_text):
    """处理子进程成功执行的情况，解析文章数量和获取数据库结果"""
    try:
        logger.info("抓取脚本成功执行。")
        
        # 解析文章数量
        articles_count = 0
        for line in output_text.splitlines():
            if "共抓取到" in line and "篇文章" in line:
                try:
                    articles_count = int(line.split("共抓取到")[1].split("篇文章")[0].strip())
                    logger.info(f"从脚本输出解析到的文章数量: {articles_count}")
                    break
                except (ValueError, IndexError) as parse_err:
                    logger.warning(f"解析文章数量失败: {parse_err}. Line: '{line}'")
        
        # 从数据库获取文章明细 - 无论抓取脚本是否报告有新文章，都尝试获取最新的文章
        # 因为可能存在脚本成功入库但未在输出中正确报告的情况
        article_list = []
        try:
            from wzzq.db import DatabaseManager
            db = DatabaseManager()
            
            # 查询最近15分钟内入库的文章，或者至少返回最新的30条记录
            current_time = datetime.datetime.now()
            fifteen_minutes_ago = current_time - datetime.timedelta(minutes=15)
            
            # 先尝试查询最近15分钟内的文章
            recent_query = """
            SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time, 
                   a.account_name as author, a.fetched_at as update_time,
                   NULL as cover_url
            FROM wechat_articles a
            WHERE a.fetched_at >= %s
            ORDER BY a.fetched_at DESC
            """
            
            recent_results = db.query(recent_query, (fifteen_minutes_ago.strftime('%Y-%m-%d %H:%M:%S'),))
            
            # 如果最近15分钟内没有新文章，则获取最新的30篇
            if not recent_results or len(recent_results) == 0:
                logger.info("最近15分钟内没有新文章，获取最新的30篇文章")
                query_limit = max(30, articles_count) if articles_count > 0 else 30
                
                fallback_query = """
                SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time, 
                       a.account_name as author, a.fetched_at as update_time,
                       NULL as cover_url
                FROM wechat_articles a
                ORDER BY a.fetched_at DESC
                LIMIT %s
                """
                
                query_results = db.query(fallback_query, (query_limit,))
                if query_results is None:
                    logger.warning("数据库查询返回None，将使用空列表")
                    article_list = []
                else:
                    article_list = query_results
                    logger.info(f"从数据库查询到 {len(article_list)} 篇最新文章")
            else:
                # 使用最近15分钟内的文章
                article_list = recent_results
                logger.info(f"从数据库查询到 {len(article_list)} 篇最近15分钟内的新文章")
            
            # 处理日期时间字段
            for article in article_list:
                if isinstance(article.get('publish_time'), datetime.datetime):
                    article['publish_time'] = article['publish_time'].strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(article.get('update_time'), datetime.datetime):
                    article['update_time'] = article['update_time'].strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as db_err:
            logger.error(f"从数据库获取文章明细失败: {db_err}", exc_info=True)
            article_list = []
        
        # 生成结果消息
        if len(article_list) > 0:
            if articles_count > 0:
                result_msg = f"抓取成功，脚本报告获取{articles_count}篇文章，数据库返回{len(article_list)}篇明细。"
            else:
                result_msg = f"抓取成功，数据库返回{len(article_list)}篇最近的文章。"
        else:
            if articles_count > 0:
                result_msg = f"抓取成功，脚本报告获取{articles_count}篇文章，但无法从数据库获取明细。"
            else:
                result_msg = "抓取成功，但未获取到新文章。"
            
        logger.info(f"最终消息: {result_msg}")
        return True, result_msg, article_list, None
        
    except Exception as success_err:
        logger.error(f"处理成功案例时发生异常: {success_err}", exc_info=True)
        return True, "抓取似乎成功，但处理结果时出错", [], {"error_type": "RESULT_PARSING_ERROR"}

def update_credentials():
    """
    更新微信公众平台凭证
    
    Returns:
        tuple: (成功标志, 结果消息)
    """
    logger.info("开始更新凭证")
    
    if WeChatAuth is None:
        return False, "无法导入WeChatAuth模块，请确认wechat_mp_auth模块已正确安装"
    
    try:
        auth = WeChatAuth()
        auth.login()
        logger.info("凭证更新成功")
        return True, "凭证更新成功"
    except LoginError as le:
        error_msg = f"登录失败: {le}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"凭证更新过程中发生错误: {e}"
        logger.error(error_msg)
        return False, error_msg

def schedule_crawler_job(job_id, schedule_type, days, time, account=None, limit=10):
    """
    调度文章抓取任务
    
    Args:
        job_id: 任务ID
        schedule_type: 计划类型 (daily, weekly)
        days: 每周几执行 (0-6, 0=周一)
        time: 执行时间 (HH:MM)
        account: 指定抓取的公众号
        limit: 每个公众号抓取的文章数量
    
    Returns:
        bool: 是否成功调度
    """
    try:
        hour, minute = map(int, time.split(':'))
        
        if schedule_type == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
            description = f"每天 {time}"
        elif schedule_type == 'weekly':
            if isinstance(days, str):
                days = [int(d) for d in days.split(',')]
            
            dow = [d+1 for d in days]
            day_names = ['一', '二', '三', '四', '五', '六', '日']
            selected_days = [day_names[d] for d in days]
            
            trigger = CronTrigger(day_of_week=','.join(map(str, dow)), hour=hour, minute=minute)
            description = f"每周{','.join(selected_days)} {time}"
        else:
            return False
        
        def job_func():
            job_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"开始执行计划任务 {job_id}: {description}")
            
            success, message, articles, extra_info = run_crawler(account, limit)
            
            result_message = message
            if success and articles and len(articles) > 0:
                result_message += f"，最新文章可在查看文章页面查看"
            
            # 记录额外的错误信息（如果有）
            if extra_info and isinstance(extra_info, dict) and 'error_type' in extra_info:
                error_type = extra_info['error_type']
                logger.info(f"计划任务 {job_id} 返回的错误类型: {error_type}")
            
            logger.info(f"计划任务 {job_id} 执行完成: {result_message}")
            
            job_logs = load_job_logs()
            job_logs.append({
                'job_id': job_id,
                'start_time': job_start_time,
                'end_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': success,
                'message': result_message,
                'articles_count': len(articles) if success and articles else 0,
                'error_type': extra_info.get('error_type') if extra_info and isinstance(extra_info, dict) else None
            })
            save_job_logs(job_logs[-100:])
        
        scheduler.add_job(
            job_func, 
            trigger=trigger, 
            id=job_id,
            replace_existing=True,
            name=f"抓取任务 - {description}"
        )
        
        logger.info(f"已调度任务 {job_id}: {description}")
        return True
    
    except Exception as e:
        logger.error(f"调度任务失败: {e}")
        return False

def load_job_logs():
    """加载任务执行记录"""
    log_file = os.path.join(BASE_DIR, 'logs', 'job_logs.json')
    if not os.path.exists(log_file):
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载任务执行记录失败: {e}")
        return []

def save_job_logs(logs):
    """保存任务执行记录"""
    log_file = os.path.join(BASE_DIR, 'logs', 'job_logs.json')
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存任务执行记录失败: {e}")
        return False

def run_content_crawler(source_type=None, limit=50, batch_size=5):
    """
    运行内容采集器

    Args:
        source_type: 指定采集的来源类型 (wechat, linux_do, nodeseek, external)
        limit: 采集文章数量限制
        batch_size: 批次大小

    Returns:
        tuple: (成功标志, 结果消息, 统计信息)
    """
    logger.info(f"开始内容采集 - 来源类型: {source_type}, 限制: {limit}")

    if IntegratedCrawler is None:
        return False, "集成采集器模块未正确加载", {}

    try:
        with IntegratedCrawler() as crawler:
            # 执行批量采集
            result = crawler.batch_crawl(
                source_type=source_type,
                limit=limit,
                batch_size=batch_size
            )

            success = result.get('total_processed', 0) > 0 or result.get('successful', 0) > 0

            if success:
                message = f"内容采集完成 - 处理: {result.get('total_processed', 0)}, 成功: {result.get('successful', 0)}, 失败: {result.get('failed', 0)}"
            else:
                message = "没有找到待采集的文章或采集失败"

            logger.info(f"内容采集结果: {message}")
            return success, message, result

    except Exception as e:
        error_msg = f"内容采集过程中发生错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg, {}

def save_urls_to_database(urls, source_type='external', source_name='手动导入'):
    """将URL列表保存到wechat_articles表，仅入库不采集"""
    import mysql.connector
    from datetime import datetime
    import re

    # 数据库配置
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
        from config_manager import get_database_config

        db_config = get_database_config('wz_database')
    except Exception as e:
        logger.error(f"无法加载数据库配置: {e}")
        # 使用默认配置
        db_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'wz',
            'charset': 'utf8mb4'
        }

    def detect_source_type_from_url(url):
        """根据URL自动检测来源类型"""
        if 'linux.do' in url:
            return 'linux.do'
        elif 'nodeseek.com' in url:
            return 'nodeseek.com'
        elif 'mp.weixin.qq.com' in url:
            return 'wechat'
        else:
            return 'external'

    results = []

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for url in urls:
            try:
                # 检查URL是否已存在 - 在wechat_articles表中检查
                check_sql = "SELECT id FROM wechat_articles WHERE article_url = %s"
                cursor.execute(check_sql, (url,))
                existing = cursor.fetchone()

                if existing:
                    results.append({
                        'url': url,
                        'status': 'skipped',
                        'reason': '链接已存在'
                    })
                    continue

                # 自动检测来源类型
                detected_source_type = detect_source_type_from_url(url)

                # 根据来源类型决定account_name和site_name
                if detected_source_type == 'wechat':
                    account_name = source_name if source_name != '手动导入' else ''
                    site_name = 'wechat'
                else:
                    account_name = ''  # 非微信链接account_name留空
                    site_name = detected_source_type

                # 插入新记录到wechat_articles表
                insert_sql = """
                INSERT INTO wechat_articles
                (account_name, title, article_url, publish_timestamp, source_type, crawl_status, site_name, fetched_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(insert_sql, (
                    account_name,  # 微信链接使用source_name，其他留空
                    '',  # title留空，等采集时填入真实标题
                    url,
                    datetime.now(),  # 使用当前时间作为发布时间
                    detected_source_type,  # 使用检测到的来源类型
                    0,  # crawl_status = 0 表示待采集
                    site_name,  # 站点名称
                    datetime.now()
                ))

                results.append({
                    'url': url,
                    'status': 'success',
                    'article_id': cursor.lastrowid,
                    'detected_source': detected_source_type
                })

            except Exception as e:
                logger.error(f"保存URL失败: {url} - {e}")
                results.append({
                    'url': url,
                    'status': 'failed',
                    'error': str(e)
                })

        conn.commit()

    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        # 如果数据库连接失败，返回所有URL为失败状态
        results = [{'url': url, 'status': 'failed', 'error': str(e)} for url in urls]

    finally:
        if 'conn' in locals():
            conn.close()

    return results

def get_crawl_status():
    """
    获取采集状态统计

    Returns:
        dict: 采集状态统计信息
    """
    if UnifiedDatabaseManager is None:
        return {}

    try:
        with UnifiedDatabaseManager() as db:
            stats = db.get_crawl_statistics()
            return stats
    except Exception as e:
        logger.error(f"获取采集状态失败: {e}")
        return {}

def schedule_content_crawler_job(job_id, schedule_type, days, time, source_type=None, limit=50, batch_size=5):
    """
    调度内容采集任务

    Args:
        job_id: 任务ID
        schedule_type: 计划类型 (daily, weekly)
        days: 每周几执行 (0-6, 0=周一)
        time: 执行时间 (HH:MM)
        source_type: 来源类型
        limit: 采集数量限制
        batch_size: 批次大小

    Returns:
        bool: 是否成功调度
    """
    try:
        hour, minute = map(int, time.split(':'))

        if schedule_type == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
            description = f"每天 {time} 内容采集"
        elif schedule_type == 'weekly':
            if isinstance(days, str):
                days = [int(d) for d in days.split(',')]

            dow = [d+1 for d in days]
            day_names = ['一', '二', '三', '四', '五', '六', '日']
            selected_days = [day_names[d] for d in days]

            trigger = CronTrigger(day_of_week=','.join(map(str, dow)), hour=hour, minute=minute)
            description = f"每周{','.join(selected_days)} {time} 内容采集"
        else:
            return False

        def job_func():
            job_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"开始执行内容采集计划任务 {job_id}: {description}")

            success, message, stats = run_content_crawler(source_type, limit, batch_size)

            logger.info(f"内容采集计划任务 {job_id} 执行完成: {message}")

            job_logs = load_job_logs()
            job_logs.append({
                'job_id': job_id,
                'job_type': 'content_crawl',
                'start_time': job_start_time,
                'end_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': success,
                'message': message,
                'articles_count': stats.get('successful', 0),
                'source_type': source_type
            })
            save_job_logs(job_logs[-100:])

        scheduler.add_job(
            job_func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            name=f"内容采集任务 - {description}"
        )

        logger.info(f"已调度内容采集任务 {job_id}: {description}")
        return True

    except Exception as e:
        logger.error(f"调度内容采集任务失败: {e}")
        return False

@app.route('/')
def index():
    """首页"""
    schedules = load_schedule_config()
    job_logs = load_job_logs()[-10:]
    return render_template('index.html', schedules=schedules, job_logs=job_logs)

@app.route('/crawl', methods=['POST'])
def crawl():
    """立即抓取文章"""
    account_name = request.form.get('account_name')
    limit = request.form.get('limit', default=10, type=int)
    
    success, message, articles, extra_info = run_crawler(account_name, limit)
    
    response_data = {
        'success': success,
        'message': message,
        'articles': articles if articles else []
    }
    if extra_info and isinstance(extra_info, dict) and 'error_type' in extra_info:
        response_data['error_type'] = extra_info['error_type']
    
    return jsonify(response_data)

@app.route('/update_credentials', methods=['POST'])
def update_cred():
    """更新凭证"""
    success, message = update_credentials()
    return jsonify({'success': success, 'message': message})

@app.route('/crawl_urls', methods=['POST'])
def crawl_urls():
    """手动URL入库（仅保存链接，不立即采集）"""
    urls_text = request.form.get('urls', '').strip()
    source_type = request.form.get('source_type', 'external')
    source_name = request.form.get('source_name', '手动导入')

    if not urls_text:
        return jsonify({
            'success': False,
            'message': '请输入要采集的URL'
        })

    # 解析URL列表
    urls = []
    for line in urls_text.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            urls.append(line)

    if not urls:
        return jsonify({
            'success': False,
            'message': '没有找到有效的URL'
        })

    try:
        # 简化版：直接入库，不立即采集
        results = save_urls_to_database(urls, source_type, source_name)

        successful = len([r for r in results if r['status'] == 'success'])
        skipped = len([r for r in results if r['status'] == 'skipped'])
        failed = len([r for r in results if r['status'] == 'failed'])

        return jsonify({
            'success': True,
            'message': f'URL入库完成！成功: {successful}个, 跳过: {skipped}个, 失败: {failed}个',
            'results': results
        })

    except Exception as e:
        logger.error(f"URL入库失败: {e}")
        return jsonify({
            'success': False,
            'message': f'入库失败: {str(e)}'
        })

@app.route('/crawl_content', methods=['POST'])
def crawl_content():
    """触发内容采集"""
    source_type = request.form.get('source_type')
    limit = request.form.get('limit', default=50, type=int)
    batch_size = request.form.get('batch_size', default=5, type=int)

    success, message, stats = run_content_crawler(source_type, limit, batch_size)

    response_data = {
        'success': success,
        'message': message,
        'stats': stats
    }

    return jsonify(response_data)

@app.route('/api/crawl_status', methods=['GET'])
def api_crawl_status():
    """获取采集状态API"""
    stats = get_crawl_status()
    return jsonify({
        'success': True,
        'data': stats
    })

@app.route('/schedule_content', methods=['POST'])
def schedule_content():
    """设置定期内容采集任务"""
    schedule_type = request.form.get('schedule_type')
    days = request.form.getlist('days')
    time = request.form.get('time')
    source_type = request.form.get('source_type')
    limit = int(request.form.get('limit', 50))
    batch_size = int(request.form.get('batch_size', 5))

    if not schedule_type or not time:
        return jsonify({'success': False, 'message': '缺少必要参数'})

    if schedule_type == 'weekly' and not days:
        return jsonify({'success': False, 'message': '请选择每周执行的日期'})

    job_id = f"content_crawl_job_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

    success = schedule_content_crawler_job(job_id, schedule_type, days, time, source_type, limit, batch_size)

    if success:
        schedules = load_schedule_config()
        schedules.append({
            'id': job_id,
            'type': 'content_crawl',
            'schedule_type': schedule_type,
            'days': days,
            'time': time,
            'source_type': source_type,
            'limit': limit,
            'batch_size': batch_size,
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_schedule_config(schedules)

        return jsonify({'success': True, 'message': '定期内容采集任务已设置'})
    else:
        return jsonify({'success': False, 'message': '设置定期内容采集任务失败'})

@app.route('/schedule', methods=['POST'])
def schedule():
    """设置定期抓取任务"""
    schedule_type = request.form.get('schedule_type')
    days = request.form.getlist('days')
    time = request.form.get('time')
    account = request.form.get('account', None)
    limit = int(request.form.get('limit', 10))
    
    if not schedule_type or not time:
        return jsonify({'success': False, 'message': '缺少必要参数'})
    
    if schedule_type == 'weekly' and not days:
        return jsonify({'success': False, 'message': '请选择每周执行的日期'})
    
    job_id = f"crawl_job_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    success = schedule_crawler_job(job_id, schedule_type, days, time, account, limit)
    
    if success:
        schedules = load_schedule_config()
        schedules.append({
            'id': job_id,
            'type': schedule_type,
            'days': days,
            'time': time,
            'account': account,
            'limit': limit,
            'created_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        save_schedule_config(schedules)
        
        return jsonify({'success': True, 'message': '定期抓取任务已设置'})
    else:
        return jsonify({'success': False, 'message': '设置定期抓取任务失败'})

@app.route('/delete_schedule', methods=['POST'])
def delete_schedule():
    """删除定期抓取任务"""
    job_id = request.form.get('job_id')
    
    if not job_id:
        return jsonify({'success': False, 'message': '缺少任务ID'})
    
    try:
        scheduler.remove_job(job_id)
    except Exception as e:
        logger.error(f"从调度器中移除任务失败: {e}")
    
    schedules = load_schedule_config()
    schedules = [s for s in schedules if s.get('id') != job_id]
    save_schedule_config(schedules)
    
    return jsonify({'success': True, 'message': '已删除定期抓取任务'})

@app.route('/logs')
def view_logs():
    """查看任务执行记录"""
    job_logs = load_job_logs()
    return render_template('logs.html', logs=job_logs)

@app.route('/articles')
def view_articles():
    """查看最新抓取的文章"""
    try:
        from wzzq.db import DatabaseManager
        db = DatabaseManager()

        limit = request.args.get('limit', 100, type=int)

        account = request.args.get('account', None)

        if account:
            query = """
            SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time,
                   a.account_name as author, a.fetched_at as update_time,
                   a.forum_published, NULL as cover_url
            FROM wechat_articles a
            WHERE a.account_name = %s
            ORDER BY a.publish_timestamp DESC
            LIMIT %s
            """
            articles = db.query(query, (account, limit))
        else:
            query = """
            SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time,
                   a.account_name as author, a.fetched_at as update_time,
                   a.forum_published, NULL as cover_url
            FROM wechat_articles a
            ORDER BY a.publish_timestamp DESC
            LIMIT %s
            """
            articles = db.query(query, (limit,))

        for article in articles:
            if isinstance(article['publish_time'], datetime.datetime):
                article['publish_time'] = article['publish_time'].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(article['update_time'], datetime.datetime):
                article['update_time'] = article['update_time'].strftime("%Y-%m-%d %H:%M:%S")

        return render_template('articles.html', articles=articles, account=account)

    except Exception as e:
        logger.error(f"获取文章列表失败: {e}")
        return render_template('error.html', error_message=f"获取文章列表失败: {e}")

@app.route('/forum_publish_status', methods=['GET'])
def forum_publish_status():
    """获取论坛发布状态"""
    if ForumPublisher is None:
        return jsonify({
            'success': False,
            'message': '论坛发布模块未加载'
        })

    try:
        publisher = ForumPublisher()
        pending_articles = publisher.get_pending_articles()

        return jsonify({
            'success': True,
            'pending_count': len(pending_articles),
            'pending_articles': [
                {
                    'id': article['id'],
                    'title': article['title'],
                    'account_name': article['account_name']
                }
                for article in pending_articles[:10]
            ]
        })

    except Exception as e:
        logger.error(f"获取论坛发布状态失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        })

@app.route('/batch_publish_forum', methods=['POST'])
def batch_publish_forum():
    """批量发布文章到论坛"""
    if BatchPublisher is None:
        return jsonify({
            'success': False,
            'message': '论坛发布模块未加载'
        })

    try:
        batch_publisher = BatchPublisher()

        # 执行批量发布
        result = batch_publisher.publish_all()

        return jsonify({
            'success': True,
            'message': f'批量发布完成: 总计{result["total"]}篇, 成功{result["success"]}篇, 失败{result["failed"]}篇',
            'total': result['total'],
            'success_count': result['success'],
            'failed_count': result['failed'],
            'details': result['details']
        })

    except Exception as e:
        logger.error(f"批量发布失败: {e}")
        return jsonify({
            'success': False,
            'message': f'批量发布失败: {str(e)}'
        })

def init_scheduler():
    """初始化调度器并加载所有计划任务"""
    schedules = load_schedule_config()
    active_jobs = {job.id: job for job in scheduler.get_jobs()}

    for config in schedules:
        job_id = config.get('id')
        if job_id in active_jobs:
            logger.info(f"任务 {job_id} 已在调度中，跳过重复添加。")
            continue

        task_type = config.get('type', 'link_crawl')  # 默认为链接抓取任务
        schedule_type = config.get('schedule_type')
        days = config.get('days')
        time_str = config.get('time') # 使用 time_str 避免与 time 模块冲突

        if not all([job_id, schedule_type, time_str]):
            logger.warning(f"跳过无效的计划任务配置（缺少id, type或time）: {config}")
            continue

        try:
            if task_type == 'content_crawl':
                # 内容采集任务
                source_type = config.get('source_type')
                limit = config.get('limit', 50)
                batch_size = config.get('batch_size', 5)
                schedule_content_crawler_job(job_id, schedule_type, days, time_str, source_type, limit, batch_size)
            else:
                # 链接抓取任务（默认）
                account = config.get('account')
                limit = config.get('limit', 10)
                schedule_crawler_job(job_id, schedule_type, days, time_str, account, limit)
        except Exception as e:
            logger.error(f"添加计划任务 {job_id} 到调度器时失败: {e}", exc_info=True)

    # 不在此处启动调度器
    if not scheduler.running:
        logger.info("调度器已配置作业，等待从主启动脚本启动。")
    else:
        logger.info("调度器已在运行中 (可能由重载器或其他方式启动)。")

# 在模块末尾调用以配置作业，但不启动调度器
init_scheduler()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 