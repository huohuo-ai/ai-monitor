import sqlite3
import time
import json
import secrets
from datetime import datetime, timedelta
from contextlib import contextmanager

class Database:
    def __init__(self, db_path='ai_monitor.db'):
        self.db_path = db_path
        self._init_db()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 用户表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    wechat_openid TEXT UNIQUE,
                    wechat_nickname TEXT,
                    wechat_headimgurl TEXT,
                    created_at INTEGER NOT NULL,
                    last_login INTEGER
                )
            ''')
            
            # 验证码表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    used INTEGER DEFAULT 0
                )
            ''')
            
            # 测试记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip TEXT,
                    test_date TEXT NOT NULL,
                    test_count INTEGER NOT NULL,
                    models_count INTEGER NOT NULL,
                    results TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 测试次数统计表（按用户/日期）
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ip TEXT,
                    test_date TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    UNIQUE(user_id, test_date),
                    UNIQUE(ip, test_date),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 分享token表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS share_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER,
                    FOREIGN KEY (record_id) REFERENCES test_records (id) ON DELETE CASCADE
                )
            ''')
            
            # 管理员表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    last_login INTEGER
                )
            ''')
            
            # 广告点击记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ad_clicks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_index INTEGER NOT NULL,
                    ad_name TEXT NOT NULL,
                    ip TEXT,
                    user_id INTEGER,
                    clicked_at INTEGER NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # 清理旧表（如果存在）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if cursor.fetchone():
                cursor.execute('DROP TABLE IF EXISTS tasks')
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_results'")
            if cursor.fetchone():
                cursor.execute('DROP TABLE IF EXISTS test_results')
            
            conn.commit()
    
    # ============ 用户相关 ============
    
    def create_user(self, email=None, wechat_openid=None, wechat_nickname=None, wechat_headimgurl=None):
        """创建新用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                INSERT INTO users (email, wechat_openid, wechat_nickname, wechat_headimgurl, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (email, wechat_openid, wechat_nickname, wechat_headimgurl, now, now))
            return cursor.lastrowid
    
    def get_user_by_email(self, email):
        """通过邮箱获取用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_user_by_wechat_openid(self, openid):
        """通过微信openid获取用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE wechat_openid = ?', (openid,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_user_wechat_info(self, user_id, nickname, headimgurl):
        """更新用户微信信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET wechat_nickname = ?, wechat_headimgurl = ? WHERE id = ?
            ''', (nickname, headimgurl, user_id))
    
    def get_user_by_id(self, user_id):
        """通过ID获取用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_last_login(self, user_id):
        """更新最后登录时间"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (int(time.time()), user_id))
    
    # ============ 验证码相关 ============
    
    def save_verification_code(self, email, code):
        """保存验证码"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            # 将同一邮箱的旧验证码标记为已使用
            cursor.execute('''
                UPDATE verification_codes SET used = 1 WHERE email = ? AND used = 0
            ''', (email,))
            # 插入新验证码
            cursor.execute('''
                INSERT INTO verification_codes (email, code, created_at)
                VALUES (?, ?, ?)
            ''', (email, code, now))
    
    def verify_code(self, email, code):
        """验证验证码"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            # 验证码5分钟有效
            cursor.execute('''
                SELECT * FROM verification_codes 
                WHERE email = ? AND code = ? AND used = 0 AND created_at > ?
            ''', (email, code, now - 300))
            row = cursor.fetchone()
            if row:
                # 标记为已使用
                cursor.execute('''
                    UPDATE verification_codes SET used = 1 WHERE id = ?
                ''', (row['id'],))
                return True
            return False
    
    def clean_expired_codes(self):
        """清理过期验证码（1小时前的）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                DELETE FROM verification_codes WHERE created_at < ?
            ''', (now - 3600,))
    
    # ============ 测试次数相关 ============
    
    def get_test_count_by_user_and_date(self, user_id, date):
        """获取用户某日的测试次数"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT count FROM test_counts WHERE user_id = ? AND test_date = ?
            ''', (user_id, date))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def get_test_count_by_ip_and_date(self, ip, date):
        """获取IP某日的测试次数"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT count FROM test_counts WHERE ip = ? AND test_date = ?
            ''', (ip, date))
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def increment_test_count(self, user_id=None, ip=None, date=None):
        """增加测试次数"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    INSERT INTO test_counts (user_id, test_date, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(user_id, test_date) DO UPDATE SET count = count + 1
                ''', (user_id, date))
            elif ip:
                cursor.execute('''
                    INSERT INTO test_counts (ip, test_date, count)
                    VALUES (?, ?, 1)
                    ON CONFLICT(ip, test_date) DO UPDATE SET count = count + 1
                ''', (ip, date))
    
    # ============ 测试记录相关 ============
    
    def save_test_record(self, record):
        """保存测试记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                INSERT INTO test_records 
                (user_id, ip, test_date, test_count, models_count, results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.get('user_id'),
                record.get('ip'),
                record['test_date'],
                record['test_count'],
                record['models_count'],
                json.dumps(record['results']),
                now
            ))
            return cursor.lastrowid
    
    def get_test_record_by_id(self, record_id):
        """通过ID获取测试记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM test_records WHERE id = ?', (record_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['results'] = json.loads(result['results'])
                return result
            return None
    
    def get_user_test_history(self, user_id, page=1, per_page=10):
        """获取用户的测试历史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            offset = (page - 1) * per_page
            
            # 获取记录
            cursor.execute('''
                SELECT tr.*, st.token as share_token
                FROM test_records tr
                LEFT JOIN share_tokens st ON tr.id = st.record_id
                WHERE tr.user_id = ?
                ORDER BY tr.created_at DESC
                LIMIT ? OFFSET ?
            ''', (user_id, per_page, offset))
            rows = cursor.fetchall()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM test_records WHERE user_id = ?', (user_id,))
            total = cursor.fetchone()['total']
            
            records = []
            for row in rows:
                record = dict(row)
                record['results'] = json.loads(record['results'])
                record['created_at_formatted'] = datetime.fromtimestamp(record['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                records.append(record)
            
            return {
                'records': records,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
    
    # ============ 分享相关 ============
    
    def create_share_token(self, record_id, expires_days=365):
        """创建分享token"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            token = secrets.token_urlsafe(32)
            now = int(time.time())
            expires_at = now + (expires_days * 24 * 3600) if expires_days else None
            
            cursor.execute('''
                INSERT INTO share_tokens (record_id, token, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (record_id, token, now, expires_at))
            
            return token
    
    def get_shared_result(self, token):
        """通过token获取分享的结果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            
            cursor.execute('''
                SELECT tr.*, st.created_at as shared_at
                FROM share_tokens st
                JOIN test_records tr ON st.record_id = tr.id
                WHERE st.token = ? AND (st.expires_at IS NULL OR st.expires_at > ?)
            ''', (token, now))
            
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['results'] = json.loads(result['results'])
                result['created_at_formatted'] = datetime.fromtimestamp(result['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                return result
            return None
    
    def clean_expired_tokens(self):
        """清理过期的分享token"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                DELETE FROM share_tokens WHERE expires_at IS NOT NULL AND expires_at < ?
            ''', (now,))
    
    # ============ 管理员相关 ============
    
    def create_admin(self, username, password_hash):
        """创建管理员账号"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            try:
                cursor.execute('''
                    INSERT INTO admins (username, password_hash, created_at)
                    VALUES (?, ?, ?)
                ''', (username, password_hash, now))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None
    
    def get_admin_by_username(self, username):
        """通过用户名获取管理员"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM admins WHERE username = ?', (username,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def update_admin_last_login(self, admin_id):
        """更新管理员最后登录时间"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE admins SET last_login = ? WHERE id = ?
            ''', (int(time.time()), admin_id))
    
    def get_admin_stats(self):
        """获取管理员仪表盘统计数据"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            
            # 总用户数
            cursor.execute('SELECT COUNT(*) as count FROM users')
            stats['total_users'] = cursor.fetchone()['count']
            
            # 今日注册用户数
            today_start = int(datetime.now().replace(hour=0, minute=0, second=0).timestamp())
            cursor.execute('SELECT COUNT(*) as count FROM users WHERE created_at >= ?', (today_start,))
            stats['today_users'] = cursor.fetchone()['count']
            
            # 总测试次数
            cursor.execute('SELECT COUNT(*) as count FROM test_records')
            stats['total_tests'] = cursor.fetchone()['count']
            
            # 今日测试次数
            cursor.execute('SELECT COUNT(*) as count FROM test_records WHERE created_at >= ?', (today_start,))
            stats['today_tests'] = cursor.fetchone()['count']
            
            # 总广告点击数
            cursor.execute('SELECT COUNT(*) as count FROM ad_clicks')
            stats['total_ad_clicks'] = cursor.fetchone()['count']
            
            # 今日广告点击数
            cursor.execute('SELECT COUNT(*) as count FROM ad_clicks WHERE clicked_at >= ?', (today_start,))
            stats['today_ad_clicks'] = cursor.fetchone()['count']
            
            return stats
    
    # ============ 广告点击相关 ============
    
    def record_ad_click(self, ad_index, ad_name, ip=None, user_id=None):
        """记录广告点击"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                INSERT INTO ad_clicks (ad_index, ad_name, ip, user_id, clicked_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (ad_index, ad_name, ip, user_id, now))
            return cursor.lastrowid
    
    def get_ad_click_stats(self, days=30):
        """获取广告点击统计（按广告分组）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            since = int((datetime.now() - timedelta(days=days)).timestamp())
            
            cursor.execute('''
                SELECT ad_index, ad_name, COUNT(*) as click_count
                FROM ad_clicks
                WHERE clicked_at >= ?
                GROUP BY ad_index, ad_name
                ORDER BY ad_index
            ''', (since,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_ad_click_daily_stats(self, days=30):
        """获取广告点击统计（按日期分组）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            since = int((datetime.now() - timedelta(days=days)).timestamp())
            
            cursor.execute('''
                SELECT date(clicked_at, 'unixepoch', 'localtime') as date, COUNT(*) as count
                FROM ad_clicks
                WHERE clicked_at >= ?
                GROUP BY date(clicked_at, 'unixepoch', 'localtime')
                ORDER BY date DESC
            ''', (since,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_recent_ad_clicks(self, limit=50):
        """获取最近的广告点击记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT ac.*, u.email, u.wechat_nickname
                FROM ad_clicks ac
                LEFT JOIN users u ON ac.user_id = u.id
                ORDER BY ac.clicked_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            results = []
            for row in rows:
                record = dict(row)
                record['clicked_at_formatted'] = datetime.fromtimestamp(record['clicked_at']).strftime('%Y-%m-%d %H:%M:%S')
                results.append(record)
            return results
    
    def get_user_stats(self, days=30):
        """获取用户注册统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            since = int((datetime.now() - timedelta(days=days)).timestamp())
            
            # 每日注册用户统计
            cursor.execute('''
                SELECT date(created_at, 'unixepoch', 'localtime') as date, COUNT(*) as count
                FROM users
                WHERE created_at >= ?
                GROUP BY date(created_at, 'unixepoch', 'localtime')
                ORDER BY date DESC
            ''', (since,))
            daily_registrations = [dict(row) for row in cursor.fetchall()]
            
            # 每日登录统计
            cursor.execute('''
                SELECT date(last_login, 'unixepoch', 'localtime') as date, COUNT(*) as count
                FROM users
                WHERE last_login >= ?
                GROUP BY date(last_login, 'unixepoch', 'localtime')
                ORDER BY date DESC
            ''', (since,))
            daily_logins = [dict(row) for row in cursor.fetchall()]
            
            # 最近的注册用户
            cursor.execute('''
                SELECT * FROM users
                ORDER BY created_at DESC
                LIMIT 20
            ''')
            recent_users = []
            for row in cursor.fetchall():
                user = dict(row)
                user['created_at_formatted'] = datetime.fromtimestamp(user['created_at']).strftime('%Y-%m-%d %H:%M:%S')
                user['last_login_formatted'] = datetime.fromtimestamp(user['last_login']).strftime('%Y-%m-%d %H:%M:%S') if user['last_login'] else None
                recent_users.append(user)
            
            return {
                'daily_registrations': daily_registrations,
                'daily_logins': daily_logins,
                'recent_users': recent_users
            }

# 全局数据库实例
db = Database()
