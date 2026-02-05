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
                    email TEXT UNIQUE NOT NULL,
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
            
            # 清理旧表（如果存在）
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
            if cursor.fetchone():
                cursor.execute('DROP TABLE IF EXISTS tasks')
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_results'")
            if cursor.fetchone():
                cursor.execute('DROP TABLE IF EXISTS test_results')
            
            conn.commit()
    
    # ============ 用户相关 ============
    
    def create_user(self, email):
        """创建新用户"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = int(time.time())
            cursor.execute('''
                INSERT INTO users (email, created_at, last_login)
                VALUES (?, ?, ?)
            ''', (email, now, now))
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

# 全局数据库实例
db = Database()
