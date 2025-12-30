from flask import Flask, render_template, request, jsonify
import requests
import time
import numpy as np
import json
from database import db
from scheduler import start_scheduler_thread, load_tasks

app = Flask(__name__)

# 启动调度器线程
start_scheduler_thread()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test_model', methods=['POST'])
def test_model():
    data = request.json
    
    # 检查是否是多模型请求
    models = data.get('models')
    test_count = data.get('test_count', 10)  # 默认测试10次
    
    # 如果是单模型请求（兼容旧格式）
    if not models:
        model_provider = data.get('model_provider', 'custom')
        model_url = data.get('model_url')
        api_key = data.get('api_key')
        
        if not model_url or not api_key:
            return jsonify({'error': '模型URL和API Key不能为空'}), 400
        
        # 将单模型转换为多模型格式处理
        models = [{
            'model_provider': model_provider,
            'model_url': model_url,
            'api_key': api_key
        }]
    
    # 准备测试数据
    test_prompt = "Hello, how are you?"
    all_model_results = []
    
    # 遍历每个模型执行测试
    for model in models:
        model_provider = model.get('model_provider', 'custom')
        model_url = model.get('model_url')
        api_key = model.get('api_key')
        
        if not model_url or not api_key:
            continue  # 跳过无效模型配置
        
        results = []
        errors = 0
        
        # 执行多次测试
        for i in range(test_count):
            start_time = time.time()
            try:
                # 根据模型提供商设置模型名称和API路径
                model_map = {
                    'deepseek': 'deepseek-chat',
                    'openai': 'gpt-3.5-turbo',
                    'anthropic': 'claude-3-sonnet-20240229',
                    'custom': 'custom-model'
                }
                
                # 设置默认模型
                model_name = model_map.get(model_provider, 'custom-model')
                
                # 确保URL格式正确（添加完整路径，针对常见模型服务）
                api_url = model_url
                if model_provider == 'deepseek' and '/v1/chat/completions' not in api_url:
                    api_url = f"{api_url.rstrip('/')}/v1/chat/completions"
                elif model_provider == 'openai' and '/v1/chat/completions' not in api_url:
                    api_url = f"{api_url.rstrip('/')}/v1/chat/completions"
                elif model_provider == 'anthropic' and '/v1/messages' not in api_url:
                    api_url = f"{api_url.rstrip('/')}/v1/messages"
                
                # 检查是否有自定义请求
                custom_request = model.get('custom_request')
                if custom_request:
                    # 使用用户自定义的JSON请求
                    request_data = custom_request
                else:
                    # 使用默认请求格式
                    request_data = {
                        'model': model_name,
                        'messages': [{'role': 'user', 'content': test_prompt}],
                        'max_tokens': 50
                    }
                
                response = requests.post(
                    api_url,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json=request_data,
                    timeout=30
                )
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # 转换为毫秒
                
                if response.status_code == 200:
                    results.append(latency)
                else:
                    errors += 1
                    print(f"测试 {i+1} 失败: HTTP {response.status_code} ({api_url})")
            except requests.exceptions.RequestException as e:
                errors += 1
                print(f"测试 {i+1} 网络异常: {str(e)} ({api_url if 'api_url' in locals() else model_url})")
            except Exception as e:
                errors += 1
                print(f"测试 {i+1} 未知异常: {str(e)}")
        
        # 计算性能指标
        if results:
            avg_latency = np.mean(results)
            p90_latency = np.percentile(results, 90)
            p99_latency = np.percentile(results, 99)
            min_latency = np.min(results)
            max_latency = np.max(results)
        else:
            avg_latency = p90_latency = p99_latency = min_latency = max_latency = 0
        
        error_rate = errors / test_count * 100
        success_count = test_count - errors
        
        # 保存该模型的测试结果
        model_result = {
            'model_provider': model_provider,
            'total_tests': test_count,
            'success_count': success_count,
            'error_count': errors,
            'error_rate': round(error_rate, 2),
            'latency_stats': {
                'avg': round(avg_latency, 2),
                'p90': round(p90_latency, 2),
                'p99': round(p99_latency, 2),
                'min': round(min_latency, 2),
                'max': round(max_latency, 2)
            }
        }
        
        all_model_results.append(model_result)
    
    # 如果是多模型请求，返回包含所有模型结果的响应
    if len(all_model_results) > 1:
        return jsonify({'results': all_model_results})
    # 如果只有一个模型，返回单模型格式（兼容旧格式）
    elif all_model_results:
        return jsonify(all_model_results[0])
    else:
        return jsonify({'error': '没有有效的模型配置'}), 400

# 计划任务管理API
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = db.get_all_tasks()
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task[0],
            'name': task[1],
            'model_provider': task[2],
            'model_url': task[3],
            'test_count': task[5],
            'interval': task[6],
            'is_active': task[7],
            'created_at': task[8],
            'updated_at': task[9]
        })
    return jsonify(task_list)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    task_id = db.add_task(
        data['name'],
        data['model_provider'],
        data['model_url'],
        data['api_key'],
        data['test_count'],
        data['interval']
    )
    # 重新加载任务
    load_tasks()
    return jsonify({'task_id': task_id})

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    success = db.update_task(task_id, **data)
    # 重新加载任务
    load_tasks()
    return jsonify({'success': success})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    success = db.delete_task(task_id)
    # 重新加载任务
    load_tasks()
    return jsonify({'success': success})

@app.route('/api/tasks/<int:task_id>/results', methods=['GET'])
def get_task_results(task_id):
    results = db.get_task_results_with_info(task_id, limit=100)
    result_list = []
    for result in results:
        result_list.append({
            'id': result[0],
            'test_time': result[2],
            'total_tests': result[3],
            'success_count': result[4],
            'error_count': result[5],
            'error_rate': result[6],
            'latency_stats': json.loads(result[7])
        })
    return jsonify(result_list)

# 获取所有测试结果，用于图表展示
@app.route('/api/results', methods=['GET'])
def get_all_results():
    task_id = request.args.get('task_id')
    if task_id:
        results = db.get_task_results(int(task_id), limit=100)
    else:
        results = db.get_test_results(limit=100)
    
    result_list = []
    for result in results:
        result_list.append({
            'id': result[0],
            'task_id': result[1],
            'test_time': result[2],
            'total_tests': result[3],
            'success_count': result[4],
            'error_count': result[5],
            'error_rate': result[6],
            'latency_stats': json.loads(result[7])
        })
    
    return jsonify(result_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
