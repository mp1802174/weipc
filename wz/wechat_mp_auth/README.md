# 微信公众平台认证模块 (wechat_mp_auth)

这个模块提供微信公众平台的登录认证功能，包括扫码登录、凭据保存和会话状态检查。

## 功能特点

- 自动化扫码登录微信公众平台
- 获取并保存登录凭据（token和cookie）
- 检测会话是否过期并自动重新登录
- 处理API请求频率限制

## 安装要求

- Python 3.6+
- DrissionPage (用于浏览器自动化)

## 基本用法

### 初始化

```python
from wz.wechat_mp_auth import WeChatAuth

# 使用默认配置创建认证对象
auth = WeChatAuth()

# 或者使用自定义配置
from wz.wechat_mp_auth.config import Config
custom_config = Config(data_dir='custom/path', id_info_filename='custom_id_info')
auth = WeChatAuth(config=custom_config)
```

### 登录

```python
try:
    # 简单登录
    auth.login()
    
    # 或者提供DrissionPage配置
    auth.login(drission_page_config={
        'driver_path': '/path/to/chromedriver'
    })
    
    # 登录成功后可以使用token和cookie
    print(f"Token: {auth.token}")
    print(f"Cookie: {auth.cookie_str}")
    
except LoginError as e:
    print(f"登录失败: {e}")
```

### 检查会话状态

```python
# 假设你从API获取了响应
api_response = {
    'base_resp': {
        'err_msg': 'ok',
        'ret': 0
    },
    'data': 'some_data'
}

try:
    if auth.session_is_overdue(api_response):
        print("会话已过期或遇到频率限制，已自动处理")
    else:
        print("会话正常")
except LoginError as e:
    print(f"重新登录失败: {e}")
```

### 获取请求头

```python
try:
    headers = auth.get_headers()
    # 使用headers进行API请求
except LoginError as e:
    print(f"获取请求头失败: {e}")
```

## 配置说明

- `data_dir`: 凭据文件存储目录，默认为 `WZ/data`
- `id_info_filename`: 凭据文件名，默认为 `id_info`

## 异常处理

模块定义了 `LoginError` 异常，在以下情况会抛出：

- 登录超时（用户未扫码）
- 无法从URL获取token
- 无法获取cookie
- 重新登录失败
- 认证信息不完整 