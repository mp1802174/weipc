"""
CFCJ工具函数模块
"""
import re
import time
import hashlib
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta


def clean_text(text: str) -> str:
    """
    清理文本内容
    
    Args:
        text: 原始文本
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除多余的空白字符
    text = re.sub(r'\s+', ' ', text)
    
    # 移除首尾空白
    text = text.strip()
    
    return text


def extract_domain(url: str) -> str:
    """
    从URL中提取域名
    
    Args:
        url: URL地址
        
    Returns:
        域名
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""


def is_valid_url(url: str) -> bool:
    """
    检查URL是否有效
    
    Args:
        url: URL地址
        
    Returns:
        是否有效
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def generate_hash(text: str) -> str:
    """
    生成文本的MD5哈希值
    
    Args:
        text: 输入文本
        
    Returns:
        MD5哈希值
    """
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的大小字符串
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def parse_time_string(time_str: str) -> Optional[datetime]:
    """
    解析时间字符串
    
    Args:
        time_str: 时间字符串
        
    Returns:
        datetime对象或None
    """
    if not time_str:
        return None
    
    # 常见时间格式
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S',
        '%Y/%m/%d %H:%M',
        '%Y/%m/%d',
        '%d/%m/%Y %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%d-%m-%Y %H:%M:%S',
        '%d-%m-%Y %H:%M',
        '%d-%m-%Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    
    return None


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (attempt + 1))
                        continue
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator


def batch_process(items: List[Any], batch_size: int = 10):
    """
    批量处理生成器
    
    Args:
        items: 要处理的项目列表
        batch_size: 批次大小
        
    Yields:
        批次项目列表
    """
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def safe_filename(filename: str) -> str:
    """
    生成安全的文件名
    
    Args:
        filename: 原始文件名
        
    Returns:
        安全的文件名
    """
    # 移除或替换不安全的字符
    unsafe_chars = r'[<>:"/\\|?*]'
    safe_name = re.sub(unsafe_chars, '_', filename)
    
    # 限制长度
    if len(safe_name) > 200:
        safe_name = safe_name[:200]
    
    return safe_name


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归合并字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（简单版本）
    
    Args:
        text1: 第一个文本
        text2: 第二个文本
        
    Returns:
        相似度（0-1之间）
    """
    if not text1 or not text2:
        return 0.0
    
    # 转换为小写并分词
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # 计算交集和并集
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if not union:
        return 0.0
    
    return len(intersection) / len(union)


def get_relative_time(timestamp: datetime) -> str:
    """
    获取相对时间描述
    
    Args:
        timestamp: 时间戳
        
    Returns:
        相对时间描述
    """
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"
