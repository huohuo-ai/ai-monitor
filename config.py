# 系统配置

# 广告位配置
AD_CONFIG = {
    # 总开关：是否启用广告位
    'enabled': True,
    
    # 广告位标题
    'title': '🚀 推荐服务',
    
    # 广告列表
    'ads': [
        {
            'icon': 'bi-robot',
            'name': 'DeepSeek API',
            'desc': '国产大模型，性价比之选',
            'url': 'https://platform.deepseek.com/',
            'badge': '热门',
            'badge_color': 'danger'
        },
        {
            'icon': 'bi-lightning-charge',
            'name': 'Kimi API',
            'desc': 'Moonshot AI，长文本专家',
            'url': 'https://platform.moonshot.cn/',
            'badge': None,
            'badge_color': None
        },
        {
            'icon': 'bi-globe',
            'name': 'OpenRouter',
            'desc': '一站式接入多种大模型',
            'url': 'https://openrouter.ai/',
            'badge': '聚合',
            'badge_color': 'info'
        },
        {
            'icon': 'bi-cpu',
            'name': 'SiliconFlow',
            'desc': '开源模型推理服务',
            'url': 'https://siliconflow.cn/',
            'badge': None,
            'badge_color': None
        }
    ]
}
