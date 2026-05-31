from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import time
import traceback

from models import (
    ChatRequest, ChatResponse, HealthResponse, StatisticsResponse,
    CompareResponse, RAGQuery, RAGResponse
)
from dialogue_manager import dialogue_manager
from database import db_handler
from prompt import chat_finance, chat_finance_base, chat_finance_compare

app = FastAPI(
    title="金融问答机器人 API",
    version="1.0.0",
    description="基于自然语言处理的金融问答系统，支持多轮对话、意图识别和上下文理解"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session = dialogue_manager.get_or_create_session(request.session_id, request.user_id)
        result = dialogue_manager.process_turn(session, request.question)
        
        return ChatResponse(
            session_id=session.session_id,
            question=request.question,
            answer=result['answer'],
            intent=result['intent'],
            state=result['state'],
            success=True,
            context_maintained=result['context_maintained']
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag-chat", response_model=RAGResponse)
async def rag_chat(request: RAGQuery):
    try:
        if not request.question or request.question.strip() == "":
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        answer = chat_finance(request.question)
        
        return RAGResponse(
            question=request.question,
            answer=answer,
            success=True
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        return RAGResponse(
            question=request.question,
            answer="",
            success=False,
            error=f"服务器内部错误: {str(e)}"
        )

@app.post("/compare", response_model=CompareResponse)
async def compare_models(request: RAGQuery):
    try:
        if not request.question or request.question.strip() == "":
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        result = chat_finance_compare(request.question)
        
        return CompareResponse(
            question=request.question,
            base_model=result['base_model'],
            fine_tuned_model=result['fine_tuned_model'],
            success=True
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        return CompareResponse(
            question=request.question,
            base_model="",
            fine_tuned_model="",
            success=False,
            error=f"服务器内部错误: {str(e)}"
        )

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy",
        service="finance-chatbot",
        version="1.0.0",
        database_connected=True,
        nlp_model_loaded=True,
        uptime=time.time() - start_time
    )

@app.get("/statistics", response_model=StatisticsResponse)
async def statistics():
    stats = db_handler.get_statistics()
    return StatisticsResponse(
        total_sessions=stats['total_sessions'],
        total_messages=stats['total_messages'],
        average_response_time=0.5,
        top_intents=stats['top_intents'],
        daily_active_users=stats['daily_active_users']
    )

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    info = dialogue_manager.get_session_info(session_id)
    if not info:
        raise HTTPException(status_code=404, detail="会话不存在")
    return info

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if dialogue_manager.clear_session(session_id):
        return {"message": "会话已清除", "session_id": session_id}
    raise HTTPException(status_code=404, detail="会话不存在")

@app.get("/history/{session_id}")
async def get_history(session_id: str, limit: int = 50):
    history = db_handler.get_session_history(session_id, limit)
    return {"session_id": session_id, "history": history}

if __name__ == "__main__":
    import uvicorn
    print("🚀 启动金融问答机器人服务...")
    print("📡 服务地址: http://localhost:8000")
    print("⏳ 首次加载模型可能需要几分钟，请耐心等待...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=120,
        access_log=True
    )
