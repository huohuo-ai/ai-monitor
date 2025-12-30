import requests
import time

# 用户提供的API Key
api_key = "sk-93c916e510a24f5e9bfe44407086efa7"

# DeepSeek API完整URL
deepseek_url = "https://api.deepseek.com/v1/chat/completions"

# 测试请求数据 - 包含model字段
test_data = {
    "model": "deepseek-chat",
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
        
        # 检查是否有错误
        if 'error' in response_json:
            print(f"\n❌ API错误: {response_json['error']['message']}")
        else:
            print("\n✅ API调用成功!")
            if 'choices' in response_json and response_json['choices']:
                print(f"响应内容: {response_json['choices'][0]['message']['content']}")
                
    except Exception as e:
        print(f"\n解析JSON响应失败: {str(e)}")
        print(f"响应内容(原始): {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"\n❌ 请求异常: {str(e)}")
    import traceback
    traceback.print_exc()
