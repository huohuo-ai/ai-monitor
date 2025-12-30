import requests
import json

# 测试完整的应用流程
base_url = "http://localhost:5000"

# 使用用户提供的DeepSeek API Key
test_api_key = "sk-93c916e510a24f5e9bfe44407086efa7"

def test_app_flow():
    print("测试AI模型拨测应用完整流程...")
    print("=" * 60)
    
    # 1. 测试主页是否可访问
    try:
        response = requests.get(base_url)
        print(f"1. 主页访问: {'✅ 成功' if response.status_code == 200 else '❌ 失败'} (状态码: {response.status_code})")
    except Exception as e:
        print(f"1. 主页访问: ❌ 失败 - {str(e)}")
        return False
    
    # 2. 测试模型测试功能
    print("\n2. 测试DeepSeek模型拨测...")
    test_data = {
        "model_provider": "deepseek",
        "model_url": "https://api.deepseek.com",
        "api_key": test_api_key,
        "test_count": 2
    }
    
    try:
        response = requests.post(f"{base_url}/test_model", json=test_data)
        print(f"   API调用: {'✅ 成功' if response.status_code == 200 else '❌ 失败'} (状态码: {response.status_code})")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   测试结果:")
            print(f"   - 总测试次数: {result['total_tests']}")
            print(f"   - 成功次数: {result['success_count']}")
            print(f"   - 失败次数: {result['error_count']}")
            print(f"   - 错误率: {result['error_rate']}%")
            print(f"   - 延迟统计:")
            print(f"     * 平均延时: {result['latency_stats']['avg']} ms")
            print(f"     * P90延时: {result['latency_stats']['p90']} ms")
            print(f"     * P99延时: {result['latency_stats']['p99']} ms")
            print(f"     * 最小延时: {result['latency_stats']['min']} ms")
            print(f"     * 最大延时: {result['latency_stats']['max']} ms")
            
            if result['success_count'] > 0:
                print(f"\n✅ 应用集成测试成功！DeepSeek API拨测正常工作。")
                return True
            else:
                print(f"\n❌ 测试请求全部失败")
                return False
        else:
            print(f"   错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_app_flow()
    print("\n" + "=" * 60)
    print(f"集成测试{'通过' if success else '失败'}")
