#!/usr/bin/env python3
"""
调试选择器问题
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def debug_selectors():
    """调试选择器"""
    
    # 读取之前保存的HTML文件
    html_file = Path(__file__).parent / 'page_structure.html'
    
    if not html_file.exists():
        print("❌ 找不到页面结构文件")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("=== 调试主贴选择器 ===")
    
    # 测试各种主贴选择器
    selectors = [
        '#post_1',
        '.topic-post:first-child',
        '[data-post-number="1"]',
        '.post-stream .topic-post:first-child',
        '.topic-post',
        '[data-post-number]',
        '.post-stream .topic-post'
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        print(f"选择器 '{selector}': 找到 {len(elements)} 个元素")
        
        if elements:
            first_element = elements[0]
            # 检查是否有data-post-number属性
            post_number = first_element.get('data-post-number')
            if post_number:
                print(f"  第一个元素的 data-post-number: {post_number}")
            
            # 检查是否有id属性
            element_id = first_element.get('id')
            if element_id:
                print(f"  第一个元素的 id: {element_id}")
            
            # 检查class属性
            element_classes = first_element.get('class', [])
            if element_classes:
                print(f"  第一个元素的 class: {' '.join(element_classes)}")
            
            # 查找内容
            cooked = first_element.select_one('.cooked')
            if cooked:
                content_preview = cooked.get_text(strip=True)[:100]
                print(f"  内容预览: {content_preview}...")
            else:
                print("  未找到 .cooked 内容")
        
        print()
    
    print("=== 查找所有帖子 ===")
    all_posts = soup.select('.topic-post')
    print(f"总共找到 {len(all_posts)} 个帖子")
    
    for i, post in enumerate(all_posts[:5]):  # 只显示前5个
        post_number = post.get('data-post-number', 'N/A')
        post_id = post.get('id', 'N/A')
        print(f"帖子 {i+1}: data-post-number={post_number}, id={post_id}")
        
        # 查找用户名
        username_elem = post.select_one('.username')
        if username_elem:
            username = username_elem.get_text(strip=True)
            print(f"  用户名: {username}")
        
        # 查找内容
        cooked = post.select_one('.cooked')
        if cooked:
            content_preview = cooked.get_text(strip=True)[:50]
            print(f"  内容: {content_preview}...")
        
        print()

if __name__ == "__main__":
    debug_selectors()
