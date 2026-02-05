from flask import Flask, render_template, request, jsonify, session
import secrets
import time
import json
from datetime import datetime, timedelta
from functools import wraps
import re

from database import db
from email_service import send_verification_email
from config import AD_CONFIG

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '请先登录', 'code': 401}), 401
        return f(*args, **kwargs)
    return decorated_function

# 检查是否是新用户（根据邮箱判断）
def is_new_user(email):
    user = db.get_user_by_email(email)
    return user is None

# 获取今日测试次数
def get_today_test_count(user_id=None, ip=None):
    today = datetime.now().strftime('%Y-%m-%d')
    if user_id:
        count = db.get_test_count_by_user_and_date(user_id, today)
    else:
        count = db.get_test_count_by_ip_and_date(ip, today)
    return count

# 检查测试次数限制
def check_test_limit(user_id=None, ip=None):
    today_count = get_today_test_count(user_id, ip)
    if user_id:
        # 注册用户每天10次
        return today_count < 10, 10 - today_count
    else:
        # 非注册用户每天3次
        return today_count < 3, 3 - today_count

# ============ 页面路由 ============

@app.route('/')
def index():
    return render_template('index.html', ad_config=AD_CONFIG)

@app.route('/history')
def history():
    """测试历史页面"""
    return render_template('history.html')

@app.route('/share/<share_token>')
def share_result(share_token):
    """分享结果页面"""
    return render_template('share.html', share_token=share_token)

# ============ 用户认证 API ============

@app.route('/api/auth/send-code', methods=['POST'])
def send_code():
    """发送验证码"""
    data = request.json
    email = data.get('email', '').strip().lower()
    
    if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({'error': '请输入有效的邮箱地址'}), 400
    
    # 生成6位验证码
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # 保存验证码到数据库（5分钟有效）
    db.save_verification_code(email, code)
    
    # 发送邮件
    success = send_verification_email(email, code)
    if success:
        return jsonify({'message': '验证码已发送，请查收邮件'})
    else:
        return jsonify({'error': '验证码发送失败，请稍后重试'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """注册/登录"""
    data = request.json
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    
    if not email or not code:
        return jsonify({'error': '邮箱和验证码不能为空'}), 400
    
    # 验证验证码
    if not db.verify_code(email, code):
        return jsonify({'error': '验证码错误或已过期'}), 400
    
    # 检查用户是否存在，不存在则创建
    user = db.get_user_by_email(email)
    if not user:
        user_id = db.create_user(email)
        is_new = True
    else:
        user_id = user['id']
        is_new = False
    
    # 设置session
    session['user_id'] = user_id
    session['email'] = email
    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)
    
    return jsonify({
        'message': '登录成功',
        'user': {
            'id': user_id,
            'email': email,
            'is_new': is_new
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """退出登录"""
    session.clear()
    return jsonify({'message': '退出成功'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息"""
    if 'user_id' not in session:
        return jsonify({'logged_in': False})
    
    user = db.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        return jsonify({'logged_in': False})
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = db.get_test_count_by_user_and_date(user['id'], today)
    
    return jsonify({
        'logged_in': True,
        'user': {
            'id': user['id'],
            'email': user['email'],
            'daily_limit': 10,
            'today_used': today_count,
            'today_remaining': max(0, 10 - today_count)
        }
    })

# ============ 测试 API ============

@app.route('/api/test/limit', methods=['GET'])
def get_test_limit():
    """获取当前用户的测试限制"""
    user_id = session.get('user_id')
    ip = request.remote_addr
    
    can_test, remaining = check_test_limit(user_id, ip)
    limit = 10 if user_id else 3
    
    return jsonify({
        'logged_in': user_id is not None,
        'daily_limit': limit,
        'today_remaining': remaining,
        'can_test': remaining > 0
    })

@app.route('/api/test/submit', methods=['POST'])
def submit_test():
    """提交测试结果（前端完成测试后提交结果）"""
    user_id = session.get('user_id')
    ip = request.remote_addr
    
    # 检查测试次数限制
    can_test, remaining = check_test_limit(user_id, ip)
    if not can_test:
        limit = 10 if user_id else 3
        return jsonify({'error': f'今日测试次数已用完（{limit}次/天），请明天再试'}), 429
    
    data = request.json
    models = data.get('models', [])
    test_count = data.get('test_count', 1)
    results = data.get('results', [])  # 前端测试完成后的结果
    
    if not results:
        return jsonify({'error': '测试结果不能为空'}), 400
    
    # 保存测试记录
    today = datetime.now().strftime('%Y-%m-%d')
    test_record = {
        'user_id': user_id,
        'ip': ip if not user_id else None,
        'test_date': today,
        'test_count': test_count,
        'models_count': len(models),
        'results': results
    }
    
    record_id = db.save_test_record(test_record)
    
    # 记录测试次数
    if user_id:
        db.increment_test_count(user_id=user_id, date=today)
    else:
        db.increment_test_count(ip=ip, date=today)
    
    # 生成分享token
    share_token = db.create_share_token(record_id)
    
    return jsonify({
        'success': True,
        'record_id': record_id,
        'share_token': share_token,
        'share_url': f"/share/{share_token}",
        'today_remaining': remaining - 1
    })

@app.route('/api/test/history', methods=['GET'])
@login_required
def get_test_history():
    """获取测试历史（仅登录用户）"""
    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    history = db.get_user_test_history(user_id, page=page, per_page=per_page)
    return jsonify(history)

@app.route('/api/test/share/<share_token>', methods=['GET'])
def get_shared_result(share_token):
    """获取分享的测试结果"""
    result = db.get_shared_result(share_token)
    if not result:
        return jsonify({'error': '分享链接无效或已过期'}), 404
    
    return jsonify({
        'success': True,
        'data': result
    })

# ============ 错误处理 ============

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': '请求过于频繁，请稍后再试'}), 429

@app.errorhandler(500)
def server_error_handler(e):
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
