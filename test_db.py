import sqlite3

try:
    conn = sqlite3.connect('chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM messages')
    count = cursor.fetchone()[0]
    print(f'消息总数: {count}')
    
    cursor.execute('SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5')
    messages = cursor.fetchall()
    print('\n最近5条消息:')
    for msg in messages:
        print(f'{msg[4]} - {msg[2]}: {msg[3][:30]}...')
    
    cursor.execute('SELECT COUNT(*) FROM sessions')
    session_count = cursor.fetchone()[0]
    print(f'\n会话总数: {session_count}')
    
    conn.close()
except Exception as e:
    print(f'错误: {e}')

input('按回车退出...')