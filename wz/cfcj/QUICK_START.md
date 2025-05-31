# CFCJ 快速开始指南

## 1. 安装依赖

```bash
# 进入项目目录
cd wz/cfcj

# 方法1: 使用安装脚本（推荐）
python install_deps.py

# 方法2: 手动安装
pip install beautifulsoup4 lxml requests undetected-chromedriver selenium DrissionPage
```

## 2. 基础测试

```bash
# 运行基础功能测试
python test_basic.py

# 如果看到 "所有测试通过！" 说明安装成功
```

## 3. 快速使用

### 方法1: Python代码
```python
from wz.cfcj.api import CFCJAPI

# 创建API实例
api = CFCJAPI()

# 采集目标文章
result = api.crawl_article("https://linux.do/t/topic/690688/48")

# 查看结果
print(f"标题: {result['title']}")
print(f"内容长度: {len(result['content'])} 字符")
```

### 方法2: 命令行
```bash
# 采集单个URL
python main.py https://linux.do/t/topic/690688/48

# 显示浏览器窗口（便于观察CF验证过程）
python main.py --no-headless https://linux.do/t/topic/690688/48

# 测试连接
python main.py --test-connection https://linux.do/

# 交互模式
python main.py
```

### 方法3: 演示脚本
```bash
# 运行完整演示
python demo.py
```

## 4. 针对linux.do的专项测试

```bash
# 运行linux.do专项测试
python tests/test_linux_do.py

# 手动测试（显示浏览器）
python tests/test_linux_do.py --manual
```

## 5. 常见问题解决

### Chrome浏览器问题
```bash
# 确保Chrome已安装
google-chrome --version

# Windows用户确保Chrome在PATH中
```

### 依赖安装问题
```bash
# 升级pip
python -m pip install --upgrade pip

# 重新安装依赖
pip install --force-reinstall beautifulsoup4 lxml undetected-chromedriver
```

### Cloudflare检测问题
- 增加等待时间：使用 `--no-headless` 参数观察CF验证过程
- 检查网络连接：确保能正常访问目标网站
- 重试机制：程序会自动重试3次

## 6. 配置调整

创建或编辑 `data/cfcj_config.json`：
```json
{
  "browser": {
    "headless": false,
    "timeout": 60
  },
  "crawler": {
    "max_retries": 5,
    "cf_wait_time": 20
  }
}
```

## 7. 集成到其他项目

```python
# 在其他项目中使用
import sys
sys.path.append('path/to/wz')

from wz.cfcj.api import crawl_single_article

# 简单调用
result = crawl_single_article("https://linux.do/t/topic/690688/48")
```

## 8. 需要登录的网站

```python
from wz.cfcj.api import CFCJAPI

api = CFCJAPI()

# 登录凭据
login_credentials = {
    'username': 'your_username',
    'password': 'your_password',
    'login_url': 'https://example.com/login'
}

# 采集需要登录的内容
result = api.crawl_article(
    "https://example.com/protected-content",
    login_required=True,
    login_credentials=login_credentials
)
```

## 9. 批量采集

```python
from wz.cfcj.api import CFCJAPI

api = CFCJAPI()

urls = [
    "https://linux.do/t/topic/690688/48",
    "https://linux.do/",
    # 更多URL...
]

result = api.crawl_articles_batch(urls, batch_size=3)
print(f"成功: {result['success_count']}, 失败: {result['failed_count']}")
```

## 10. 故障排除

### 查看详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 然后运行你的代码
```

### 命令行详细输出
```bash
python main.py --verbose --no-headless <url>
```

### 检查模块状态
```bash
python -c "from wz.cfcj.api import CFCJAPI; print('模块加载成功')"
```

## 成功标志

如果你看到以下输出，说明CFCJ工作正常：

```
采集成功!
标题: [文章标题]
作者: [作者名]
发布时间: [时间]
内容长度: [数字] 字符
字数统计: [数字]
结果已保存到: [文件名]
```

## 下一步

- 查看 `README.md` 了解详细功能
- 查看 `PROJECT_SUMMARY.md` 了解项目架构
- 根据需要修改配置文件
- 集成到你的项目中

祝使用愉快！🎉
