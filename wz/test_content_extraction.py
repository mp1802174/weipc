#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号内容提取测试脚本
使用 trafilatura + newspaper3k 进行智能内容提取
"""

import requests
import logging
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_with_trafilatura(url: str) -> Dict[str, Any]:
    """使用 trafilatura 提取内容"""
    try:
        import trafilatura
        
        # 下载网页内容
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return {'success': False, 'error': '无法下载网页内容'}
        
        # 提取主要内容
        result = trafilatura.extract(
            downloaded,
            include_comments=False,  # 不包含评论
            include_tables=True,     # 包含表格
            include_images=True,     # 包含图片信息
            include_links=True,      # 包含链接
            output_format='txt'      # 输出纯文本
        )
        
        if not result:
            return {'success': False, 'error': 'trafilatura 无法提取内容'}
        
        # 获取元数据
        metadata = trafilatura.extract_metadata(downloaded)
        
        return {
            'success': True,
            'method': 'trafilatura',
            'title': metadata.title if metadata else '',
            'author': metadata.author if metadata else '',
            'date': metadata.date if metadata else '',
            'content': result,
            'word_count': len(result),
            'url': url
        }
        
    except ImportError:
        return {'success': False, 'error': 'trafilatura 未安装'}
    except Exception as e:
        return {'success': False, 'error': f'trafilatura 提取失败: {str(e)}'}

def extract_with_newspaper(url: str) -> Dict[str, Any]:
    """使用 newspaper3k 提取内容"""
    try:
        from newspaper import Article
        
        # 创建文章对象
        article = Article(url, language='zh')
        
        # 下载和解析
        article.download()
        article.parse()
        
        # 尝试提取关键词和摘要（可能需要额外的NLP处理）
        try:
            article.nlp()
        except:
            pass  # NLP处理失败不影响主要内容提取
        
        if not article.text:
            return {'success': False, 'error': 'newspaper3k 无法提取内容'}
        
        return {
            'success': True,
            'method': 'newspaper3k',
            'title': article.title or '',
            'author': ', '.join(article.authors) if article.authors else '',
            'date': article.publish_date.isoformat() if article.publish_date else '',
            'content': article.text,
            'word_count': len(article.text),
            'summary': article.summary if hasattr(article, 'summary') else '',
            'keywords': article.keywords if hasattr(article, 'keywords') else [],
            'images': list(article.images) if article.images else [],
            'url': url
        }
        
    except ImportError:
        return {'success': False, 'error': 'newspaper3k 未安装'}
    except Exception as e:
        return {'success': False, 'error': f'newspaper3k 提取失败: {str(e)}'}

def extract_with_both(url: str) -> Dict[str, Any]:
    """使用两种方法提取内容并比较结果"""
    logger.info(f"开始提取URL: {url}")
    
    # 使用两种方法提取
    trafilatura_result = extract_with_trafilatura(url)
    newspaper_result = extract_with_newspaper(url)
    
    # 分析结果
    results = {
        'url': url,
        'trafilatura': trafilatura_result,
        'newspaper': newspaper_result,
        'comparison': {}
    }
    
    # 比较两种方法的效果
    if trafilatura_result['success'] and newspaper_result['success']:
        traf_content = trafilatura_result['content']
        news_content = newspaper_result['content']
        
        results['comparison'] = {
            'trafilatura_length': len(traf_content),
            'newspaper_length': len(news_content),
            'length_ratio': len(traf_content) / len(news_content) if len(news_content) > 0 else 0,
            'recommended': 'trafilatura' if len(traf_content) > len(news_content) else 'newspaper'
        }
        
        # 选择更好的结果
        if len(traf_content) > len(news_content):
            results['best_result'] = trafilatura_result
        else:
            results['best_result'] = newspaper_result
    elif trafilatura_result['success']:
        results['best_result'] = trafilatura_result
        results['comparison']['recommended'] = 'trafilatura'
    elif newspaper_result['success']:
        results['best_result'] = newspaper_result
        results['comparison']['recommended'] = 'newspaper'
    else:
        results['best_result'] = {'success': False, 'error': '两种方法都失败了'}
    
    return results

def clean_wechat_content(content: str) -> str:
    """清理微信文章内容的辅助函数"""
    if not content:
        return content
    
    # 常见的微信文章无关内容模式
    unwanted_patterns = [
        '点击上方蓝字关注',
        '长按二维码关注',
        '扫码关注我们',
        '点击阅读原文',
        '在看点这里',
        '分享点这里',
        '点击👇下方小卡片关注',
        '星标置顶',
        '推荐阅读',
        '往期精彩',
        '更多精彩内容',
        '免责声明',
        '版权声明',
        '商务合作',
        '投稿邮箱'
    ]
    
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否包含不需要的内容
        should_skip = False
        for pattern in unwanted_patterns:
            if pattern in line:
                should_skip = True
                break
        
        if not should_skip:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def test_extraction(test_urls: list):
    """测试多个URL的提取效果"""
    print("=" * 80)
    print("微信公众号内容提取测试")
    print("=" * 80)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n【测试 {i}】URL: {url}")
        print("-" * 60)
        
        try:
            results = extract_with_both(url)
            
            if results['best_result']['success']:
                best = results['best_result']
                print(f"✅ 提取成功 (推荐方法: {results['comparison'].get('recommended', 'unknown')})")
                print(f"📰 标题: {best.get('title', '未知')}")
                print(f"👤 作者: {best.get('author', '未知')}")
                print(f"📅 日期: {best.get('date', '未知')}")
                print(f"📝 字数: {best.get('word_count', 0)}")
                
                # 显示内容预览（前200字符）
                content = best.get('content', '')
                cleaned_content = clean_wechat_content(content)
                preview = cleaned_content[:200] + "..." if len(cleaned_content) > 200 else cleaned_content
                print(f"📄 内容预览:\n{preview}")
                
                # 显示清理效果
                if len(cleaned_content) != len(content):
                    reduction = len(content) - len(cleaned_content)
                    print(f"🧹 清理效果: 减少了 {reduction} 个字符 ({reduction/len(content)*100:.1f}%)")
                
            else:
                print(f"❌ 提取失败: {results['best_result'].get('error', '未知错误')}")
                
        except Exception as e:
            print(f"❌ 测试异常: {str(e)}")
        
        print("-" * 60)

if __name__ == "__main__":
    # 测试URL列表（请替换为实际的微信公众号文章URL）
    test_urls = [
        # 示例URL，请替换为实际的微信文章链接
        "https://mp.weixin.qq.com/s/example1",
        "https://mp.weixin.qq.com/s/example2",
    ]
    
    print("请将测试URL添加到 test_urls 列表中，然后运行测试")
    print("示例用法:")
    print("python test_content_extraction.py")
    
    # 如果有测试URL，运行测试
    if any("example" not in url for url in test_urls):
        test_extraction(test_urls)
    else:
        print("\n⚠️  请先添加真实的微信文章URL进行测试")
