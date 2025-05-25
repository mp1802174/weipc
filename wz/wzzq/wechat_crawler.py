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
import logging # 新增: 用于日志记录

from .utils import load_auth_info, load_wechat_accounts, jstime_to_datetime, DEFAULT_HEADERS, save_wechat_accounts

# 新增: 配置一个简单的日志记录器，如果已有则可忽略
logger = logging.getLogger(__name__)
# (如果需要，可以在这里添加handler和formatter，但通常由调用方配置)

# 1.1. 定义自定义异常类
class CredentialsExpiredError(Exception):
    pass

class RateLimitError(Exception): # 新增: 针对频率控制的异常
    pass


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
        
    # 1.2. 添加新的私有方法 _check_credential_status
    def _check_credential_status(self, response_json, api_name="API"):
        """检查API响应，判断凭据是否失效或请求是否被频率控制"""
        if not isinstance(response_json, dict): # 确保 response_json 是字典
            logger.warning(f"{api_name}: API响应格式不正确，期望字典，得到 {type(response_json)}")
            # 可以根据实际情况决定是否抛出通用异常
            # raise Exception(f"{api_name}: API响应格式不正确")
            return # 或者直接返回，让后续的逻辑处理空响应

        base_resp = response_json.get('base_resp', {})
        err_msg = base_resp.get('err_msg', '').lower() # 转为小写以便比较
        ret_code = base_resp.get('ret')

        if err_msg in ['invalid session', 'invalid csrf token', 'missing session', 'missing csrf token']: # 增加了 missing 的情况
            logger.warning(f"{api_name}: 凭据已失效 (ret: {ret_code}, msg: {err_msg}). 请更新凭据。")
            raise CredentialsExpiredError(f"凭据已失效 (ret: {ret_code}): {err_msg}")
        
        if err_msg == 'freq control' or 'freq control' in err_msg: # 更灵活的频率控制检查
            logger.warning(f"{api_name}: 请求频率过快 (ret: {ret_code}, msg: {err_msg}). 请稍后再试。")
            raise RateLimitError(f"请求频率过快 (ret: {ret_code}): {err_msg}")

        if ret_code != 0:
            logger.warning(f"{api_name}: API调用失败 (ret: {ret_code}, msg: {err_msg}).")
            # 对于其他非0的ret_code，可以抛出通用异常，或者让调用方根据具体业务处理
            # raise Exception(f"{api_name} 调用失败 (ret: {ret_code}): {err_msg}")
            # 注意：如果这里抛出通用异常，get_articles等方法需要能处理，或者依赖于 response.get('list', []) 等返回空
            # 为了保持与原逻辑的兼容性（即ret!=0时返回空列表或None），这里可以仅记录日志而不抛出通用异常
            # 调用方通常会检查期望的数据是否存在于response_json中

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
            str: 公众号的fakeid，如果未找到或发生错误则返回None
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
            response = requests.get(url=url, params=params, headers=self.headers)
            response.raise_for_status() # 检查HTTP错误
            response_json = response.json()
            
            # 1.3. 调用 _check_credential_status
            self._check_credential_status(response_json, api_name="search_biz") # 新增调用

            # 原有的 ret != 0 检查已被 _check_credential_status 覆盖或部分替代
            # 如果 _check_credential_status 中对于未知 ret !=0 的情况不抛异常，
            # 那么这里依然需要检查 response_json 中是否有期望的数据
            
            # 查找匹配的公众号
            # 确保 'list' 键存在且其值为列表
            account_list = response_json.get('list', [])
            if not isinstance(account_list, list):
                logger.warning(f"search_biz: API响应中的'list'字段不是列表或不存在。响应: {response_json}")
                return None

            for account in account_list:
                if account.get('nickname') == account_name: # 增加 .get() 避免KeyError
                    fakeid = account.get('fakeid')
                    if fakeid:
                        self.accounts[account_name] = fakeid
                        save_wechat_accounts(self.accounts)
                        return fakeid
                    
            logger.info(f"未找到公众号: {account_name}") # 从 print 改为 logger.info
            return None
            
        except CredentialsExpiredError: # 直接重新抛出，让上层处理
            raise
        except RateLimitError: # 直接重新抛出
            raise
        except requests.exceptions.RequestException as e: # 网络或HTTP错误
            logger.error(f"获取公众号fakeid时发生网络请求异常 for {account_name}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"获取公众号fakeid时解析JSON响应失败 for {account_name}: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e: # 其他未知异常
            logger.error(f"获取公众号fakeid时发生未知异常 for {account_name}: {e}", exc_info=True)
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
        
        articles_data = [] # 重命名内部变量以区分返回的 articles
        url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish?"
        
        try:
            response = requests.get(url=url, params=params, headers=self.headers)
            response.raise_for_status() # 检查HTTP错误
            response_json = response.json()

            # 1.4. 调用 _check_credential_status
            self._check_credential_status(response_json, api_name="appmsgpublish") # 新增调用

            # 原有的 ret != 0 检查已被 _check_credential_status 覆盖或部分替代
            
            # 处理文章列表
            if 'publish_page' not in response_json:
                logger.warning(f"appmsgpublish: API响应中未包含'publish_page'字段 for {account_name}。响应: {response_json}")
                return [] # 返回空列表表示没有获取到文章
                
            # 确保 publish_page 的内容是字符串，以便 json.loads
            publish_page_str = response_json.get('publish_page')
            if not isinstance(publish_page_str, str):
                logger.warning(f"appmsgpublish: 'publish_page'内容不是字符串 for {account_name}。实际类型: {type(publish_page_str)}")
                return []

            messages_outer = json.loads(publish_page_str)
            if 'publish_list' not in messages_outer:
                logger.warning(f"appmsgpublish: 解析'publish_page'后未找到'publish_list' for {account_name}。解析结果: {messages_outer}")
                return []

            messages = messages_outer['publish_list']
            for message_item_wrapper in messages: # publish_list 中的每个元素可能还是一个包装
                # publish_info 在 publish_list 的每个元素的 'publish_info' 字段中
                if not isinstance(message_item_wrapper, dict) or 'publish_info' not in message_item_wrapper:
                    logger.warning(f"appmsgpublish: 'publish_list'中的项目格式不正确或缺少'publish_info' for {account_name}。项目: {message_item_wrapper}")
                    continue

                message_info_str = message_item_wrapper['publish_info']
                if not isinstance(message_info_str, str):
                    logger.warning(f"appmsgpublish: 'publish_info'内容不是字符串 for {account_name}。实际类型: {type(message_info_str)}")
                    continue
                
                message_content = json.loads(message_info_str) # 解析 'publish_info' 的内容
                
                # appmsgex 在解析后的 'publish_info' 的 'appmsgex' 字段中
                if not isinstance(message_content, dict) or 'appmsgex' not in message_content or not isinstance(message_content['appmsgex'], list):
                    logger.warning(f"appmsgpublish: 解析'publish_info'后内容格式不正确或缺少'appmsgex'列表 for {account_name}。内容: {message_content}")
                    continue

                for article_detail in message_content['appmsgex']:
                    if not isinstance(article_detail, dict): # 确保 article_detail 是字典
                        logger.warning(f"appmsgpublish: 'appmsgex'中的项目不是字典 for {account_name}。项目: {article_detail}")
                        continue
                    
                    # 跳过没有创建时间的文章
                    if not article_detail.get('create_time'):
                        continue
                        
                    # 转换时间戳为datetime对象
                    publish_time = jstime_to_datetime(article_detail['create_time'])
                    
                    articles_data.append({
                        'title': article_detail.get('title', '未知标题'), # 使用.get增加健壮性
                        'article_url': article_detail.get('link', ''),
                        'publish_timestamp': publish_time,
                        'account_name': account_name
                    })
                    
                    # 如果达到限制数量，则返回
                    if len(articles_data) >= limit:
                        return articles_data
                        
            return articles_data # 返回已收集的文章
            
        except CredentialsExpiredError: # 直接重新抛出
            raise
        except RateLimitError: # 直接重新抛出
            raise
        except requests.exceptions.RequestException as e: # 网络或HTTP错误
            logger.error(f"获取文章列表时发生网络请求异常 for {account_name}: {e}")
            return []
        except json.JSONDecodeError as e: # JSON解析错误
            logger.error(f"获取文章列表时解析JSON响应失败 for {account_name}: {e}. Response text: {response.text if 'response' in locals() else 'N/A'}")
            return []
        except Exception as e: # 其他未知异常
            logger.error(f"获取文章列表时发生未知异常 for {account_name}: {e}", exc_info=True)
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