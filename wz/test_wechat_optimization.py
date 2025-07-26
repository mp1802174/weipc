#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试微信公众号内容优化功能
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cfcj.core.wechat_content_optimizer import optimize_wechat_content

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_sample_wechat_urls():
    """从数据库获取一些微信文章URL进行测试"""
    import mysql.connector
    
    db_config = {
        'host': '140.238.201.162',
        'port': 3306,
        'user': 'cj',
        'password': '760516',
        'database': 'cj',
        'charset': 'utf8mb4'
    }
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # 获取一些微信文章URL
        sql = """
        SELECT article_url, title, account_name 
        FROM wechat_articles 
        WHERE article_url LIKE '%mp.weixin.qq.com%' 
        AND article_url IS NOT NULL 
        LIMIT 3
        """
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        urls = []
        for row in results:
            urls.append({
                'url': row[0],
                'title': row[1] or '未知标题',
                'account': row[2] or '未知公众号'
            })
        
        return urls
        
    except Exception as e:
        logger.error(f"获取测试URL失败: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def test_single_url(url_info):
    """测试单个URL的优化提取"""
    url = url_info['url']
    print(f"\n{'='*80}")
    print(f"测试URL: {url}")
    print(f"原标题: {url_info['title']}")
    print(f"公众号: {url_info['account']}")
    print(f"{'='*80}")
    
    try:
        # 使用优化提取器
        result = optimize_wechat_content(url)
        
        if result['success']:
            print("✅ 提取成功!")
            print(f"📰 提取标题: {result.get('title', '无')}")
            print(f"🔧 提取方法: {result.get('method', '未知')}")
            print(f"📝 内容字数: {result.get('word_count', 0)}")
            
            if 'original_word_count' in result:
                original_count = result['original_word_count']
                cleaned_count = result['word_count']
                reduction = original_count - cleaned_count
                if reduction > 0:
                    print(f"🧹 清理效果: 原始 {original_count} 字符 → 清理后 {cleaned_count} 字符")
                    print(f"   减少了 {reduction} 字符 ({reduction/original_count*100:.1f}%)")
            
            # 显示内容预览
            content = result.get('content', '')
            if content:
                preview_length = 200
                preview = content[:preview_length]
                if len(content) > preview_length:
                    preview += "..."
                print(f"📄 内容预览:\n{preview}")
            
            return True
        else:
            print(f"❌ 提取失败: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {str(e)}")
        return False

def compare_methods(url):
    """比较不同提取方法的效果"""
    print(f"\n{'='*80}")
    print(f"方法对比测试: {url}")
    print(f"{'='*80}")
    
    try:
        from cfcj.core.wechat_content_optimizer import WeChatContentOptimizer
        
        optimizer = WeChatContentOptimizer()
        
        # 测试 trafilatura
        print("\n🔧 测试 trafilatura:")
        traf_result = optimizer.extract_with_trafilatura(url)
        if traf_result['success']:
            print(f"✅ 成功 - 字数: {traf_result['word_count']}")
        else:
            print(f"❌ 失败: {traf_result['error']}")
        
        # 测试 newspaper3k
        print("\n📰 测试 newspaper3k:")
        news_result = optimizer.extract_with_newspaper(url)
        if news_result['success']:
            print(f"✅ 成功 - 字数: {news_result['word_count']}")
        else:
            print(f"❌ 失败: {news_result['error']}")
        
        # 测试优化方法
        print("\n🚀 测试优化方法:")
        opt_result = optimizer.optimize_content(url)
        if opt_result['success']:
            print(f"✅ 成功 - 字数: {opt_result['word_count']}")
            print(f"   清理率: {opt_result.get('cleaning_ratio', 0)*100:.1f}%")
        else:
            print(f"❌ 失败: {opt_result['error']}")
        
        # 比较结果
        if traf_result['success'] and news_result['success']:
            traf_len = traf_result['word_count']
            news_len = news_result['word_count']
            print(f"\n📊 对比结果:")
            print(f"   trafilatura: {traf_len} 字符")
            print(f"   newspaper3k: {news_len} 字符")
            print(f"   长度比例: {traf_len/news_len:.2f}" if news_len > 0 else "   无法计算比例")
        
    except Exception as e:
        print(f"❌ 对比测试异常: {str(e)}")

def main():
    """主测试函数"""
    print("🧪 微信公众号内容优化测试")
    print("=" * 80)
    
    # 获取测试URL
    print("📡 从数据库获取测试URL...")
    test_urls = get_sample_wechat_urls()
    
    if not test_urls:
        print("⚠️  没有找到测试URL，请确保数据库中有微信文章数据")
        return
    
    print(f"✅ 找到 {len(test_urls)} 个测试URL")
    
    # 测试每个URL
    success_count = 0
    for i, url_info in enumerate(test_urls, 1):
        print(f"\n🔍 测试 {i}/{len(test_urls)}")
        if test_single_url(url_info):
            success_count += 1
        
        # 如果是第一个URL，进行详细的方法对比
        if i == 1:
            compare_methods(url_info['url'])
    
    # 总结
    print(f"\n{'='*80}")
    print(f"📊 测试总结:")
    print(f"   总测试数: {len(test_urls)}")
    print(f"   成功数: {success_count}")
    print(f"   成功率: {success_count/len(test_urls)*100:.1f}%")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
