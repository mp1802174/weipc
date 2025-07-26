#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析Discuz数据库表结构
获取发布功能需要的详细表结构信息
"""

import mysql.connector
import json
from datetime import datetime

def analyze_discuz_structure():
    """分析Discuz数据库表结构"""
    print("🔍 分析Discuz数据库表结构")
    print("=" * 60)
    
    # 连接配置
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': '00077',
        'password': '760516',
        'database': '00077',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 要分析的表
        tables = [
            'pre_forum_thread',
            'pre_forum_post', 
            'pre_forum_forum',
            'pre_common_member'
        ]
        
        structure_info = {}
        
        for table in tables:
            print(f"\n📋 分析表: {table}")
            print("-" * 40)
            
            # 获取表结构
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            
            table_info = {
                'columns': [],
                'sample_data': None,
                'record_count': 0
            }
            
            print("字段信息:")
            for col in columns:
                field_name, field_type, null, key, default, extra = col
                table_info['columns'].append({
                    'name': field_name,
                    'type': field_type,
                    'null': null,
                    'key': key,
                    'default': default,
                    'extra': extra
                })
                print(f"  {field_name:20} {field_type:25} {null:5} {key:5} {str(default):15} {extra}")
            
            # 获取记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info['record_count'] = count
            print(f"\n记录数: {count}")
            
            # 获取样本数据
            if table == 'pre_forum_thread':
                cursor.execute(f"SELECT tid, fid, subject, author, authorid, dateline, lastpost FROM {table} ORDER BY tid DESC LIMIT 2")
            elif table == 'pre_forum_post':
                cursor.execute(f"SELECT pid, tid, first, subject, author, authorid, dateline FROM {table} WHERE first = 1 ORDER BY pid DESC LIMIT 2")
            elif table == 'pre_forum_forum':
                cursor.execute(f"SELECT fid, name, threads, posts, lastpost FROM {table} WHERE fid = 2")
            elif table == 'pre_common_member':
                cursor.execute(f"SELECT uid, username, posts, threads FROM {table} WHERE uid = 4")
            
            sample_data = cursor.fetchall()
            if sample_data:
                table_info['sample_data'] = [list(row) for row in sample_data]
                print("样本数据:")
                for row in sample_data:
                    print(f"  {row}")
            
            structure_info[table] = table_info
        
        # 获取当前最大ID
        print(f"\n📊 当前最大ID")
        print("-" * 40)
        
        cursor.execute("SELECT MAX(tid) FROM pre_forum_thread")
        max_tid = cursor.fetchone()[0] or 0
        print(f"最大TID: {max_tid}")
        
        cursor.execute("SELECT MAX(pid) FROM pre_forum_post")
        max_pid = cursor.fetchone()[0] or 0
        print(f"最大PID: {max_pid}")
        
        structure_info['max_ids'] = {
            'max_tid': max_tid,
            'max_pid': max_pid
        }
        
        # 保存结构信息到文件
        output_file = 'discuz_structure_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(structure_info, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n💾 结构信息已保存到: {output_file}")
        
        conn.close()
        return structure_info
        
    except mysql.connector.Error as e:
        print(f"❌ 数据库错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def check_wechat_articles_structure():
    """检查wechat_articles表结构"""
    print(f"\n🔍 检查WZ数据库表结构")
    print("=" * 60)
    
    config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': 'cj',
        'password': '760516',
        'database': 'cj',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # 检查wechat_articles表结构
        print("📋 wechat_articles表结构:")
        cursor.execute("DESCRIBE wechat_articles")
        columns = cursor.fetchall()
        
        has_forum_published = False
        for col in columns:
            field_name = col[0]
            if field_name == 'forum_published':
                has_forum_published = True
            print(f"  {col[0]:20} {col[1]:25} {col[2]:5} {col[3]:5}")
        
        if has_forum_published:
            print("✅ forum_published字段已存在")
        else:
            print("❌ forum_published字段不存在，需要添加")
        
        # 统计待发布文章
        if has_forum_published:
            cursor.execute("SELECT COUNT(*) FROM wechat_articles WHERE forum_published IS NULL")
        else:
            cursor.execute("SELECT COUNT(*) FROM wechat_articles")
        
        pending_count = cursor.fetchone()[0]
        print(f"📊 待发布文章数量: {pending_count}")
        
        conn.close()
        return has_forum_published
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Discuz数据库结构分析")
    print("=" * 80)
    
    # 分析Discuz表结构
    discuz_info = analyze_discuz_structure()
    
    # 检查WZ表结构
    has_field = check_wechat_articles_structure()
    
    print(f"\n{'='*80}")
    print("📋 分析完成")
    if discuz_info:
        print("✅ Discuz表结构分析成功")
    if has_field:
        print("✅ WZ表结构检查完成")
    print("=" * 80)
