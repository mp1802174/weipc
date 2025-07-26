#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Web API端点
"""

import requests
import json

def test_forum_publish_status():
    """测试论坛发布状态API"""
    print("🔍 测试论坛发布状态API...")
    
    try:
        response = requests.get('http://127.0.0.1:5000/forum_publish_status')
        data = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        if data.get('success'):
            print(f"✅ 待发布文章数量: {data['pending_count']}")
        else:
            print(f"❌ 获取状态失败: {data.get('message')}")
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")

def test_batch_publish_api():
    """测试批量发布API（仅测试连接，不实际发布）"""
    print("\n🔍 测试批量发布API连接...")
    
    try:
        # 只是测试API是否可访问，不实际发送POST请求
        response = requests.get('http://127.0.0.1:5000/')
        if response.status_code == 200:
            print("✅ Web服务正常运行")
            print("✅ 批量发布API端点应该可用")
        else:
            print(f"❌ Web服务状态异常: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")

if __name__ == "__main__":
    print("🧪 Web API测试")
    print("=" * 50)
    
    test_forum_publish_status()
    test_batch_publish_api()
    
    print("\n" + "=" * 50)
    print("✅ API测试完成")
    print("💡 请在浏览器中访问 http://127.0.0.1:5000 查看Web界面")
