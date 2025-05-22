#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
微信公众号文章抓取模块
实现公众号文章列表抓取和处理
"""

import json
import requests
import time
from tqdm import tqdm

from .utils import load_auth_info, load_wechat_accounts, jstime_to_datetime, DEFAULT_HEADERS


class WechatCrawler:
    """微信公众号文章抓取类"""
    
    def __init__(self):
        """初始化抓取器，加载认证信息"""
        # 加载认证信息
        auth_info = load_auth_info()
        self.token = auth_info.get('token')
        self.cookie = auth_info.get('cookie')
        
        # 设置请求头
        self.headers = DEFAULT_HEADERS.copy()
        if self.cookie:
            self.headers['Cookie'] = self.cookie
            
        # 加载公众号列表
        self.accounts = load_wechat_accounts()
        
    def is_authenticated(self):
        """
        检查是否已认证
        
        Returns:
            bool: 是否已认证
        """
        return bool(self.token and self.cookie)
        
    def get_account_fakeid(self, account_name):
        """
        获取公众号的fakeid
        
        Args:
            account_name: 公众号名称
            
        Returns:
            str: 公众号的fakeid，如果未找到则返回None
        """
        # 首先从缓存中查找
        if account_name in self.accounts and self.accounts[account_name]:
            return self.accounts[account_name]
            
        # 如果缓存中没有，则通过API获取
        params = {
            'action': 'search_biz',
            'begin': 0,
            'count': 5,
            'query': account_name,
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': 1,
        }
        
        url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
        try:
            response = requests.get(url=url, params=params, headers=self.headers).json()
            
            # 检查API响应状态
            if response.get('base_resp', {}).get('ret') != 0:
                print(f"获取公众号fakeid失败: {response.get('base_resp', {}).get('err_msg')}")
                return None
                
            # 查找匹配的公众号
            for account in response.get('list', []):
                if account['nickname'] == account_name:
                    # 更新缓存
                    self.accounts[account_name] = account['fakeid']
                    return account['fakeid']
                    
            print(f"未找到公众号: {account_name}")
            return None
            
        except Exception as e:
            print(f"获取公众号fakeid异常: {e}")
            return None
            
    def get_articles(self, account_name, limit=20):
        """
        获取公众号的文章列表
        
        Args:
            account_name: 公众号名称
            limit: 获取的文章数量限制
            
        Returns:
            list: 文章信息列表，每篇文章包含title, link, create_time
        """
        if not self.is_authenticated():
            print("未认证，无法获取文章列表")
            return []
            
        # 获取公众号fakeid
        fakeid = self.get_account_fakeid(account_name)
        if not fakeid:
            print(f"无法获取公众号{account_name}的fakeid")
            return []
            
        # 设置请求参数
        params = {
            'sub': 'list',
            'search_field': 'null',
            'begin': 0,
            'count': min(limit, 5),  # 单次请求最多5条
            'query': '',
            'fakeid': fakeid,
            'type': '101_1',
            'free_publish_type': 1,
            'sub_action': 'list_ex',
            'token': self.token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': 1,
        }
        
        articles = []
        url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish?"
        
        try:
            response = requests.get(url=url, params=params, headers=self.headers).json()
            
            # 检查API响应状态
            if response.get('base_resp', {}).get('ret') != 0:
                print(f"获取文章列表失败: {response.get('base_resp', {}).get('err_msg')}")
                return []
                
            # 处理文章列表
            if 'publish_page' not in response:
                print("API响应中未包含文章列表")
                return []
                
            messages = json.loads(response['publish_page'])['publish_list']
            for message_item in messages:
                message = json.loads(message_item['publish_info'])
                
                for article in message['appmsgex']:
                    # 跳过没有创建时间的文章
                    if not article.get('create_time'):
                        continue
                        
                    # 转换时间戳为datetime对象
                    publish_time = jstime_to_datetime(article['create_time'])
                    
                    articles.append({
                        'title': article['title'],
                        'article_url': article['link'],
                        'publish_timestamp': publish_time,
                        'account_name': account_name
                    })
                    
                    # 如果达到限制数量，则返回
                    if len(articles) >= limit:
                        return articles
                        
            return articles
            
        except Exception as e:
            print(f"获取文章列表异常: {e}")
            return []
            
    def crawl_all_accounts(self, limit_per_account=10):
        """
        抓取所有公众号的文章
        
        Args:
            limit_per_account: 每个公众号抓取的文章数量
            
        Returns:
            list: 所有文章的列表
        """
        all_articles = []
        
        print(f"开始抓取{len(self.accounts)}个公众号的文章...")
        for account_name in tqdm(self.accounts.keys()):
            print(f"抓取公众号: {account_name}")
            
            # 获取公众号文章
            articles = self.get_articles(account_name, limit=limit_per_account)
            
            # 添加到总列表
            all_articles.extend(articles)
            
            # 防止请求频率过快
            time.sleep(1)
            
        print(f"抓取完成，共获取{len(all_articles)}篇文章")
        return all_articles