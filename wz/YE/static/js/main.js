// 微信公众号文章抓取工具前端交互脚本

document.addEventListener('DOMContentLoaded', function() {
    // 初始化Bootstrap工具提示
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // 加载遮罩层
    const loaderOverlay = document.getElementById('loaderOverlay');
    
    // 立即抓取表单提交处理
    const crawlForm = document.getElementById('crawlForm');
    if (crawlForm) {
        crawlForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 显示加载遮罩层
            loaderOverlay.style.display = 'flex';
            
            const formData = new FormData(crawlForm);
            
            fetch('/crawl', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示结果消息
                const resultDiv = document.getElementById('crawlResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = data.success ? 'alert alert-success' : 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = data.message;
                
                resultDiv.appendChild(alert);
                
                // 5秒后自动隐藏消息
                setTimeout(() => {
                    alert.classList.add('fade');
                    setTimeout(() => {
                        resultDiv.innerHTML = '';
                    }, 500);
                }, 5000);
            })
            .catch(error => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示错误消息
                const resultDiv = document.getElementById('crawlResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = '发生错误: ' + error.message;
                
                resultDiv.appendChild(alert);
            });
        });
    }
    
    // 更新凭证表单处理
    const credForm = document.getElementById('credForm');
    if (credForm) {
        credForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 显示加载遮罩层
            loaderOverlay.style.display = 'flex';
            
            fetch('/update_cred', {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示结果消息
                const resultDiv = document.getElementById('credResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = data.success ? 'alert alert-success' : 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = data.message;
                
                resultDiv.appendChild(alert);
            })
            .catch(error => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示错误消息
                const resultDiv = document.getElementById('credResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = '发生错误: ' + error.message;
                
                resultDiv.appendChild(alert);
            });
        });
    }
    
    // 定时任务表单处理
    const scheduleForm = document.getElementById('scheduleForm');
    if (scheduleForm) {
        // 切换定时类型时更新UI
        const scheduleType = document.getElementById('scheduleType');
        const daysGroup = document.getElementById('daysGroup');
        
        if (scheduleType && daysGroup) {
            scheduleType.addEventListener('change', function() {
                if (this.value === 'weekly') {
                    daysGroup.style.display = 'block';
                } else {
                    daysGroup.style.display = 'none';
                }
            });
        }
        
        // 表单提交
        scheduleForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 显示加载遮罩层
            loaderOverlay.style.display = 'flex';
            
            const formData = new FormData(scheduleForm);
            
            fetch('/schedule', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示结果消息
                const resultDiv = document.getElementById('scheduleResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = data.success ? 'alert alert-success' : 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = data.message;
                
                resultDiv.appendChild(alert);
                
                // 如果成功，刷新页面以显示新任务
                if (data.success) {
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                }
            })
            .catch(error => {
                // 隐藏加载遮罩层
                loaderOverlay.style.display = 'none';
                
                // 显示错误消息
                const resultDiv = document.getElementById('scheduleResult');
                resultDiv.innerHTML = '';
                
                const alert = document.createElement('div');
                alert.className = 'alert alert-danger';
                alert.setAttribute('role', 'alert');
                alert.textContent = '发生错误: ' + error.message;
                
                resultDiv.appendChild(alert);
            });
        });
    }
    
    // 删除定时任务处理
    const deleteButtons = document.querySelectorAll('.delete-schedule');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const jobId = this.getAttribute('data-id');
            
            if (confirm('确定要删除这个定时任务吗？')) {
                // 显示加载遮罩层
                loaderOverlay.style.display = 'flex';
                
                fetch('/delete_schedule', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'job_id=' + encodeURIComponent(jobId)
                })
                .then(response => response.json())
                .then(data => {
                    // 隐藏加载遮罩层
                    loaderOverlay.style.display = 'none';
                    
                    if (data.success) {
                        // 刷新页面以更新任务列表
                        window.location.reload();
                    } else {
                        alert('删除失败: ' + data.message);
                    }
                })
                .catch(error => {
                    // 隐藏加载遮罩层
                    loaderOverlay.style.display = 'none';
                    alert('发生错误: ' + error.message);
                });
            }
        });
    });
}); 