# WZ内容管理系统 - 故障排查指南

## 目录

- [常见问题快速诊断](#常见问题快速诊断)
- [数据库相关问题](#数据库相关问题)
- [采集功能问题](#采集功能问题)
- [Web界面问题](#web界面问题)
- [系统性能问题](#系统性能问题)
- [网络连接问题](#网络连接问题)
- [权限和安全问题](#权限和安全问题)
- [日志分析](#日志分析)
- [紧急恢复流程](#紧急恢复流程)

## 常见问题快速诊断

### 系统健康检查脚本

```bash
#!/bin/bash
# health_check.sh - 系统健康检查

echo "=== WZ系统健康检查 ==="

# 1. 检查Python环境
echo "1. Python环境检查..."
python3 --version
which python3

# 2. 检查虚拟环境
if [ -d "venv" ]; then
    echo "✅ 虚拟环境存在"
    source venv/bin/activate
    pip list | grep -E "(flask|mysql|beautifulsoup4|drissionpage)"
else
    echo "❌ 虚拟环境不存在"
fi

# 3. 检查数据库连接
echo "2. 数据库连接检查..."
python3 -c "
from core.database import get_db_manager
try:
    db = get_db_manager()
    if db.connect():
        print('✅ 数据库连接成功')
        db.disconnect()
    else:
        print('❌ 数据库连接失败')
except Exception as e:
    print(f'❌ 数据库连接异常: {e}')
"

# 4. 检查Chrome浏览器
echo "3. Chrome浏览器检查..."
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome已安装: $(google-chrome --version)"
    google-chrome --headless --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Chrome运行正常"
    else
        echo "❌ Chrome运行异常"
    fi
else
    echo "❌ Chrome未安装"
fi

# 5. 检查系统资源
echo "4. 系统资源检查..."
echo "内存使用情况:"
free -h
echo "磁盘使用情况:"
df -h | grep -E "(/$|/opt)"

# 6. 检查网络连接
echo "5. 网络连接检查..."
ping -c 1 google.com > /dev/null 2>&1 && echo "✅ 外网连接正常" || echo "❌ 外网连接异常"

# 7. 检查服务状态
echo "6. 服务状态检查..."
if systemctl is-active --quiet wz-web.service; then
    echo "✅ WZ Web服务运行中"
else
    echo "❌ WZ Web服务未运行"
fi

echo "=== 检查完成 ==="
```

### 快速问题定位

| 症状 | 可能原因 | 快速检查命令 |
|------|----------|--------------|
| 无法访问Web界面 | 服务未启动/端口被占用 | `sudo systemctl status wz-web.service` |
| 数据库连接失败 | MySQL服务停止/配置错误 | `sudo systemctl status mysql` |
| 采集功能异常 | Chrome问题/网络问题 | `google-chrome --version` |
| 内存不足 | 系统资源耗尽 | `free -h && htop` |
| 磁盘空间不足 | 日志文件过大 | `df -h && du -sh wz/logs/` |

## 数据库相关问题

### 问题1: 数据库连接失败

**错误信息**:
```
ERROR - 数据库连接失败: (2003, "Can't connect to MySQL server on '140.238.201.162' (10061)")
```

**诊断步骤**:
```bash
# 1. 检查MySQL服务状态
sudo systemctl status mysql

# 2. 检查MySQL进程
ps aux | grep mysql

# 3. 检查端口监听
sudo netstat -tulpn | grep :3306

# 4. 测试连接
mysql -h 140.238.201.162 -u cj -p -e "SELECT 1;"
```

**解决方案**:
```bash
# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 如果是远程连接问题，检查防火墙
sudo ufw status
sudo firewall-cmd --list-ports

# 检查MySQL配置
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
# 确保 bind-address = 0.0.0.0 或注释掉该行

# 重启MySQL
sudo systemctl restart mysql
```

### 问题2: 数据库权限错误

**错误信息**:
```
ERROR - (1045, "Access denied for user 'cj'@'localhost' (using password: YES)")
```

**解决方案**:
```bash
# 重置用户密码
mysql -u root -p
```

```sql
-- 重新创建用户
DROP USER IF EXISTS 'cj'@'localhost';
CREATE USER 'cj'@'localhost' IDENTIFIED BY 'new_password';
GRANT ALL PRIVILEGES ON cj.* TO 'cj'@'localhost';
FLUSH PRIVILEGES;
```

```bash
# 更新配置文件
nano wz/config/config.json
# 修改 "password": "new_password"
```

### 问题3: 数据库表不存在

**错误信息**:
```
ERROR - (1146, "Table 'cj.articles' doesn't exist")
```

**解决方案**:
```bash
# 重新初始化数据库
cd wz
mysql -u cj -p cj < sql/001_unified_database_schema.sql

# 如果有旧数据需要迁移
python scripts/migrate_database.py
```

### 问题4: 数据库连接数过多

**错误信息**:
```
ERROR - (1040, "Too many connections")
```

**解决方案**:
```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';

-- 查看最大连接数限制
SHOW VARIABLES LIKE 'max_connections';

-- 临时增加连接数限制
SET GLOBAL max_connections = 200;

-- 永久修改（需要重启MySQL）
-- 编辑 /etc/mysql/mysql.conf.d/mysqld.cnf
-- 添加: max_connections = 200
```

```bash
# 检查并关闭空闲连接
mysql -u root -p -e "SHOW PROCESSLIST;" | grep Sleep
mysql -u root -p -e "KILL <connection_id>;"
```

## 采集功能问题

### 问题1: Chrome浏览器启动失败

**错误信息**:
```
ERROR - Chrome浏览器启动失败: Message: unknown error: Chrome failed to start
```

**诊断步骤**:
```bash
# 1. 检查Chrome安装
google-chrome --version

# 2. 检查Chrome依赖
ldd $(which google-chrome) | grep "not found"

# 3. 测试Chrome启动
google-chrome --headless --no-sandbox --disable-dev-shm-usage --version
```

**解决方案**:
```bash
# Ubuntu/Debian: 安装缺失依赖
sudo apt install -y \
    libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 \
    libasound2 libatspi2.0-0 libgtk-3-0

# CentOS/RHEL: 安装缺失依赖
sudo yum install -y \
    nss atk at-spi2-atk gtk3 cups-libs libdrm libxkbcommon \
    libxcomposite libxdamage libxrandr libgbm libxss alsa-lib

# 设置显示环境（无头服务器）
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# 修改Chrome启动参数
# 编辑 wz/cfcj/core/browser_manager.py
# 添加更多启动参数：
# --no-sandbox --disable-dev-shm-usage --disable-gpu --remote-debugging-port=9222
```

### 问题2: 网站采集失败

**错误信息**:
```
ERROR - 文章采集失败: 不支持的站点: example.com
```

**诊断步骤**:
```bash
# 1. 测试网站连接
curl -I "https://example.com/article"

# 2. 检查站点配置
python wz/cfcj/main.py --test-connection "https://example.com/article"

# 3. 使用详细日志
python wz/cfcj/main.py "https://example.com/article" --verbose
```

**解决方案**:
```bash
# 1. 添加站点支持
# 编辑 wz/cfcj/data/cfcj_config.json
# 添加新站点配置

# 2. 使用通用提取器
python wz/cfcj/main.py "https://example.com/article" --force-generic

# 3. 检查反爬虫机制
# 增加请求延迟
python main_integrated.py config --set-key "cfcj.request_delay" --set-value "5"
```

### 问题3: 微信登录失效

**错误信息**:
```
WARNING - 微信登录状态无效，请先登录
```

**解决方案**:
```bash
# 1. 清除旧的认证文件
rm wz/data/id_info.json

# 2. 重新登录
cd wz/wechat_mp_auth
python auth.py --login

# 3. 验证登录状态
python auth.py --check

# 4. 如果仍然失败，检查网络和微信平台状态
curl -I "https://mp.weixin.qq.com"
```

### 问题4: 采集内容为空

**错误信息**:
```
WARNING - 采集到的内容为空或过短
```

**诊断步骤**:
```bash
# 1. 手动测试URL
python wz/cfcj/main.py "https://example.com/article" --debug

# 2. 检查页面结构
curl -s "https://example.com/article" | grep -i "content\|article"

# 3. 检查JavaScript渲染
python -c "
from cfcj.core.browser_manager import BrowserManager
browser = BrowserManager()
browser.get('https://example.com/article')
print(browser.page_source[:1000])
"
```

**解决方案**:
```bash
# 1. 增加页面加载等待时间
python main_integrated.py config --set-key "cfcj.page_load_timeout" --set-value "90"

# 2. 更新内容提取规则
# 编辑 wz/cfcj/core/multi_site_extractor.py

# 3. 使用备用提取策略
python wz/cfcj/main.py "https://example.com/article" --fallback-extraction
```

## Web界面问题

### 问题1: 无法访问Web界面

**错误信息**:
```
curl: (7) Failed to connect to localhost port 5000: Connection refused
```

**诊断步骤**:
```bash
# 1. 检查服务状态
sudo systemctl status wz-web.service

# 2. 检查端口占用
sudo netstat -tulpn | grep :5000

# 3. 检查进程
ps aux | grep "python.*app.py"

# 4. 查看服务日志
sudo journalctl -u wz-web.service -f
```

**解决方案**:
```bash
# 1. 启动服务
sudo systemctl start wz-web.service

# 2. 如果端口被占用，修改配置
python main_integrated.py config --set-key "web.port" --set-value "5001"

# 3. 手动启动（调试模式）
cd wz/YE
python app.py

# 4. 检查防火墙
sudo ufw allow 5000
sudo firewall-cmd --add-port=5000/tcp --permanent
```

### 问题2: Web界面加载缓慢

**诊断步骤**:
```bash
# 1. 检查系统资源
htop
iotop

# 2. 检查数据库查询性能
mysql -u cj -p cj -e "SHOW PROCESSLIST;"

# 3. 分析Web访问日志
tail -f wz/logs/flask_app.log
```

**解决方案**:
```bash
# 1. 优化数据库查询
mysql -u cj -p cj -e "
ANALYZE TABLE articles;
OPTIMIZE TABLE articles;
"

# 2. 增加数据库连接池
python main_integrated.py config --set-key "database.pool_size" --set-value "20"

# 3. 启用缓存
# 编辑 wz/YE/app.py，添加缓存配置
```

### 问题3: 静态文件404错误

**解决方案**:
```bash
# 1. 检查静态文件路径
ls -la wz/YE/static/

# 2. 修复权限
chmod -R 644 wz/YE/static/
chmod 755 wz/YE/static/

# 3. 检查Flask配置
# 确保 wz/YE/app.py 中静态文件路径正确
```

## 系统性能问题

### 问题1: 内存使用过高

**诊断步骤**:
```bash
# 1. 查看内存使用
free -h
ps aux --sort=-%mem | head -10

# 2. 查看Python进程内存
ps aux | grep python | awk '{print $2, $4, $11}' | sort -k2 -nr

# 3. 使用内存分析工具
pip install memory_profiler
python -m memory_profiler wz/main_integrated.py status
```

**解决方案**:
```bash
# 1. 减少批处理大小
python main_integrated.py config --set-key "cfcj.batch_size" --set-value "2"
python main_integrated.py config --set-key "wechat.batch_size" --set-value "5"

# 2. 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. 优化数据库连接池
python main_integrated.py config --set-key "database.pool_size" --set-value "5"

# 4. 定期重启服务
# 添加到crontab: 0 3 * * * sudo systemctl restart wz-web.service
```

### 问题2: CPU使用率过高

**诊断步骤**:
```bash
# 1. 查看CPU使用情况
htop
top -p $(pgrep -f python)

# 2. 分析进程
strace -p <python_pid>
```

**解决方案**:
```bash
# 1. 增加请求间隔
python main_integrated.py config --set-key "cfcj.request_delay" --set-value "3"

# 2. 限制并发数
python main_integrated.py config --set-key "cfcj.batch_size" --set-value "1"

# 3. 使用nice降低进程优先级
nice -n 10 python main_integrated.py crawl-db
```

### 问题3: 磁盘空间不足

**诊断步骤**:
```bash
# 1. 查看磁盘使用
df -h
du -sh wz/logs/
du -sh wz/data/

# 2. 查找大文件
find wz/ -type f -size +100M -exec ls -lh {} \;
```

**解决方案**:
```bash
# 1. 清理日志文件
find wz/logs/ -name "*.log.*" -mtime +7 -delete
find wz/logs/ -name "*.log" -size +100M -exec truncate -s 50M {} \;

# 2. 清理临时文件
rm -rf wz/temp/*
find /tmp -name "wz_*" -mtime +1 -delete

# 3. 压缩旧日志
gzip wz/logs/*.log.1

# 4. 设置日志轮转
# 编辑 /etc/logrotate.d/wz-project
```

## 网络连接问题

### 问题1: 网络超时

**错误信息**:
```
ERROR - 请求超时: HTTPSConnectionPool(host='example.com', port=443): Read timed out.
```

**解决方案**:
```bash
# 1. 增加超时时间
python main_integrated.py config --set-key "cfcj.timeout" --set-value "60"

# 2. 检查网络连接
ping example.com
traceroute example.com

# 3. 使用代理（如果需要）
# 编辑配置文件，添加代理设置
```

### 问题2: DNS解析失败

**解决方案**:
```bash
# 1. 检查DNS设置
cat /etc/resolv.conf

# 2. 测试DNS解析
nslookup example.com
dig example.com

# 3. 更换DNS服务器
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
```

### 问题3: SSL证书错误

**错误信息**:
```
ERROR - SSL: CERTIFICATE_VERIFY_FAILED
```

**解决方案**:
```bash
# 1. 更新CA证书
sudo apt update && sudo apt install ca-certificates

# 2. 临时禁用SSL验证（不推荐用于生产环境）
export PYTHONHTTPSVERIFY=0

# 3. 配置自定义证书路径
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

## 权限和安全问题

### 问题1: 文件权限错误

**错误信息**:
```
PermissionError: [Errno 13] Permission denied: '/path/to/wz/logs/app.log'
```

**解决方案**:
```bash
# 1. 修复文件权限
sudo chown -R $USER:$USER /opt/wz-project/
chmod -R 755 /opt/wz-project/
chmod -R 644 /opt/wz-project/wz/config/

# 2. 修复日志目录权限
chmod 755 /opt/wz-project/wz/logs/
chmod 644 /opt/wz-project/wz/logs/*.log

# 3. 设置正确的服务用户
sudo systemctl edit wz-web.service
# 添加: [Service]
#       User=your_username
#       Group=your_group
```

### 问题2: 数据库安全配置

```bash
# 1. 修改默认密码
mysql -u root -p
ALTER USER 'cj'@'localhost' IDENTIFIED BY 'strong_password_here';

# 2. 限制数据库访问
# 编辑 /etc/mysql/mysql.conf.d/mysqld.cnf
# bind-address = 127.0.0.1

# 3. 启用防火墙
sudo ufw enable
sudo ufw allow from 127.0.0.1 to any port 3306
```

## 日志分析

### 日志文件位置

```bash
# 主要日志文件
wz/logs/wz_integrated.log      # 集成系统日志
wz/logs/flask_app.log          # Web应用日志
wz/logs/cfcj_crawler.log       # 采集器日志
wz/logs/wechat_auth.log        # 微信认证日志

# 系统日志
/var/log/syslog                # 系统日志
sudo journalctl -u wz-web.service  # 服务日志
```

### 常用日志分析命令

```bash
# 1. 查看最新错误
grep "ERROR" wz/logs/wz_integrated.log | tail -20

# 2. 统计错误类型
grep "ERROR" wz/logs/wz_integrated.log | cut -d'-' -f4 | sort | uniq -c

# 3. 查看特定时间段日志
grep "2025-07-09 14:" wz/logs/wz_integrated.log

# 4. 实时监控日志
tail -f wz/logs/wz_integrated.log | grep -E "(ERROR|WARNING)"

# 5. 分析采集成功率
grep -E "(采集成功|采集失败)" wz/logs/wz_integrated.log | \
awk '{if(/成功/) success++; else fail++} END {print "成功:", success, "失败:", fail}'

# 6. 查看内存使用趋势
grep "内存使用" wz/logs/wz_integrated.log | tail -50
```

### 日志级别调整

```bash
# 临时启用调试日志
python main_integrated.py --verbose crawl-db

# 永久修改日志级别
python main_integrated.py config --set-key "system.log_level" --set-value "DEBUG"
```

## 紧急恢复流程

### 系统完全无响应

```bash
#!/bin/bash
# emergency_recovery.sh

echo "=== 紧急恢复流程 ==="

# 1. 停止所有相关服务
sudo systemctl stop wz-web.service
pkill -f "python.*main_integrated.py"
pkill -f "python.*app.py"

# 2. 检查系统资源
echo "检查系统资源..."
free -h
df -h
ps aux --sort=-%cpu | head -10

# 3. 清理临时文件和进程
rm -rf /tmp/wz_*
find /opt/wz-project/wz/temp -type f -delete

# 4. 重启数据库
sudo systemctl restart mysql
sleep 5

# 5. 检查数据库状态
mysql -u cj -p -e "SELECT 1;" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 数据库恢复正常"
else
    echo "❌ 数据库仍有问题"
    exit 1
fi

# 6. 重启Web服务
sudo systemctl start wz-web.service
sleep 10

# 7. 验证恢复
curl -f http://localhost:5000/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 系统恢复成功"
else
    echo "❌ 系统恢复失败，需要手动检查"
fi

echo "=== 恢复完成 ==="
```

### 数据损坏恢复

```bash
# 1. 停止所有服务
sudo systemctl stop wz-web.service

# 2. 备份当前状态
mysqldump -u cj -p cj > emergency_backup_$(date +%Y%m%d_%H%M%S).sql

# 3. 检查数据完整性
mysql -u cj -p cj -e "CHECK TABLE articles, publish_tasks, system_config;"

# 4. 修复损坏的表
mysql -u cj -p cj -e "REPAIR TABLE articles;"

# 5. 如果修复失败，从备份恢复
# 选择最近的备份文件
ls -la /backups/backup_*.sql | tail -5
mysql -u cj -p cj < /backups/backup_20250709_020000.sql

# 6. 验证数据完整性
python wz/scripts/verify_data_integrity.py

# 7. 重启服务
sudo systemctl start wz-web.service
```

### 配置文件损坏恢复

```bash
# 1. 恢复默认配置
cd /opt/wz-project/wz
cp config/config.json.template config/config.json

# 2. 重新运行配置迁移
python scripts/migrate_config.py

# 3. 手动调整关键配置
nano config/config.json
# 修改数据库连接信息等

# 4. 验证配置
python -c "from core.config import get_config; print('配置加载成功' if get_config() else '配置加载失败')"
```

---

## 获取技术支持

如果以上解决方案都无法解决问题，请：

1. **收集诊断信息**:
   ```bash
   # 运行诊断脚本
   bash health_check.sh > diagnostic_report.txt 2>&1
   
   # 收集日志
   tar -czf logs_$(date +%Y%m%d).tar.gz wz/logs/
   ```

2. **联系技术支持**:
   - 邮箱: support@example.com
   - 提供: 错误信息、诊断报告、系统环境信息

3. **社区支持**:
   - GitHub Issues: 提交bug报告
   - 文档Wiki: 查看最新解决方案

---

*故障排查指南最后更新: 2025-07-09*
