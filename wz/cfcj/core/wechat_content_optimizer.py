#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号内容优化器
使用 trafilatura + newspaper3k 进行智能内容提取和清理
"""

import re
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class WeChatContentOptimizer:
    """微信公众号内容优化器"""
    
    def __init__(self):
        self.unwanted_patterns = [
            # 关注相关
            r'点击.*?关注',
            r'长按.*?关注',
            r'扫码关注',
            r'关注.*?公众号',
            r'点击上方.*?关注',
            r'点击👇.*?关注',
            r'星标置顶',
            
            # 互动相关
            r'点击.*?阅读原文',
            r'在看点这里',
            r'分享点这里',
            r'点赞.*?在看',
            r'转发.*?朋友圈',
            
            # 推广相关
            r'推荐阅读',
            r'往期精彩',
            r'更多精彩内容',
            r'热门文章',
            r'相关阅读',
            
            # 版权相关
            r'免责声明',
            r'版权声明',
            r'版权所有',
            r'转载请注明',
            
            # 商务相关
            r'商务合作',
            r'投稿邮箱',
            r'联系我们',
            r'广告投放',
            
            # 特殊标记
            r'——.*?节选自',
            r'来源[:：]',
            r'编辑[:：]',
            r'审核[:：]',
        ]
        
        # 编译正则表达式以提高性能
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.unwanted_patterns]
    
    def extract_with_trafilatura(self, url: str) -> Dict[str, Any]:
        """使用 trafilatura 提取内容"""
        try:
            import trafilatura
            import requests

            logger.info(f"使用 trafilatura 提取: {url}")

            # 尝试直接使用requests下载，避免代理问题
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                downloaded = response.text
            except Exception as e:
                logger.warning(f"requests下载失败，尝试trafilatura: {e}")
                # 回退到trafilatura的下载方法
                downloaded = trafilatura.fetch_url(url)

            if not downloaded:
                return {'success': False, 'error': '无法下载网页内容'}

            # 提取主要内容
            content = trafilatura.extract(
                downloaded,
                include_comments=False,
                include_tables=True,
                include_images=False,  # 微信文章图片处理复杂，暂时不包含
                include_links=False,   # 减少无关链接
                output_format='txt'
            )

            if not content:
                return {'success': False, 'error': 'trafilatura 无法提取内容'}

            # 获取元数据
            metadata = trafilatura.extract_metadata(downloaded)

            return {
                'success': True,
                'method': 'trafilatura',
                'title': metadata.title if metadata else '',
                'content': content,
                'word_count': len(content),
                'raw_length': len(downloaded) if downloaded else 0
            }

        except ImportError:
            return {'success': False, 'error': 'trafilatura 未安装'}
        except Exception as e:
            logger.error(f"trafilatura 提取失败: {e}")
            return {'success': False, 'error': f'trafilatura 提取失败: {str(e)}'}
    
    def extract_with_newspaper(self, url: str) -> Dict[str, Any]:
        """使用 newspaper3k 提取内容"""
        try:
            from newspaper import Article
            import requests

            logger.info(f"使用 newspaper3k 提取: {url}")

            # 创建文章对象，配置请求参数
            article = Article(url, language='zh')

            # 设置请求头
            article.config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            article.config.request_timeout = 30

            # 下载和解析
            article.download()

            # 检查下载是否成功
            if not article.html:
                return {'success': False, 'error': 'newspaper3k 无法下载网页'}

            article.parse()

            if not article.text:
                return {'success': False, 'error': 'newspaper3k 无法提取内容'}

            return {
                'success': True,
                'method': 'newspaper3k',
                'title': article.title or '',
                'content': article.text,
                'word_count': len(article.text),
                'images': list(article.images) if article.images else []
            }

        except ImportError:
            return {'success': False, 'error': 'newspaper3k 未安装'}
        except Exception as e:
            logger.error(f"newspaper3k 提取失败: {e}")
            return {'success': False, 'error': f'newspaper3k 提取失败: {str(e)}'}
    
    def clean_wechat_content(self, content: str) -> str:
        """清理微信文章内容"""
        if not content:
            return content
        
        logger.debug("开始清理微信文章内容")
        
        # 按行分割
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 检查是否匹配不需要的模式
            should_skip = False
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    logger.debug(f"跳过行: {line[:50]}...")
                    should_skip = True
                    break
            
            # 过滤过短的行（可能是无意义的片段）
            if len(line) < 3:
                should_skip = True
            
            # 过滤纯符号行
            if re.match(r'^[^\w\u4e00-\u9fff]*$', line):
                should_skip = True
            
            if not should_skip:
                cleaned_lines.append(line)
        
        cleaned_content = '\n'.join(cleaned_lines)
        
        # 移除多余的空行
        cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
        
        reduction = len(content) - len(cleaned_content)
        if reduction > 0:
            logger.info(f"内容清理完成，减少了 {reduction} 个字符 ({reduction/len(content)*100:.1f}%)")
        
        return cleaned_content.strip()
    
    def optimize_content(self, url: str) -> Dict[str, Any]:
        """优化微信文章内容提取"""
        logger.info(f"开始优化内容提取: {url}")
        
        # 验证是否为微信链接
        if 'mp.weixin.qq.com' not in url:
            logger.warning(f"非微信链接，使用标准提取: {url}")
            return self.extract_with_trafilatura(url)
        
        # 使用两种方法提取
        trafilatura_result = self.extract_with_trafilatura(url)
        newspaper_result = self.extract_with_newspaper(url)
        
        # 选择最佳结果
        best_result = self._select_best_result(trafilatura_result, newspaper_result)
        
        if best_result['success']:
            # 清理内容
            original_content = best_result['content']
            cleaned_content = self.clean_wechat_content(original_content)
            
            # 更新结果
            best_result['content'] = cleaned_content
            best_result['word_count'] = len(cleaned_content)
            best_result['original_word_count'] = len(original_content)
            best_result['cleaning_ratio'] = (len(original_content) - len(cleaned_content)) / len(original_content) if len(original_content) > 0 else 0
            
            logger.info(f"内容优化完成: {best_result['word_count']} 字符 (清理率: {best_result['cleaning_ratio']*100:.1f}%)")
        
        return best_result
    
    def _select_best_result(self, trafilatura_result: Dict[str, Any], newspaper_result: Dict[str, Any]) -> Dict[str, Any]:
        """选择最佳提取结果"""
        
        # 如果只有一个成功，返回成功的那个
        if trafilatura_result['success'] and not newspaper_result['success']:
            logger.info("选择 trafilatura 结果（newspaper 失败）")
            return trafilatura_result
        elif newspaper_result['success'] and not trafilatura_result['success']:
            logger.info("选择 newspaper 结果（trafilatura 失败）")
            return newspaper_result
        elif not trafilatura_result['success'] and not newspaper_result['success']:
            logger.error("两种方法都失败了")
            return {'success': False, 'error': '所有提取方法都失败了'}
        
        # 两个都成功，比较质量
        traf_content = trafilatura_result['content']
        news_content = newspaper_result['content']
        
        traf_length = len(traf_content)
        news_length = len(news_content)
        
        # 选择策略：
        # 1. 优先选择内容更长的（通常意味着提取更完整）
        # 2. 如果长度相近（差异<20%），优先选择 trafilatura（通常更干净）
        
        if abs(traf_length - news_length) / max(traf_length, news_length) < 0.2:
            # 长度相近，优先选择 trafilatura
            logger.info(f"选择 trafilatura 结果（长度相近，trafilatura: {traf_length}, newspaper: {news_length}）")
            return trafilatura_result
        elif traf_length > news_length:
            logger.info(f"选择 trafilatura 结果（内容更长，trafilatura: {traf_length}, newspaper: {news_length}）")
            return trafilatura_result
        else:
            logger.info(f"选择 newspaper 结果（内容更长，newspaper: {news_length}, trafilatura: {traf_length}）")
            return newspaper_result

# 全局实例
wechat_optimizer = WeChatContentOptimizer()

def optimize_wechat_content(url: str) -> Dict[str, Any]:
    """优化微信内容提取的便捷函数"""
    return wechat_optimizer.optimize_content(url)
