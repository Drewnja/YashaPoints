import random
import asyncio
from fastapi import FastAPI, WebSocket

app = FastAPI()

# HTTP endpoint for Swagger
@app.get("/", summary="Welcome Message", description="Returns a welcome message for the WebSocket random number generator.")
async def root():
    return {"message": "Welcome to the WebSocket random number generator!"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    last_100_numbers = []  # List to store the last 100 random numbers
    try:
        while True:
            # Generate a random number between 1 and 100
            random_number = random.randint(1, 100)
            
            # Add the new number to the list
            last_100_numbers.append(random_number)
            
            # Keep only the last 100 numbers in the list
            if len(last_100_numbers) > 100:
                last_100_numbers.pop(0)
            
            # Send the last 100 numbers as an array
            await websocket.send_text(str(last_100_numbers))
            
            # Wait for 1 seconds before generating the next number
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Connection closed: {e}")
    finally:
        await websocket.close()

