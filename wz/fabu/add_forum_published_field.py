#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为wechat_articles表添加forum_published字段
"""

import mysql.connector

def add_forum_published_field():
    """添加forum_published字段"""
    print("🔧 添加forum_published字段到wechat_articles表")
    
    try:
        # 连接WZ数据库
        conn = mysql.connector.connect(
            host='140.238.201.162',
            port=3306,
            user='cj',
            password='760516',
            database='cj',
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("SHOW COLUMNS FROM wechat_articles LIKE 'forum_published'")
        result = cursor.fetchone()
        
        if result:
            print("✅ forum_published字段已存在，无需添加")
            return True
        
        # 添加字段
        print("📝 正在添加forum_published字段...")
        alter_sql = """
        ALTER TABLE wechat_articles 
        ADD COLUMN forum_published TINYINT(1) DEFAULT NULL 
        COMMENT '论坛发布状态: NULL=未发布, 1=已发布'
        """
        
        cursor.execute(alter_sql)
        conn.commit()
        
        print("✅ forum_published字段添加成功")
        
        # 验证字段添加
        cursor.execute("SHOW COLUMNS FROM wechat_articles LIKE 'forum_published'")
        result = cursor.fetchone()
        if result:
            print(f"✅ 验证成功: {result}")
        
        # 统计待发布文章数量
        cursor.execute("SELECT COUNT(*) FROM wechat_articles WHERE forum_published IS NULL")
        pending_count = cursor.fetchone()[0]
        print(f"📊 待发布文章数量: {pending_count}")
        
        conn.close()
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

if __name__ == "__main__":
    add_forum_published_field()
