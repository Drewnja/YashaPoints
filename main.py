import random
import asyncio
from fastapi import FastAPI, WebSocket

app = FastAPI()

# Добавляем HTTP эндпоинт для Swagger
@app.get("/")
async def root():
    return {"message": "Welcome to the WebSocket random number generator!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Генерируем случайное число от 1 до 100
            random_number = random.randint(1, 100)
            await websocket.send_text(str(random_number))
            await asyncio.sleep(2)  # Отправляем данные каждые 2 секунды
    except Exception as e:
        print(f"Connection closed: {e}")
    finally:
        await websocket.close()
