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
    for model_idx, model in enumerate(models):
        model_provider = model.get('model_provider', 'custom')
        model_url = model.get('model_url')
        api_key = model.get('api_key')
        
        print(f"\n{'='*60}")
        print(f"开始测试模型 {model_idx + 1}/{len(models)}")
        print(f"模型提供商: {model_provider}")
        print(f"API URL: {model_url}")
        print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")
        print(f"{'='*60}\n")
        
        if not model_url or not api_key:
            print(f"模型 {model_idx + 1}: 跳过无效模型配置")
            continue  # 跳过无效模型配置
        
        results = []
        ttft_results = []
        tokens_throughput_results = []
        total_tokens_results = []
        errors = 0
        
        # 执行多次测试
        for i in range(test_count):
            start_time = time.time()
            print(f"  测试 {i+1}/{test_count} 开始...")
            try:
                # 根据模型提供商设置模型名称和API路径
                model_map = {
                    'deepseek': 'deepseek-chat',
                    'openai': 'gpt-3.5-turbo',
                    'anthropic': 'claude-3-sonnet-20240229',
                    'kimi': 'kimi-k2-turbo-preview',
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
                        'max_tokens': 50,
                        'stream': True  # 启用流式响应
                    }
                
                # 流式请求以计算TTFT和tokens吞吐
                response = requests.post(
                    api_url,
                    headers={
                        'Authorization': f'Bearer {api_key}',
                        'Content-Type': 'application/json'
                    },
                    json=request_data,
                    stream=True,
                    timeout=30
                )
                
                print(f"  响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    # 检测响应类型（流式或非流式）
                    first_line = next(response.iter_lines(), None)
                    is_streaming = first_line and first_line.decode('utf-8').startswith('data: ')
                    
                    # 重置响应迭代器
                    response = requests.post(
                        api_url,
                        headers={
                            'Authorization': f'Bearer {api_key}',
                            'Content-Type': 'application/json'
                        },
                        json=request_data,
                        stream=True,
                        timeout=30
                    )
                    
                    # 计算TTFT和tokens吞吐
                    first_token_time = None
                    total_tokens = 0
                    completion_start_time = time.time()
                    
                    if is_streaming:
                        print(f"  检测到流式响应")
                        print(f"  开始处理流式响应...")
                        line_count = 0
                        for line in response.iter_lines():
                            if line:
                                line = line.decode('utf-8')
                                line_count += 1
                                # 打印前5行响应数据用于调试
                                if line_count <= 5:
                                    print(f"  响应行 {line_count}: {line[:200]}...")
                                
                                if line.startswith('data: '):
                                    data_str = line[6:]
                                    if data_str == '[DONE]':
                                        break
                                    try:
                                        data = json.loads(data_str)
                                        # 打印前3个解析的JSON对象用于调试
                                        if line_count <= 5:
                                            print(f"  解析JSON: {json.dumps(data, ensure_ascii=False)[:200]}...")
                                        
                                        # 提取token数（兼容不同API格式）
                                        if 'choices' in data and len(data['choices']) > 0:
                                            delta = data['choices'][0].get('delta', {})
                                            if 'content' in delta and delta['content']:
                                                if first_token_time is None:
                                                    first_token_time = time.time()
                                                    print(f"  首个token到达时间: {first_token_time - start_time:.3f}s")
                                                total_tokens += len(delta['content'].split())
                                        else:
                                            # 如果没有choices字段，尝试其他格式
                                            if line_count <= 5:
                                                print(f"  警告: 响应中没有'choices'字段，keys={list(data.keys())}")
                                    except json.JSONDecodeError as e:
                                        if line_count <= 5:
                                            print(f"  JSON解析错误: {e}")
                    else:
                        print(f"  检测到非流式响应")
                        # 处理非流式响应
                        try:
                            response_data = response.json()
                            print(f"  响应数据: {json.dumps(response_data, ensure_ascii=False)[:200]}...")
                            
                            # 从非流式响应中提取内容
                            if 'choices' in response_data and len(response_data['choices']) > 0:
                                message = response_data['choices'][0].get('message', {})
                                content = message.get('content', '')
                                if content:
                                    total_tokens = len(content.split())
                                    print(f"  提取到内容，tokens: {total_tokens}")
                        except Exception as e:
                            print(f"  解析非流式响应失败: {e}")
                    
                    completion_end_time = time.time()
                    print(f"  流式响应完成，总tokens: {total_tokens}")
                    
                    # 计算总延迟（从请求发送到流式响应完成的时间，毫秒）
                    latency = (completion_end_time - start_time) * 1000
                    
                    # 计算TTFT（毫秒）- 仅流式响应有TTFT
                    if is_streaming and first_token_time:
                        ttft = (first_token_time - start_time) * 1000
                        ttft_results.append(ttft)
                        print(f"  TTFT: {ttft:.2f}ms")
                    elif not is_streaming:
                        print(f"  非流式响应，无法计算TTFT")
                    else:
                        print(f"  警告: 未检测到首个token!")
                    
                    # 计算tokens吞吐（tokens/秒）
                    if total_tokens > 0 and completion_end_time > completion_start_time:
                        throughput = total_tokens / (completion_end_time - completion_start_time)
                        tokens_throughput_results.append(throughput)
                        total_tokens_results.append(total_tokens)
                        print(f"  Token吞吐: {throughput:.2f} tokens/s")
                    else:
                        print(f"  警告: Token吞吐计算失败 (total_tokens={total_tokens}, duration={completion_end_time - completion_start_time:.3f}s)")
                    
                    results.append(latency)
                    print(f"  延迟: {latency:.2f}ms")
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
            avg_latency = float(np.mean(results))
            p90_latency = float(np.percentile(results, 90))
            p99_latency = float(np.percentile(results, 99))
            min_latency = float(np.min(results))
            max_latency = float(np.max(results))
        else:
            avg_latency = p90_latency = p99_latency = min_latency = max_latency = 0.0
        
        # 计算TTFT指标
        if ttft_results:
            avg_ttft = float(np.mean(ttft_results))
            p90_ttft = float(np.percentile(ttft_results, 90))
            p99_ttft = float(np.percentile(ttft_results, 99))
            min_ttft = float(np.min(ttft_results))
            max_ttft = float(np.max(ttft_results))
        else:
            avg_ttft = p90_ttft = p99_ttft = min_ttft = max_ttft = 0.0
        
        # 计算tokens吞吐指标
        if tokens_throughput_results:
            avg_throughput = float(np.mean(tokens_throughput_results))
            p90_throughput = float(np.percentile(tokens_throughput_results, 90))
            p99_throughput = float(np.percentile(tokens_throughput_results, 99))
            min_throughput = float(np.min(tokens_throughput_results))
            max_throughput = float(np.max(tokens_throughput_results))
        else:
            avg_throughput = p90_throughput = p99_throughput = min_throughput = max_throughput = 0.0
        
        # 计算总token数指标
        if total_tokens_results:
            avg_tokens = float(np.mean(total_tokens_results))
            p90_tokens = float(np.percentile(total_tokens_results, 90))
            p99_tokens = float(np.percentile(total_tokens_results, 99))
            min_tokens = float(np.min(total_tokens_results))
            max_tokens = float(np.max(total_tokens_results))
        else:
            avg_tokens = p90_tokens = p99_tokens = min_tokens = max_tokens = 0.0
        
        error_rate = errors / test_count * 100
        success_count = test_count - errors
        
        print(f"\n{'='*60}")
        print(f"模型 {model_idx + 1} 测试完成:")
        print(f"  成功: {success_count}/{test_count}")
        print(f"  失败: {errors}/{test_count}")
        print(f"  TTFT结果数: {len(ttft_results)}")
        print(f"  Token吞吐结果数: {len(tokens_throughput_results)}")
        print(f"  延迟结果数: {len(results)}")
        print(f"{'='*60}\n")
        
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
            },
            'ttft_stats': {
                'avg': round(avg_ttft, 2),
                'p90': round(p90_ttft, 2),
                'p99': round(p99_ttft, 2),
                'min': round(min_ttft, 2),
                'max': round(max_ttft, 2)
            },
            'tokens_throughput_stats': {
                'avg': round(avg_throughput, 2),
                'p90': round(p90_throughput, 2),
                'p99': round(p99_throughput, 2),
                'min': round(min_throughput, 2),
                'max': round(max_throughput, 2)
            },
            'total_tokens_stats': {
                'avg': round(avg_tokens, 2),
                'p90': round(p90_tokens, 2),
                'p99': round(p99_tokens, 2),
                'min': round(min_tokens, 2),
                'max': round(max_tokens, 2)
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
            'latency_stats': json.loads(result[7]),
            'ttft_stats': json.loads(result[8]) if result[8] else {},
            'tokens_throughput_stats': json.loads(result[9]) if result[9] else {},
            'total_tokens_stats': json.loads(result[10]) if result[10] else {}
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
            'latency_stats': json.loads(result[7]),
            'ttft_stats': json.loads(result[8]) if result[8] else {},
            'tokens_throughput_stats': json.loads(result[9]) if result[9] else {},
            'total_tokens_stats': json.loads(result[10]) if result[10] else {}
        })
    
    return jsonify(result_list)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
