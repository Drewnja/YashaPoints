import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse
import ssl
import os

app = FastAPI()

# Update CORS middleware to allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://drewnja.xyz", "https://94.131.123.104", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store the last 100 numbers
last_100_numbers = []

# Function to save numbers to a file
def save_numbers():
    with open("numbers.json", "w") as f:
        json.dump(last_100_numbers, f)

# Function to load numbers from a file
def load_numbers():
    global last_100_numbers
    try:
        with open("numbers.json", "r") as f:
            last_100_numbers = json.load(f)
    except FileNotFoundError:
        last_100_numbers = []

# Load numbers on startup
load_numbers()

# HTTP endpoint for Swagger
@app.get("/", summary="Welcome Message", description="Returns a welcome message for the WebSocket random number generator.")
async def root():
    return {"message": "Welcome to the WebSocket random number generator!"}

@app.get("/initial-data")
async def get_initial_data():
    return last_100_numbers

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Generate a random number between 1 and 100
            random_number = random.randint(1, 100)
            
            # Add the new number to the list
            last_100_numbers.append(random_number)
            
            # Keep only the last 100 numbers in the list
            if len(last_100_numbers) > 100:
                last_100_numbers.pop(0)
            
            # Save numbers to file
            save_numbers()
            
            # Send the last 100 numbers as a JSON array
            await websocket.send_json(last_100_numbers)
            
            # Wait for 1 second before generating the next number
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print("WebSocket connection closed")

if __name__ == "__main__":
    import uvicorn
    
    if os.environ.get('ENVIRONMENT') == 'production':
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain("cert.pem", "key.pem")
        uvicorn.run(app, host="0.0.0.0", port=8443, ssl=ssl_context)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080)  # Changed port to 8080 for development

