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
    
    def __init__(self, host=None, port=None, user=None, password=None,
                 database=None, charset=None):
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
        # 如果没有提供参数，从配置文件加载
        if host is None:
            try:
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
                from config_manager import get_database_config

                db_config = get_database_config('wz_database')
                self.config = db_config.copy()
            except Exception as e:
                # 配置加载失败时的默认配置
                self.config = {
                    'host': 'localhost',
                    'port': 3306,
                    'user': 'root',
                    'password': '',
                    'database': 'wz',
                    'charset': 'utf8mb4'
                }
                print(f"警告: 无法加载数据库配置，使用默认配置: {e}")
        else:
            # 使用提供的参数
            self.config = {
                'host': host,
                'port': port,
                'user': user,
                'password': password,
                'database': database,
                'charset': charset or 'utf8mb4',
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
            print(f"正在连接数据库: {self.config['host']}:{self.config['port']}/{self.config['database']}, 用户: {self.config['user']}")
            self.conn = mysql.connector.connect(**self.config)
            
            if not USING_PYMYSQL:
                self.cursor = self.conn.cursor(dictionary=True)
            else:
                self.cursor = self.conn.cursor()
                
            print(f"数据库连接成功")
            
            # 确保wechat_articles表存在
            self._ensure_table_exists()
            
            return True
        except Error as e:
            print(f"数据库连接失败: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            return False
            
    def _ensure_table_exists(self):
        """确保wechat_articles表存在，如果不存在则创建"""
        try:
            # 检查表是否存在
            check_table_sql = "SHOW TABLES LIKE 'wechat_articles'"
            self.cursor.execute(check_table_sql)
            table_exists = self.cursor.fetchone()
            
            if not table_exists:
                print("表wechat_articles不存在，正在创建...")
                # 创建表
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS `wechat_articles` (
                  `id` int(11) NOT NULL AUTO_INCREMENT,
                  `account_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '公众号名称',
                  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文章标题',
                  `article_url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文章链接',
                  `publish_timestamp` datetime NOT NULL COMMENT '文章发布时间',
                  `source_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'wechat' COMMENT '来源类型: wechat, external_link等',
                  `fetched_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取入库时间',
                  PRIMARY KEY (`id`),
                  KEY `idx_account_url` (`account_name`,`article_url`(255))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聚合的微信文章表';
                """
                self.cursor.execute(create_table_sql)
                print("表wechat_articles创建成功")
            else:
                print("表wechat_articles已存在，确认字段结构...")
                # 检查必要字段是否存在
                check_columns_sql = """
                SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'wechat_articles'
                """
                self.cursor.execute(check_columns_sql, (self.config['database'],))
                columns = [row['COLUMN_NAME'] if isinstance(row, dict) else row[0] for row in self.cursor.fetchall()]
                
                required_columns = ['account_name', 'title', 'article_url', 'publish_timestamp']
                missing_columns = [col for col in required_columns if col not in columns]
                
                if missing_columns:
                    print(f"警告: 表wechat_articles缺少必要字段: {', '.join(missing_columns)}")
                else:
                    print("表wechat_articles结构正常")
        except Error as e:
            print(f"检查/创建表时出错: {e}")
            print("继续使用现有表结构...")
            
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
        
    def query(self, sql, params=None):
        """
        执行SQL查询并返回结果
        
        Args:
            sql: SQL查询语句
            params: 查询参数(元组或列表)
            
        Returns:
            list: 查询结果的列表
        """
        try:
            if not self.conn or not self.cursor:
                self.connect()
                
            self.cursor.execute(sql, params)
            results = self.cursor.fetchall()
            return results
        except Error as e:
            print(f"查询执行失败: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            return []
            
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
        
        if not articles:
            print("没有文章需要保存")
            return 0
        
        print(f"准备批量保存 {len(articles)} 篇文章到数据库")
        
        try:
            # 准备批量插入的SQL和参数
            insert_sql = """
            INSERT INTO wechat_articles 
            (account_name, title, article_url, publish_timestamp, source_type) 
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            title = VALUES(title),
            fetched_at = CURRENT_TIMESTAMP
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
                        formatted_timestamp = datetime.datetime.strptime(str(publish_timestamp), "%Y-%m-%d %H:%M")
                    except (ValueError, TypeError):
                        # 如果转换失败，使用当前时间
                        formatted_timestamp = datetime.datetime.now()
                        print(f"警告: 无法解析发布时间 '{publish_timestamp}'，使用当前时间")
                
                values.append((
                    article.get('account_name'),
                    article.get('title'),
                    article.get('article_url'),
                    formatted_timestamp,
                    'wechat'  # 默认来源类型
                ))
            
            # 批量插入
            print(f"执行批量插入，共 {len(values)} 条记录")
            self.cursor.executemany(insert_sql, values)
            success_count = self.cursor.rowcount
            
            if not self.config.get('autocommit', False):
                self.conn.commit()
            
            print(f"批量保存完成，成功保存 {success_count} 篇文章")
            return success_count
            
        except Error as e:
            print(f"批量保存文章失败: {e}")
            # 打印更详细的错误信息
            import traceback
            traceback.print_exc()
            
            if not self.config.get('autocommit', False):
                self.conn.rollback()
            
            # 尝试逐个保存，绕过可能有问题的记录
            if len(articles) > 1:
                print("尝试逐个保存文章...")
                for article in articles:
                    try:
                        result = self.save_article(
                            article.get('account_name'),
                            article.get('title'),
                            article.get('article_url'),
                            article.get('publish_timestamp')
                        )
                        if result:
                            success_count += 1
                    except Exception as e2:
                        print(f"保存单篇文章失败: {e2}")
                print(f"逐个保存完成，成功保存 {success_count} 篇文章")
            
            return success_count