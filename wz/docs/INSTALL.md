# WZ内容管理系统 - 安装指南

## 快速安装

### 一键安装脚本（推荐）

```bash
#!/bin/bash
# install.sh - WZ系统一键安装脚本

set -e

echo "=== WZ内容管理系统安装程序 ==="

# 检查系统
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "✅ 检测到Linux系统"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ 检测到macOS系统"
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    exit 1
fi

# 检查Python版本
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python版本检查通过: $python_version"
else
    echo "❌ Python版本过低，需要3.8或更高版本，当前版本: $python_version"
    exit 1
fi

# 安装系统依赖
echo "📦 安装系统依赖..."
if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv mysql-server wget gnupg
    
    # 安装Chrome
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
    
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    sudo yum install -y python3-pip mysql-server wget
    
    # 安装Chrome
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
    sudo yum localinstall -y google-chrome-stable_current_x86_64.rpm
    rm google-chrome-stable_current_x86_64.rpm
    
else
    echo "❌ 不支持的包管理器"
    exit 1
fi

# 创建项目目录
PROJECT_DIR="/opt/wz-project"
echo "📁 创建项目目录: $PROJECT_DIR"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 复制项目文件
echo "📋 复制项目文件..."
cp -r . $PROJECT_DIR/

# 创建虚拟环境
echo "🐍 创建Python虚拟环境..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
echo "📦 安装Python依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置MySQL
echo "🗄️ 配置MySQL数据库..."
sudo systemctl start mysql
sudo systemctl enable mysql

# 创建数据库和用户
mysql -u root -p << EOF
CREATE DATABASE IF NOT EXISTS cj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'cj'@'localhost' IDENTIFIED BY 'wz_default_password';
GRANT ALL PRIVILEGES ON cj.* TO 'cj'@'localhost';
FLUSH PRIVILEGES;
EOF

# 初始化数据库
echo "🏗️ 初始化数据库..."
mysql -u cj -pwz_default_password cj < wz/sql/001_unified_database_schema.sql

# 配置系统
echo "⚙️ 配置系统..."
cd wz
cp config/config.json.template config/config.json

# 修改配置文件中的数据库密码
sed -i 's/"password": "760516"/"password": "wz_default_password"/' config/config.json

# 运行配置迁移
python scripts/migrate_config.py

# 创建系统服务
echo "🔧 创建系统服务..."
sudo tee /etc/systemd/system/wz-web.service > /dev/null << EOF
[Unit]
Description=WZ Content Management System Web Service
After=network.target mysql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/wz/YE
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable wz-web.service
sudo systemctl start wz-web.service

# 运行测试
echo "🧪 运行系统测试..."
cd $PROJECT_DIR/wz
python test_integration.py

echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 安装信息:"
echo "  项目目录: $PROJECT_DIR"
echo "  Web界面: http://localhost:5000"
echo "  数据库: localhost:3306/cj"
echo "  用户名: cj"
echo "  密码: wz_default_password"
echo ""
echo "🔧 管理命令:"
echo "  查看状态: sudo systemctl status wz-web.service"
echo "  启动服务: sudo systemctl start wz-web.service"
echo "  停止服务: sudo systemctl stop wz-web.service"
echo "  查看日志: sudo journalctl -u wz-web.service -f"
echo ""
echo "📖 更多信息请查看文档: $PROJECT_DIR/wz/docs/README.md"
```

### 手动安装步骤

如果一键安装脚本不适用，可以按照以下步骤手动安装：

#### 1. 系统要求检查

```bash
# 检查Python版本
python3 --version  # 需要3.8+

# 检查可用内存
free -h  # 建议4GB+

# 检查磁盘空间
df -h  # 建议20GB+
```

#### 2. 安装系统依赖

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv mysql-server wget gnupg curl

# 安装Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable
```

**CentOS/RHEL:**
```bash
sudo yum install -y python3 python3-pip mysql-server wget curl

# 安装Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
sudo yum localinstall -y google-chrome-stable_current_x86_64.rpm
```

#### 3. 配置MySQL

```bash
# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全配置（可选）
sudo mysql_secure_installation

# 创建数据库和用户
mysql -u root -p
```

```sql
CREATE DATABASE cj CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'cj'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON cj.* TO 'cj'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

#### 4. 部署项目

```bash
# 创建项目目录
sudo mkdir -p /opt/wz-project
sudo chown $USER:$USER /opt/wz-project

# 复制项目文件
cp -r /path/to/source/* /opt/wz-project/

# 进入项目目录
cd /opt/wz-project

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. 初始化数据库

```bash
cd /opt/wz-project/wz

# 执行数据库初始化
mysql -u cj -p cj < sql/001_unified_database_schema.sql
```

#### 6. 配置系统

```bash
# 复制配置模板
cp config/config.json.template config/config.json

# 编辑配置文件
nano config/config.json
```

修改以下关键配置：
- 数据库连接信息
- Web服务密钥
- 日志路径

#### 7. 运行配置迁移

```bash
python scripts/migrate_config.py
```

#### 8. 测试安装

```bash
# 运行集成测试
python test_integration.py

# 检查系统状态
python main_integrated.py status
```

#### 9. 配置系统服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/wz-web.service
```

```ini
[Unit]
Description=WZ Content Management System Web Service
After=network.target mysql.service

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/wz-project/wz/YE
Environment=PATH=/opt/wz-project/venv/bin
ExecStart=/opt/wz-project/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable wz-web.service
sudo systemctl start wz-web.service
sudo systemctl status wz-web.service
```

## 验证安装

### 1. 基本功能测试

```bash
cd /opt/wz-project/wz

# 检查系统状态
python main_integrated.py status

# 测试数据库连接
python -c "from core.database import get_db_manager; db = get_db_manager(); print('✅ 数据库连接成功' if db.connect() else '❌ 数据库连接失败')"

# 测试Web界面
curl -f http://localhost:5000/ && echo "✅ Web界面正常" || echo "❌ Web界面异常"
```

### 2. 功能验证

```bash
# 测试URL采集
python main_integrated.py crawl-urls "https://httpbin.org/html" --source-type external

# 查看采集结果
python main_integrated.py status
```

### 3. 性能测试

```bash
# 检查系统资源
htop

# 检查数据库性能
mysql -u cj -p cj -e "SHOW STATUS LIKE 'Threads_connected';"
```

## 常见安装问题

### 1. Chrome安装失败

**问题**: Chrome浏览器安装失败或无法启动

**解决方案**:
```bash
# 安装缺失依赖
sudo apt install -y libnss3-dev libatk-bridge2.0-dev libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2

# 测试Chrome
google-chrome --version
google-chrome --headless --no-sandbox --disable-dev-shm-usage --dump-dom https://www.google.com > /dev/null
```

### 2. MySQL连接问题

**问题**: 无法连接到MySQL数据库

**解决方案**:
```bash
# 检查MySQL状态
sudo systemctl status mysql

# 重置MySQL密码
sudo mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'new_password';
FLUSH PRIVILEGES;
```

### 3. 权限问题

**问题**: 文件权限不足

**解决方案**:
```bash
# 修复项目权限
sudo chown -R $USER:$USER /opt/wz-project
chmod -R 755 /opt/wz-project
chmod -R 644 /opt/wz-project/wz/config/
```

### 4. 端口冲突

**问题**: 5000端口被占用

**解决方案**:
```bash
# 查看端口占用
sudo netstat -tulpn | grep :5000

# 修改配置文件中的端口
nano /opt/wz-project/wz/config/config.json
# 将 "port": 5000 改为 "port": 5001
```

## 卸载

如需卸载系统：

```bash
#!/bin/bash
# uninstall.sh - 卸载脚本

echo "=== WZ系统卸载程序 ==="

# 停止服务
sudo systemctl stop wz-web.service
sudo systemctl disable wz-web.service

# 删除服务文件
sudo rm -f /etc/systemd/system/wz-web.service
sudo systemctl daemon-reload

# 删除数据库（可选）
read -p "是否删除数据库？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mysql -u root -p -e "DROP DATABASE IF EXISTS cj; DROP USER IF EXISTS 'cj'@'localhost';"
    echo "✅ 数据库已删除"
fi

# 删除项目文件（可选）
read -p "是否删除项目文件？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo rm -rf /opt/wz-project
    echo "✅ 项目文件已删除"
fi

echo "🎯 卸载完成"
```

---

*安装指南最后更新: 2025-07-09*
