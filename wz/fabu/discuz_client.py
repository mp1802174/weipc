#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discuz数据库客户端
负责与Discuz X3.5数据库的安全交互
"""

import mysql.connector
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# 添加config目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from config_manager import get_database_config, get_forum_config

logger = logging.getLogger(__name__)

class DiscuzClient:
    """Discuz数据库客户端"""
    
    def __init__(self):
        """初始化Discuz客户端"""
        try:
            self.config = get_database_config('discuz_database')
            self.forum_config = get_forum_config()
        except Exception as e:
            logger.warning(f"无法加载配置文件，使用默认配置: {e}")
            # 使用默认配置作为备用
            self.config = {
                'host': '140.238.201.162',
                'port': 3306,
                'user': '00077',
                'password': '760516',
                'database': '00077',
                'charset': 'utf8mb4'
            }
            self.forum_config = {
                'target_forum_id': 2,
                'publisher_user_id': 4,
                'publisher_username': '砂鱼'
            }
        self.connection = None
    
    def connect(self) -> bool:
        """连接数据库"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Discuz数据库连接成功")
            return True
        except Exception as e:
            logger.error(f"Discuz数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Discuz数据库连接已关闭")
    
    def get_next_ids(self) -> Tuple[int, int]:
        """获取下一个可用的TID和PID"""
        cursor = self.connection.cursor()
        
        # 获取最大TID
        cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
        max_tid = cursor.fetchone()[0] or 0
        next_tid = max_tid + 1
        
        # 获取最大PID
        cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
        max_pid = cursor.fetchone()[0] or 0
        next_pid = max_pid + 1
        
        cursor.close()
        return next_tid, next_pid
    
    def get_forum_info(self, fid: int) -> Optional[Dict]:
        """获取版块信息"""
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute("SELECT fid, name, threads, posts FROM pre_forum_forum WHERE fid = %s", (fid,))
        result = cursor.fetchone()
        cursor.close()
        return result
    
    def get_user_info(self, uid: int) -> Optional[Dict]:
        """获取用户信息"""
        cursor = self.connection.cursor(dictionary=True)
        
        # 从member表获取基本信息
        cursor.execute("SELECT uid, username FROM pre_common_member WHERE uid = %s", (uid,))
        user_info = cursor.fetchone()
        
        if user_info:
            # 从member_count表获取统计信息
            cursor.execute("SELECT posts, threads FROM pre_common_member_count WHERE uid = %s", (uid,))
            count_info = cursor.fetchone()
            if count_info:
                user_info.update(count_info)
        
        cursor.close()
        return user_info
    
    def publish_article(self, article_data: Dict) -> bool:
        """
        发布单篇文章到论坛
        
        Args:
            article_data: 文章数据，包含title, content, author, authorid等
            
        Returns:
            bool: 是否发布成功
        """
        try:
            # 开始事务
            self.connection.start_transaction()
            
            # 获取新的ID
            next_tid, next_pid = self.get_next_ids()
            current_time = int(time.time())
            
            # 准备数据
            fid = article_data.get('fid', 2)  # 默认版块ID=2
            author = article_data.get('author', '砂鱼')
            authorid = article_data.get('authorid', 4)
            subject = article_data['title']
            content = article_data['content']
            
            cursor = self.connection.cursor()
            
            # 1. 插入主题记录
            thread_sql = """
            INSERT INTO pre_forum_thread (
                tid, fid, author, authorid, subject, dateline, lastpost, lastposter,
                views, replies, displayorder, digest, special, attachment, moderated,
                closed, stickreply, recommends, recommend_add, recommend_sub, heats,
                status, isgroup, favtimes, sharetimes, stamp, icon, pushedaid, cover,
                replycredit, relatebytag, maxposition, bgcolor, comments, hidden
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                0, 0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, 0, 0,
                0, 0, 0, 0, -1, -1, 0, 0,
                0, '', 1, '', 0, 0
            )
            """
            
            cursor.execute(thread_sql, (
                next_tid, fid, author, authorid, subject, current_time, current_time, author
            ))
            
            # 2. 插入帖子记录
            post_sql = """
            INSERT INTO pre_forum_post (
                pid, fid, tid, repid, first, author, authorid, subject, dateline,
                lastupdate, updateuid, premsg, message, useip, port, invisible,
                anonymous, usesig, htmlon, bbcodeoff, smileyoff, parseurloff,
                attachment, rate, ratetimes, status, tags, comment, replycredit, position
            ) VALUES (
                %s, %s, %s, 0, 1, %s, %s, %s, %s,
                0, 0, '', %s, '', 0, 0,
                0, 1, 0, 0, 0, 0,
                0, 0, 0, 0, '', 0, 0, 1
            )
            """

            cursor.execute(post_sql, (
                next_pid, fid, next_tid, author, authorid, subject, current_time, content
            ))
            
            # 3. 更新版块统计
            cursor.execute("""
                UPDATE pre_forum_forum 
                SET threads = threads + 1, posts = posts + 1,
                    lastpost = %s
                WHERE fid = %s
            """, (f"{next_tid}\t{subject}\t{current_time}\t{author}", fid))
            
            # 4. 更新用户统计
            cursor.execute("""
                UPDATE pre_common_member_count 
                SET posts = posts + 1, threads = threads + 1
                WHERE uid = %s
            """, (authorid,))
            
            # 提交事务
            self.connection.commit()
            cursor.close()
            
            logger.info(f"文章发布成功: TID={next_tid}, PID={next_pid}, 标题={subject}")
            return True
            
        except Exception as e:
            # 回滚事务
            self.connection.rollback()
            logger.error(f"文章发布失败: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
