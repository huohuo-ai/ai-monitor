import schedule
import time
import threading
import requests
from datetime import datetime
import sys
import os

# 添加当前目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database

# 初始化数据库
db = Database()

# 测试任务执行函数
def run_test_task(task):
    print(f"[{datetime.now()}] 开始执行任务: {task[1]} (ID: {task[0]})")
    
    # 构建测试请求数据
    test_data = {
        "model_provider": task[2],
        "model_url": task[3],
        "api_key": task[4],
        "test_count": task[5]
    }
    
    try:
        # 调用本地测试API
        response = requests.post(
            'http://localhost:5000/test_model',
            headers={'Content-Type': 'application/json'},
            json=test_data,
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            result = response.json()
            # 保存测试结果到数据库
            db.add_test_result(task[0], result)
            print(f"[{datetime.now()}] 任务 {task[0]} 执行成功，保存结果")
        else:
            print(f"[{datetime.now()}] 任务 {task[0]} 执行失败: API返回状态码 {response.status_code}")
            
    except Exception as e:
        print(f"[{datetime.now()}] 任务 {task[0]} 执行异常: {str(e)}")

# 加载所有活跃任务到调度器
def load_tasks():
    # 清除所有现有任务
    schedule.clear()
    
    # 获取所有活跃任务
    tasks = db.get_active_tasks()
    print(f"[{datetime.now()}] 加载 {len(tasks)} 个活跃任务到调度器")
    
    for task in tasks:
        # 为每个任务设置定时执行
        schedule.every(task[7]).minutes.do(run_test_task, task)

# 启动调度器
# 注意：在实际生产环境中，应该使用更可靠的任务调度系统（如Celery）
def start_scheduler():
    print(f"[{datetime.now()}] 启动任务调度器")
    load_tasks()
    
    # 定时重新加载任务，支持动态添加/修改/删除任务
    schedule.every(5).minutes.do(load_tasks)
    
    # 运行调度器
    while True:
        schedule.run_pending()
        time.sleep(1)

# 创建并启动调度器线程
def start_scheduler_thread():
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    print("任务调度器线程已启动")
