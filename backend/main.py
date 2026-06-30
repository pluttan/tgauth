from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import secrets
import time

app = FastAPI()

# Разрешаем запросы с фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Словарь для хранения кодов {код: (таймштамп, Telegram ID)}
codes = {}
EXPIRATION_TIME = 300  # 5 минут


class CodeRequest(BaseModel):
    code: str


@app.post("/verify")
def verify_code(data: CodeRequest):
    code = data.code.strip()
    if code in codes:
        timestamp, _ = codes[code]
        if time.time() - timestamp < EXPIRATION_TIME:
            del codes[code]  # Код используется один раз
            return {"success": True, "token": secrets.token_hex(16)}
    raise HTTPException(status_code=400, detail="Неверный или просроченный код")
