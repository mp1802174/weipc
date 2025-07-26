#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WZ项目数据库迁移脚本
从现有wechat_articles表迁移到新的统一表结构
"""

import os
import sys
import json
import logging
import datetime
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from wzzq.db import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """数据库迁移管理器"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.migration_log = []
        
    def log_step(self, step, message, success=True):
        """记录迁移步骤"""
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'step': step,
            'message': message,
            'success': success
        }
        self.migration_log.append(log_entry)
        
        if success:
            logger.info(f"[{step}] {message}")
        else:
            logger.error(f"[{step}] {message}")
    
    def check_prerequisites(self):
        """检查迁移前提条件"""
        logger.info("=== 检查迁移前提条件 ===")
        
        try:
            # 检查数据库连接
            if not self.db.connect():
                raise Exception("无法连接到数据库")
            self.log_step("PREREQ", "数据库连接成功")
            
            # 检查原表是否存在
            result = self.db.query("SHOW TABLES LIKE 'wechat_articles'")
            if not result:
                raise Exception("原表wechat_articles不存在")
            self.log_step("PREREQ", "原表wechat_articles存在")
            
            # 统计原表数据
            result = self.db.query("SELECT COUNT(*) as count FROM wechat_articles")
            original_count = result[0]['count'] if result else 0
            self.log_step("PREREQ", f"原表包含{original_count}条记录")
            
            # 检查新表是否已存在
            result = self.db.query("SHOW TABLES LIKE 'articles'")
            if result:
                logger.warning("新表articles已存在，将进行增量迁移")
                self.log_step("PREREQ", "新表articles已存在", success=False)
            
            return True
            
        except Exception as e:
            self.log_step("PREREQ", f"前提条件检查失败: {e}", success=False)
            return False
    
    def backup_original_data(self):
        """备份原始数据"""
        logger.info("=== 备份原始数据 ===")
        
        try:
            backup_table = f"wechat_articles_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_sql = f"""
            CREATE TABLE `{backup_table}` AS 
            SELECT * FROM `wechat_articles`
            """
            
            self.db.cursor.execute(backup_sql)
            self.log_step("BACKUP", f"创建备份表: {backup_table}")
            
            # 验证备份
            result = self.db.query(f"SELECT COUNT(*) as count FROM `{backup_table}`")
            backup_count = result[0]['count'] if result else 0
            self.log_step("BACKUP", f"备份表包含{backup_count}条记录")
            
            return backup_table
            
        except Exception as e:
            self.log_step("BACKUP", f"备份失败: {e}", success=False)
            return None
    
    def create_new_schema(self):
        """创建新的表结构"""
        logger.info("=== 创建新表结构 ===")
        
        try:
            # 读取SQL文件
            sql_file = project_root / "sql" / "001_unified_database_schema.sql"
            
            if not sql_file.exists():
                raise Exception(f"SQL文件不存在: {sql_file}")
            
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句
            sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for i, statement in enumerate(sql_statements):
                if statement.upper().startswith(('CREATE TABLE', 'CREATE VIEW')):
                    try:
                        self.db.cursor.execute(statement)
                        table_name = self._extract_table_name(statement)
                        self.log_step("SCHEMA", f"创建表/视图: {table_name}")
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            self.log_step("SCHEMA", f"表/视图已存在，跳过: {statement[:50]}...")
                        else:
                            raise e
            
            return True
            
        except Exception as e:
            self.log_step("SCHEMA", f"创建表结构失败: {e}", success=False)
            return False
    
    def migrate_data(self):
        """迁移数据"""
        logger.info("=== 迁移数据 ===")
        
        try:
            # 检查是否已有数据
            result = self.db.query("SELECT COUNT(*) as count FROM articles WHERE source_type = 'wechat'")
            existing_count = result[0]['count'] if result else 0
            
            if existing_count > 0:
                logger.warning(f"新表中已有{existing_count}条微信文章记录")
                response = input("是否继续增量迁移？(y/N): ")
                if response.lower() != 'y':
                    self.log_step("MIGRATE", "用户取消迁移")
                    return False
            
            # 执行数据迁移
            migration_sql = """
            INSERT IGNORE INTO `articles` (
                `source_type`,
                `source_name`, 
                `title`,
                `article_url`,
                `publish_timestamp`,
                `crawl_status`,
                `content`,
                `content_html`,
                `word_count`,
                `images`,
                `crawl_error`,
                `crawled_at`,
                `fetched_at`,
                `created_at`
            )
            SELECT 
                'wechat' as source_type,
                `account_name` as source_name,
                `title`,
                `article_url`,
                `publish_timestamp`,
                CASE 
                    WHEN `crawl_status` = 1 THEN 'completed'
                    WHEN `crawl_status` = 2 THEN 'failed'
                    ELSE 'pending'
                END as crawl_status,
                `content`,
                `content` as content_html,
                COALESCE(`word_count`, 0) as word_count,
                `images`,
                `error_message` as crawl_error,
                `crawled_at`,
                `fetched_at`,
                `fetched_at` as created_at
            FROM `wechat_articles`
            WHERE `article_url` IS NOT NULL 
              AND `article_url` != ''
              AND `title` IS NOT NULL 
              AND `title` != ''
            """
            
            self.db.cursor.execute(migration_sql)
            migrated_count = self.db.cursor.rowcount
            self.log_step("MIGRATE", f"迁移了{migrated_count}条记录")
            
            # 验证迁移结果
            result = self.db.query("SELECT COUNT(*) as count FROM articles WHERE source_type = 'wechat'")
            total_count = result[0]['count'] if result else 0
            self.log_step("MIGRATE", f"新表中现有{total_count}条微信文章记录")
            
            return True
            
        except Exception as e:
            self.log_step("MIGRATE", f"数据迁移失败: {e}", success=False)
            return False
    
    def validate_migration(self):
        """验证迁移结果"""
        logger.info("=== 验证迁移结果 ===")
        
        try:
            # 统计原表数据
            result = self.db.query("SELECT COUNT(*) as count FROM wechat_articles")
            original_count = result[0]['count'] if result else 0
            
            # 统计新表数据
            result = self.db.query("SELECT COUNT(*) as count FROM articles WHERE source_type = 'wechat'")
            migrated_count = result[0]['count'] if result else 0
            
            self.log_step("VALIDATE", f"原表记录数: {original_count}")
            self.log_step("VALIDATE", f"新表记录数: {migrated_count}")
            
            # 检查数据完整性
            integrity_sql = """
            SELECT 
                SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as empty_titles,
                SUM(CASE WHEN article_url IS NULL OR article_url = '' THEN 1 ELSE 0 END) as empty_urls,
                SUM(CASE WHEN source_name IS NULL OR source_name = '' THEN 1 ELSE 0 END) as empty_sources
            FROM articles WHERE source_type = 'wechat'
            """
            
            result = self.db.query(integrity_sql)
            if result:
                integrity = result[0]
                self.log_step("VALIDATE", f"数据完整性检查 - 空标题: {integrity['empty_titles']}, 空URL: {integrity['empty_urls']}, 空来源: {integrity['empty_sources']}")
            
            # 检查重复数据
            duplicate_sql = """
            SELECT COUNT(*) as duplicates
            FROM (
                SELECT article_url, COUNT(*) as cnt
                FROM articles 
                WHERE source_type = 'wechat'
                GROUP BY article_url 
                HAVING COUNT(*) > 1
            ) t
            """
            
            result = self.db.query(duplicate_sql)
            duplicate_count = result[0]['duplicates'] if result else 0
            self.log_step("VALIDATE", f"重复URL数量: {duplicate_count}")
            
            return migrated_count > 0
            
        except Exception as e:
            self.log_step("VALIDATE", f"验证失败: {e}", success=False)
            return False
    
    def create_compatibility_view(self):
        """创建兼容性视图"""
        logger.info("=== 创建兼容性视图 ===")
        
        try:
            view_sql = """
            CREATE OR REPLACE VIEW `wechat_articles_view` AS
            SELECT 
                id,
                source_name as account_name,
                title,
                article_url,
                publish_timestamp,
                CASE 
                    WHEN crawl_status = 'completed' THEN 1
                    WHEN crawl_status = 'failed' THEN 2
                    ELSE 0
                END as crawl_status,
                content,
                word_count,
                images,
                crawl_error as error_message,
                'wechat' as site_name,
                crawled_at,
                fetched_at
            FROM `articles` 
            WHERE `source_type` = 'wechat'
            """
            
            self.db.cursor.execute(view_sql)
            self.log_step("COMPAT", "创建兼容性视图wechat_articles_view")
            
            return True
            
        except Exception as e:
            self.log_step("COMPAT", f"创建兼容性视图失败: {e}", success=False)
            return False
    
    def save_migration_log(self):
        """保存迁移日志"""
        log_file = f"migration_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(self.migration_log, f, indent=2, ensure_ascii=False)
            
            logger.info(f"迁移日志已保存到: {log_file}")
            
        except Exception as e:
            logger.error(f"保存迁移日志失败: {e}")
    
    def _extract_table_name(self, sql_statement):
        """从SQL语句中提取表名"""
        import re
        match = re.search(r'CREATE\s+(?:TABLE|VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?`?(\w+)`?', sql_statement, re.IGNORECASE)
        return match.group(1) if match else "unknown"

def main():
    """主函数"""
    print("=" * 60)
    print("WZ项目数据库迁移工具")
    print("=" * 60)
    
    migrator = DatabaseMigrator()
    
    try:
        # 1. 检查前提条件
        if not migrator.check_prerequisites():
            print("前提条件检查失败，迁移终止")
            return False
        
        # 2. 备份原始数据
        backup_table = migrator.backup_original_data()
        if not backup_table:
            print("数据备份失败，迁移终止")
            return False
        
        # 3. 创建新表结构
        if not migrator.create_new_schema():
            print("创建新表结构失败，迁移终止")
            return False
        
        # 4. 迁移数据
        if not migrator.migrate_data():
            print("数据迁移失败，迁移终止")
            return False
        
        # 5. 验证迁移结果
        if not migrator.validate_migration():
            print("迁移验证失败，请检查数据")
            return False
        
        # 6. 创建兼容性视图
        migrator.create_compatibility_view()
        
        print("\n" + "=" * 60)
        print("数据库迁移完成！")
        print("=" * 60)
        print(f"备份表: {backup_table}")
        print("建议下一步:")
        print("1. 测试应用程序功能")
        print("2. 更新代码使用新表结构")
        print("3. 确认无误后可删除备份表")
        
        return True
        
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {e}")
        return False
        
    finally:
        migrator.save_migration_log()
        migrator.db.disconnect()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
