import sqlite3
import time
import json

class Database:
    def __init__(self, db_path='ai_monitor.db'):
        self.db_path = db_path
        # 检查数据库文件是否存在，如果不存在则创建
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        self.create_tables(conn, cursor)
        conn.close()
    
    def get_connection(self):
        """为每个线程创建独立的数据库连接"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        return conn, cursor
    
    def create_tables(self, conn, cursor):
        # 创建计划任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model_provider TEXT NOT NULL,
                model_url TEXT NOT NULL,
                api_key TEXT NOT NULL,
                test_count INTEGER NOT NULL,
                interval INTEGER NOT NULL,  -- 间隔时间（分钟）
                is_active INTEGER DEFAULT 1,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        ''')
        
        # 创建测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                test_time INTEGER NOT NULL,
                total_tests INTEGER NOT NULL,
                success_count INTEGER NOT NULL,
                error_count INTEGER NOT NULL,
                error_rate REAL NOT NULL,
                latency_stats TEXT NOT NULL,  -- JSON格式保存延迟统计
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        conn.commit()
    
    def add_task(self, name, model_provider, model_url, api_key, test_count, interval):
        conn, cursor = self.get_connection()
        timestamp = int(time.time())
        cursor.execute('''
            INSERT INTO tasks (name, model_provider, model_url, api_key, test_count, interval, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (name, model_provider, model_url, api_key, test_count, interval, timestamp, timestamp))
        conn.commit()
        last_row_id = cursor.lastrowid
        conn.close()
        return last_row_id
    
    def update_task(self, task_id, **kwargs):
        conn, cursor = self.get_connection()
        kwargs['updated_at'] = int(time.time())
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [task_id]
        cursor.execute(f'''
            UPDATE tasks SET {set_clause} WHERE id = ?
        ''', values)
        conn.commit()
        row_count = cursor.rowcount
        conn.close()
        return row_count > 0
    
    def delete_task(self, task_id):
        conn, cursor = self.get_connection()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()
        row_count = cursor.rowcount
        conn.close()
        return row_count > 0
    
    def get_task(self, task_id):
        conn, cursor = self.get_connection()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_all_tasks(self):
        conn, cursor = self.get_connection()
        cursor.execute('SELECT * FROM tasks ORDER BY updated_at DESC')
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_active_tasks(self):
        conn, cursor = self.get_connection()
        cursor.execute('SELECT * FROM tasks WHERE is_active = 1')
        result = cursor.fetchall()
        conn.close()
        return result
    
    def add_test_result(self, task_id, result_data):
        conn, cursor = self.get_connection()
        timestamp = int(time.time())
        cursor.execute('''
            INSERT INTO test_results (task_id, test_time, total_tests, success_count, error_count, error_rate, latency_stats)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            timestamp,
            result_data['total_tests'],
            result_data['success_count'],
            result_data['error_count'],
            result_data['error_rate'],
            json.dumps(result_data['latency_stats'])
        ))
        conn.commit()
        last_row_id = cursor.lastrowid
        conn.close()
        return last_row_id
    
    def get_test_results(self, task_id=None, limit=50):
        conn, cursor = self.get_connection()
        if task_id:
            cursor.execute('''
                SELECT * FROM test_results WHERE task_id = ? ORDER BY test_time DESC LIMIT ?
            ''', (task_id, limit))
        else:
            cursor.execute('''
                SELECT * FROM test_results ORDER BY test_time DESC LIMIT ?
            ''', (limit,))
        result = cursor.fetchall()
        conn.close()
        return result
    
    def get_task_results_with_info(self, task_id, limit=50):
        conn, cursor = self.get_connection()
        cursor.execute('''
            SELECT tr.*, t.name, t.model_provider, t.model_url 
            FROM test_results tr
            JOIN tasks t ON tr.task_id = t.id
            WHERE tr.task_id = ?
            ORDER BY tr.test_time DESC
            LIMIT ?
        ''', (task_id, limit))
        result = cursor.fetchall()
        conn.close()
        return result
    
    def close(self):
        # 不需要关闭连接，因为现在每个操作都有自己的连接
        pass

# 初始化数据库实例
db = Database()
