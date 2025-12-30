import requests
import time

# 用户提供的API Key
api_key = "sk-93c916e510a24f5e9bfe44407086efa7"

# DeepSeek API完整URL
deepseek_url = "https://api.deepseek.com/v1/chat/completions"

# 测试请求数据
test_data = {
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 50,
    "temperature": 0.7
}

try:
    print(f"测试DeepSeek API: {deepseek_url}")
    print("正在发送请求...")
    
    start_time = time.time()
    response = requests.post(
        deepseek_url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        json=test_data,
        timeout=30
    )
    end_time = time.time()
    
    print(f"\n请求耗时: {round((end_time - start_time) * 1000, 2)} ms")
    print(f"HTTP状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    
    try:
        response_json = response.json()
        print(f"\n响应内容(JSON): {response_json}")
    except:
        print(f"\n响应内容(非JSON): {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\n请求异常: {str(e)}")
    import traceback
    traceback.print_exc()
