from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
from app.rag_chain import RAGService
import uuid

app = FastAPI()

# ✅ CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 必要に応じて制限可（例: ["http://localhost:3000"]）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag = RAGService()

# OpenAI互換のリクエストモデル
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = 4096

import time

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    query = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            query = msg.content
            break

    if not query:
        return {"error": "No user message found."}

    # RAGから返されるのがdictなら "result" だけ抜き出す
    rag_response = rag.ask(query)
    if isinstance(rag_response, dict):
        answer = rag_response.get("result", "（回答が見つかりませんでした）")
    else:
        answer = rag_response or "（回答が見つかりませんでした）"

    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


from fastapi.responses import JSONResponse

@app.get("/v1/models")
def list_models():
    return JSONResponse({
        "object": "list",
        "data": [
            {
                "id": "rag-local",
                "object": "model",
                "created": 0,
                "owned_by": "company",
            }
        ]
    })