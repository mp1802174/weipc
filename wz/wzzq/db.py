#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
数据库操作模块
处理与MySQL数据库的连接和数据存储
"""

# 尝试导入mysql-connector-python或PyMySQL
try:
    import mysql.connector
    from mysql.connector import Error
    USING_PYMYSQL = False
except ImportError:
    # 如果mysql-connector-python不可用，尝试导入PyMySQL
    try:
        import pymysql as mysql
        from pymysql import Error
        mysql.connector = mysql  # 兼容性处理
        USING_PYMYSQL = True
    except ImportError:
        raise ImportError("请安装MySQL连接器库：pip install mysql-connector-python==8.0.32 或 pip install PyMySQL")

import datetime


class DatabaseManager:
    """MySQL数据库管理类，用于连接数据库并执行查询"""
    
    def __init__(self, host="140.238.201.162", port=3306, user="cj", password="760516",
                 database="cj", charset="utf8mb4"):
        """
        初始化数据库连接
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            user: 数据库用户名
            password: 数据库密码
            database: 数据库名
            charset: 字符集
        """
        self.config = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
            'charset': charset,
        }
        
        # 根据实际使用的库添加特定配置
        if USING_PYMYSQL:
            self.config.update({
                'cursorclass': mysql.cursors.DictCursor,
                'autocommit': True
            })
        else:
            self.config.update({
                'use_unicode': True,
                'raise_on_warnings': True,
                'autocommit': True
            })
            
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """
        建立数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.conn = mysql.connector.connect(**self.config)
            
            if not USING_PYMYSQL:
                self.cursor = self.conn.cursor(dictionary=True)
            else:
                self.cursor = self.conn.cursor()
                
            return True
        except Error as e:
            print(f"数据库连接失败: {e}")
            return False
            
    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
        
    def save_article(self, account_name, title, article_url, publish_timestamp):
        """
        保存文章到数据库
        
        Args:
            account_name: 公众号名称
            title: 文章标题
            article_url: 文章链接
            publish_timestamp: 发布时间的datetime对象
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 检查文章是否已存在
            check_sql = """
            SELECT id FROM wechat_articles 
            WHERE account_name = %s AND article_url = %s
            """
            self.cursor.execute(check_sql, (account_name, article_url))
            exists = self.cursor.fetchone()
            
            if exists:
                # 文章已存在，可以选择更新或忽略
                return True
                
            # 插入新文章
            insert_sql = """
            INSERT INTO wechat_articles 
            (account_name, title, article_url, publish_timestamp, source_type) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            # 处理timestamp，确保是datetime格式
            if isinstance(publish_timestamp, datetime.datetime):
                formatted_timestamp = publish_timestamp
            else:
                try:
                    # 尝试转换字符串为datetime
                    formatted_timestamp = datetime.datetime.strptime(publish_timestamp, "%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    # 如果转换失败，使用当前时间
                    formatted_timestamp = datetime.datetime.now()
                    
            self.cursor.execute(insert_sql, (
                account_name, 
                title, 
                article_url, 
                formatted_timestamp,
                'wechat'  # 默认来源类型
            ))
            
            if not self.config.get('autocommit', False):
                self.conn.commit()
            
            return True
            
        except Error as e:
            print(f"保存文章失败: {e}")
            if not self.config.get('autocommit', False):
                self.conn.rollback()
            return False
            
    def save_articles_batch(self, articles):
        """
        批量保存文章到数据库
        
        Args:
            articles: 包含文章信息的列表，每篇文章是一个字典，包含account_name, title, article_url, publish_timestamp
            
        Returns:
            int: 成功保存的文章数量
        """
        success_count = 0
        
        try:
            # 准备批量插入的SQL和参数
            insert_sql = """
            INSERT INTO wechat_articles 
            (account_name, title, article_url, publish_timestamp, source_type) 
            VALUES (%s, %s, %s, %s, %s)
            """
            
            values = []
            for article in articles:
                # 处理timestamp，确保是datetime格式
                publish_timestamp = article.get('publish_timestamp')
                if isinstance(publish_timestamp, datetime.datetime):
                    formatted_timestamp = publish_timestamp
                else:
                    try:
                        # 尝试转换字符串为datetime
                        formatted_timestamp = datetime.datetime.strptime(publish_timestamp, "%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        # 如果转换失败，使用当前时间
                        formatted_timestamp = datetime.datetime.now()
                
                values.append((
                    article.get('account_name'),
                    article.get('title'),
                    article.get('article_url'),
                    formatted_timestamp,
                    'wechat'  # 默认来源类型
                ))
            
            # 批量插入
            self.cursor.executemany(insert_sql, values)
            success_count = self.cursor.rowcount
            
            if not self.config.get('autocommit', False):
                self.conn.commit()
            
            return success_count
            
        except Error as e:
            print(f"批量保存文章失败: {e}")
            if not self.config.get('autocommit', False):
                self.conn.rollback()
            return success_count