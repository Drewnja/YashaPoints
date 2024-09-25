import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

# Добавляем HTTP эндпоинт для Swagger
@app.get("/")
async def root():
    return {"message": "Welcome to the WebSocket random number generator!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        current_price = 20.0
        while True:
            # Generate a small random price change
            price_change = (random.random() - 0.5) * 2
            current_price += price_change
            await websocket.send_text(f"{current_price:.2f}")
            await asyncio.sleep(2)  # Send data every 2 seconds
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error in WebSocket connection: {e}")
