from typing import Dict, Optional, List
from models import (
    Intent, DialogueState, Message, MessageRole,
    ConversationSession, Slot
)
from nlp_engine import nlp_engine
from database import db_handler
from datetime import datetime
import uuid

class DialogueManager:
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
        self.max_history = 10
        self.session_timeout = 3600
    
    def get_or_create_session(self, session_id: Optional[str], user_id: Optional[str] = None) -> ConversationSession:
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            session.updated_at = datetime.now()
            return session
        
        new_session_id = session_id or str(uuid.uuid4())
        session = ConversationSession(
            session_id=new_session_id,
            user_id=user_id,
            state=DialogueState.START
        )
        self.sessions[new_session_id] = session
        db_handler.create_session(new_session_id, user_id)
        return session
    
    def update_session_state(self, session: ConversationSession, new_state: DialogueState, intent: Optional[Intent] = None):
        session.state = new_state
        session.updated_at = datetime.now()
        
        if intent:
            session.current_intent = intent
        
        db_handler.save_dialogue_state(
            session.session_id,
            new_state.value,
            intent.value if intent else None,
            {k: {'value': v.value, 'filled': v.filled} for k, v in session.slots.items()}
        )
    
    def add_to_context(self, session: ConversationSession, role: MessageRole, content: str, intent: Optional[Intent] = None):
        message = Message(
            role=role,
            content=content,
            metadata={'intent': intent.value if intent else None}
        )
        session.context.append(message)
        session.message_count += 1
        
        if len(session.context) > self.max_history:
            session.context = session.context[-self.max_history:]
    
    def process_turn(self, session: ConversationSession, user_input: str) -> Dict:
        self.add_to_context(session, MessageRole.USER, user_input)
        
        nlp_result = nlp_engine.process(user_input, session.current_intent)
        
        intent = nlp_result['intent']
        slots = nlp_result['slots']
        use_rag = nlp_result.get('use_rag', False)
        
        for slot_name, slot_data in slots.items():
            if slot_name in session.slots:
                if slot_data['filled']:
                    session.slots[slot_name].value = slot_data['value']
                    session.slots[slot_name].filled = True
            else:
                session.slots[slot_name] = Slot(
                    name=slot_name,
                    value=slot_data.get('value'),
                    required=slot_data.get('required', False),
                    filled=slot_data.get('filled', False)
                )
        
        response = nlp_result['response']

        if intent.value == 'stock_query' and response is None:
            try:
                from stock_api import stock_api
                import re
                stock_codes = re.findall(r'(sh|sz)\d{6}', user_input.lower())
                if stock_codes:
                    stock_code = stock_codes[0]
                else:
                    stock_code = 'sh600519'
                response = stock_api.format_quote(stock_code)
                if response is None:
                    response = f"抱歉，未找到股票 {stock_code.upper()} 的数据。请检查股票代码是否正确。\n\n常用股票代码示例：\n• 贵州茅台: sh600519\n• 招商银行: sh600036\n• 中国平安: sh601318\n• 万科A: sz000002\n• 腾讯控股: sz00700"
            except Exception as e:
                response = f"获取股票信息失败: {str(e)}"
        elif use_rag or response is None:
            try:
                from prompt import chat_finance
                response = chat_finance(user_input)
            except Exception as e:
                if response is None:
                    response = f"抱歉，暂时无法回答您的问题。错误：{str(e)}"
        
        if session.state == DialogueState.START:
            new_state = DialogueState.RESPONDING
        elif intent != session.current_intent and session.current_intent:
            new_state = DialogueState.INTENT_CONFIRM
        else:
            new_state = DialogueState.RESPONDING
        
        self.update_session_state(session, new_state, intent)
        
        self.add_to_context(session, MessageRole.BOT, response, intent)
        
        db_handler.save_message(
            session.session_id,
            MessageRole.USER.value,
            user_input,
            intent.value,
            session.state.value
        )
        db_handler.save_message(
            session.session_id,
            MessageRole.BOT.value,
            response,
            intent.value,
            session.state.value
        )
        
        return {
            'answer': response,
            'intent': intent,
            'state': session.state,
            'slots': slots,
            'context_maintained': len(session.context) > 1
        }
    
    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        return {
            'session_id': session.session_id,
            'state': session.state.value,
            'current_intent': session.current_intent.value if session.current_intent else None,
            'message_count': session.message_count,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        }
    
    def cleanup_expired_sessions(self):
        now = datetime.now()
        expired = [
            sid for sid, session in self.sessions.items()
            if (now - session.updated_at).seconds > self.session_timeout
        ]
        for sid in expired:
            del self.sessions[sid]

dialogue_manager = DialogueManager()
