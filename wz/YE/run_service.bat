@echo off
echo 正在启动微信公众号文章抓取服务...
cd /d %~dp0
start /min python app.py
echo 服务已启动! 访问 http://localhost:5000 使用Web界面
echo 按任意键退出本窗口，服务将继续在后台运行...
pause > nul 