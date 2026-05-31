import sqlite3
import json
from typing import Dict, Optional, List
from datetime import datetime
from models import Message, ConversationSession, Intent, DialogueState

class DatabaseHandler:
    def __init__(self, db_path: str = "chatbot.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                state TEXT,
                current_intent TEXT,
                slots_json TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                message_count INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                role TEXT,
                content TEXT,
                intent TEXT,
                state TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dialogue_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                state TEXT,
                intent TEXT,
                slots_json TEXT,
                timestamp TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, state, current_intent, slots_json, created_at, updated_at, message_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ''', (session_id, user_id, DialogueState.START.value, None, '{}', now, now))
            conn.commit()
            return True
        except Exception as e:
            print(f"创建会话失败: {e}")
            return False
        finally:
            conn.close()
    
    def save_message(self, session_id: str, role: str, content: str, 
                    intent: Optional[str] = None, state: Optional[str] = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            now = datetime.now()
            cursor.execute('''
                INSERT INTO messages (session_id, role, content, intent, state, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, role, content, intent, state, now))
            
            cursor.execute('''
                UPDATE sessions 
                SET message_count = message_count + 1, updated_at = ?
                WHERE session_id = ?
            ''', (now, session_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False
        finally:
            conn.close()
    
    def save_dialogue_state(self, session_id: str, state: str, 
                           intent: Optional[str] = None, slots: Optional[Dict] = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            slots_json = json.dumps(slots) if slots else '{}'
            now = datetime.now()
            cursor.execute('''
                INSERT INTO dialogue_states (session_id, state, intent, slots_json, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, state, intent, slots_json, now))
            
            cursor.execute('''
                UPDATE sessions 
                SET state = ?, current_intent = ?, slots_json = ?, updated_at = ?
                WHERE session_id = ?
            ''', (state, intent, slots_json, now, session_id))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"保存对话状态失败: {e}")
            return False
        finally:
            conn.close()
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT role, content, intent, state, timestamp 
                FROM messages 
                WHERE session_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"获取会话历史失败: {e}")
            return []
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            total_sessions = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM messages")
            total_messages = cursor.fetchone()['count']
            
            cursor.execute('''
                SELECT intent, COUNT(*) as count 
                FROM messages 
                WHERE intent IS NOT NULL 
                GROUP BY intent 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_intents = {row['intent']: row['count'] for row in cursor.fetchall()}
            
            cursor.execute('''
                SELECT COUNT(DISTINCT session_id) as count 
                FROM messages 
                WHERE DATE(timestamp) = DATE('now')
            ''')
            daily_active_users = cursor.fetchone()['count']
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'top_intents': top_intents,
                'daily_active_users': daily_active_users
            }
        except Exception as e:
            print(f"获取统计数据失败: {e}")
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'top_intents': {},
                'daily_active_users': 0
            }
        finally:
            conn.close()

db_handler = DatabaseHandler()
