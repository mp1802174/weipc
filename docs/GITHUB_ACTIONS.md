# WZ系统 GitHub Actions 自动化部署指南

## 📋 概述

本指南介绍如何在GitHub Actions中部署和运行WZ系统的自动化工作流，实现完全云端的内容采集和发布自动化。

## 🚀 功能特性

- ✅ **完全云端运行**：无需本地服务器，基于GitHub Actions
- ✅ **定时自动执行**：支持cron定时任务
- ✅ **手动触发**：支持手动执行和参数配置
- ✅ **Headless模式**：无界面浏览器，适合服务器环境
- ✅ **日志管理**：自动保存执行日志和artifacts
- ✅ **错误处理**：完善的异常处理和重试机制

## 🔧 配置步骤

### 1. 设置GitHub Secrets

在GitHub仓库的 `Settings > Secrets and variables > Actions` 中添加以下secrets：

#### 数据库配置
```
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_NAME=your_database_name
```

#### 论坛数据库配置
```
FORUM_DB_HOST=your_forum_database_host
FORUM_DB_PORT=3306
FORUM_DB_USER=your_forum_database_user
FORUM_DB_PASSWORD=your_forum_database_password
FORUM_DB_NAME=your_forum_database_name
```

### 2. 工作流配置

工作流配置文件位于：`.github/workflows/wz-automation.yml`

#### 定时执行
默认每6小时执行一次：
```yaml
schedule:
  - cron: '0 */6 * * *'
```

#### 手动执行
支持以下参数：
- `link_limit`: 链接采集限制（默认：3）
- `content_limit`: 内容采集限制（默认：50）
- `publish_limit`: 论坛发布限制（默认：50）
- `steps`: 执行步骤（默认：link_crawl,content_crawl,forum_publish）

## 📊 执行流程

### 1. 环境准备
- 安装Ubuntu系统依赖
- 安装Chrome浏览器和ChromeDriver
- 安装Python依赖包
- 创建配置文件

### 2. 执行步骤
1. **微信链接采集**：从配置的公众号采集最新文章链接
2. **内容采集**：提取文章完整内容
3. **论坛发布**：自动发布到Discuz论坛

### 3. 结果输出
- 执行日志保存为artifacts
- 成功/失败状态通知
- 详细的执行统计信息

## 🎯 使用方法

### 手动触发
1. 进入GitHub仓库的 `Actions` 页面
2. 选择 `WZ Content Automation` 工作流
3. 点击 `Run workflow`
4. 配置执行参数（可选）
5. 点击 `Run workflow` 开始执行

### 查看结果
1. 在 `Actions` 页面查看执行状态
2. 点击具体的执行记录查看详细日志
3. 下载artifacts获取完整日志文件

## ⚙️ 高级配置

### 自定义执行频率
修改 `.github/workflows/wz-automation.yml` 中的cron表达式：
```yaml
schedule:
  - cron: '0 */3 * * *'  # 每3小时执行一次
  - cron: '0 9,21 * * *'  # 每天9点和21点执行
```

### 自定义执行步骤
可以只执行特定步骤：
- `link_crawl`: 仅链接采集
- `content_crawl`: 仅内容采集
- `forum_publish`: 仅论坛发布
- `link_crawl,content_crawl`: 链接采集+内容采集

### 环境变量配置
在工作流中可以设置额外的环境变量：
```yaml
env:
  PYTHONPATH: ${{ github.workspace }}
  PYTHONIOENCODING: utf-8
  CUSTOM_CONFIG: production
```

## 🔍 故障排除

### 常见问题

#### 1. 数据库连接失败
- 检查Secrets中的数据库配置是否正确
- 确认数据库服务器允许GitHub Actions的IP访问
- 检查数据库用户权限

#### 2. Chrome浏览器问题
- 工作流会自动安装Chrome和ChromeDriver
- 如果遇到版本兼容问题，检查安装脚本

#### 3. 内容采集失败
- 检查目标网站是否有反爬虫机制
- 查看详细日志了解具体错误原因
- 考虑调整请求间隔和重试次数

#### 4. 论坛发布失败
- 检查论坛数据库配置
- 确认论坛数据库结构是否匹配
- 检查发布权限设置

### 日志分析
执行日志包含以下信息：
- 环境检查结果
- 各步骤执行状态
- 错误详情和堆栈跟踪
- 性能统计信息

## 📈 监控和优化

### 性能监控
- 执行时间统计
- 成功率监控
- 资源使用情况

### 优化建议
1. **合理设置限制**：避免单次处理过多内容
2. **调整执行频率**：根据内容更新频率设置
3. **监控执行状态**：定期检查执行日志
4. **优化网络请求**：合理设置超时和重试

## 🔒 安全注意事项

1. **Secrets管理**：
   - 不要在代码中硬编码敏感信息
   - 定期更新数据库密码
   - 使用最小权限原则

2. **网络安全**：
   - 确保数据库服务器安全配置
   - 考虑使用VPN或专用网络
   - 监控异常访问

3. **数据保护**：
   - 定期备份重要数据
   - 设置合理的数据保留策略
   - 遵守相关法律法规

## 📞 支持

如果遇到问题，请：
1. 查看GitHub Actions执行日志
2. 检查本文档的故障排除部分
3. 提交Issue描述具体问题
4. 提供相关的日志信息

---

**注意**：GitHub Actions有使用限制，请合理安排执行频率，避免超出免费额度。
