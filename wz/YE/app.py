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
        tuple: (成功标志, 结果消息, 文章列表)
    """
    logger.info("开始抓取文章")
    
    crawler_script = os.path.join(WZ_DIR, 'crawl_wechat.py')
    cmd = [sys.executable, crawler_script]
    
    if account:
        cmd.extend(['--account', account])
    
    cmd.extend(['--limit', str(limit)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=WZ_DIR)
        
        if result.returncode == 0:
            output = result.stdout
            # 尝试从输出中提取抓取到的文章数量
            articles_count = 0
            for line in output.splitlines():
                if "共抓取到" in line and "篇文章" in line:
                    try:
                        articles_count = int(line.split("共抓取到")[1].split("篇文章")[0].strip())
                    except (ValueError, IndexError):
                        pass
                    break
            
            # 获取最近抓取的文章明细
            articles = []
            try:
                # 尝试从数据库获取最近抓取的文章明细
                from wzzq.db import DatabaseManager
                db = DatabaseManager()
                
                # 查询最近抓取的文章
                query = """
                SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time, 
                       a.account_name as author, a.fetched_at as update_time,
                       NULL as cover_url
                FROM wechat_articles a
                ORDER BY a.fetched_at DESC
                LIMIT %s
                """
                articles = db.query(query, (max(30, articles_count),))
                
                # 格式化日期时间
                for article in articles:
                    if isinstance(article['publish_time'], datetime.datetime):
                        article['publish_time'] = article['publish_time'].strftime("%Y-%m-%d %H:%M:%S")
                    if isinstance(article['update_time'], datetime.datetime):
                        article['update_time'] = article['update_time'].strftime("%Y-%m-%d %H:%M:%S")
                
            except Exception as e:
                logger.error(f"获取文章明细失败: {e}")
            
            if articles_count > 0:
                message = f"抓取成功，共获取{articles_count}篇文章"
            else:
                message = "抓取成功，但未获取到新文章"
                
            logger.info(message)
            return True, message, articles
        else:
            error_msg = result.stderr or "未知错误"
            logger.error(f"抓取失败: {error_msg}")
            return False, f"抓取失败: {error_msg}", []
    
    except Exception as e:
        logger.error(f"执行抓取脚本时发生异常: {e}")
        return False, f"执行抓取脚本时发生异常: {e}", []

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
        # 解析时间
        hour, minute = map(int, time.split(':'))
        
        # 创建触发器
        if schedule_type == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
            description = f"每天 {time}"
        elif schedule_type == 'weekly':
            # 转换days为数字列表
            if isinstance(days, str):
                days = [int(d) for d in days.split(',')]
            
            # 将0-6（周一到周日）转换为1-7（APScheduler的day_of_week格式）
            dow = [d+1 for d in days]
            day_names = ['一', '二', '三', '四', '五', '六', '日']
            selected_days = [day_names[d] for d in days]
            
            trigger = CronTrigger(day_of_week=','.join(map(str, dow)), hour=hour, minute=minute)
            description = f"每周{','.join(selected_days)} {time}"
        else:
            return False
        
        # 创建任务函数（带参数的闭包）
        def job_func():
            job_start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"开始执行计划任务 {job_id}: {description}")
            
            # 执行爬虫
            success, message, articles = run_crawler(account, limit)
            
            # 生成任务结果信息
            result_message = message
            if success and len(articles) > 0:
                result_message += f"，最新文章可在查看文章页面查看"
            
            logger.info(f"计划任务 {job_id} 执行完成: {result_message}")
            
            # 记录任务执行记录
            job_logs = load_job_logs()
            job_logs.append({
                'job_id': job_id,
                'start_time': job_start_time,
                'end_time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'success': success,
                'message': result_message,
                'articles_count': len(articles) if success else 0
            })
            save_job_logs(job_logs[-100:])  # 只保留最近100条记录
        
        # 添加任务到调度器
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

@app.route('/')
def index():
    """首页"""
    schedules = load_schedule_config()
    job_logs = load_job_logs()[-10:]  # 最近10条记录
    return render_template('index.html', schedules=schedules, job_logs=job_logs)

@app.route('/crawl', methods=['POST'])
def crawl():
    """立即抓取文章"""
    account = request.form.get('account', None)
    limit = int(request.form.get('limit', 10))
    
    success, message, articles = run_crawler(account, limit)
    
    if success and len(articles) > 0:
        # 如果成功抓取且有文章，添加查看链接
        message += f"，<a href='{url_for('view_articles')}'>点击查看最新文章</a>"
    
    return jsonify({'success': success, 'message': message})

@app.route('/update_credentials', methods=['POST'])
def update_cred():
    """更新凭证"""
    success, message = update_credentials()
    return jsonify({'success': success, 'message': message})

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
    
    # 如果是每周模式，但未选择任何日期
    if schedule_type == 'weekly' and not days:
        return jsonify({'success': False, 'message': '请选择每周执行的日期'})
    
    # 生成任务ID
    job_id = f"crawl_job_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 添加到调度器
    success = schedule_crawler_job(job_id, schedule_type, days, time, account, limit)
    
    if success:
        # 保存到配置文件
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
    
    # 从调度器中移除
    try:
        scheduler.remove_job(job_id)
    except Exception as e:
        logger.error(f"从调度器中移除任务失败: {e}")
    
    # 从配置文件中移除
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
        # 从数据库获取最新抓取的文章
        from wzzq.db import DatabaseManager
        db = DatabaseManager()
        
        # 默认显示最近100篇文章
        limit = request.args.get('limit', 100, type=int)
        
        # 可选按公众号筛选
        account = request.args.get('account', None)
        
        if account:
            query = """
            SELECT a.id, a.title, a.article_url as link, a.publish_timestamp as publish_time, 
                   a.account_name as author, a.fetched_at as update_time,
                   NULL as cover_url
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
                   NULL as cover_url
            FROM wechat_articles a
            ORDER BY a.publish_timestamp DESC
            LIMIT %s
            """
            articles = db.query(query, (limit,))
        
        # 格式化日期时间
        for article in articles:
            if isinstance(article['publish_time'], datetime.datetime):
                article['publish_time'] = article['publish_time'].strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(article['update_time'], datetime.datetime):
                article['update_time'] = article['update_time'].strftime("%Y-%m-%d %H:%M:%S")
        
        return render_template('articles.html', articles=articles, account=account)
    
    except Exception as e:
        logger.error(f"获取文章列表失败: {e}")
        return render_template('error.html', error_message=f"获取文章列表失败: {e}")

def init_scheduler():
    """初始化调度器，加载已保存的任务"""
    schedules = load_schedule_config()
    
    for schedule in schedules:
        job_id = schedule.get('id')
        schedule_type = schedule.get('type')
        days = schedule.get('days')
        time = schedule.get('time')
        account = schedule.get('account')
        limit = schedule.get('limit', 10)
        
        schedule_crawler_job(job_id, schedule_type, days, time, account, limit)
    
    # 启动调度器
    scheduler.start()
    logger.info("调度器已启动")

# 初始化调度器
init_scheduler()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 