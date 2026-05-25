import os

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app.chatbot import EVChatbot


DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ev_database.json")
chatbot = EVChatbot(db_path=DB_FILE)

app = FastAPI(
    title="EV NLP Consulting Chatbot API",
    description="Lightweight Vietnamese NLP pipeline EV chatbot optimized for Raspberry Pi 4",
    version="1.1.0",
)


class ChatRequest(BaseModel):
    message: str


class CarRequest(BaseModel):
    name: str
    price: float
    range: int


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Tin nhắn không được để trống")
    try:
        return chatbot.get_response(req.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {exc}")


@app.get("/api/database")
async def get_database():
    return chatbot.db.get_all()


@app.post("/api/database")
async def update_database(req: CarRequest):
    if not req.name.strip():
        raise HTTPException(status_code=400, detail="Tên xe không được để trống")
    if req.price <= 0 or req.range <= 0:
        raise HTTPException(status_code=400, detail="Giá và quãng đường phải lớn hơn 0")

    try:
        car = chatbot.db.upsert(req.name, req.price, req.range)
        return {"status": "success", "data": car}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi lưu trữ: {exc}")


@app.delete("/api/database/{name}")
async def delete_car(name: str):
    try:
        success = chatbot.db.delete(name)
        if success:
            return {"status": "success", "message": f"Đã xóa xe {name}"}
        raise HTTPException(status_code=404, detail=f"Không tìm thấy xe {name} trong database")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lỗi: {exc}")


PUBLIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public")


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(PUBLIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>Giao diện Web chưa được khởi tạo.</h1>", status_code=404)
    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/css/style.css")
async def serve_css():
    css_path = os.path.join(PUBLIC_DIR, "css", "style.css")
    if not os.path.exists(css_path):
        return Response(status_code=404)
    with open(css_path, "r", encoding="utf-8") as f:
        return Response(f.read(), media_type="text/css")


@app.get("/js/main.js")
async def serve_js():
    js_path = os.path.join(PUBLIC_DIR, "js", "main.js")
    if not os.path.exists(js_path):
        return Response(status_code=404)
    with open(js_path, "r", encoding="utf-8") as f:
        return Response(f.read(), media_type="application/javascript")
