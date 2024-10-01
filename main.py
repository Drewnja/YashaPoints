import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import FileResponse
import ssl
import os
from datetime import datetime
import re 


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

# Function to load iCalendar and count today's events
def load_icalendar(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def count_today_events(ical_data, today):
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ical_data, re.DOTALL)

    # Считаем количество занятий на сегодня
    today_events = 0
    for event in events:
        dtstart_match = re.search(r"DTSTART:(\d+T\d+)", event)
        if dtstart_match:
            dtstart = dtstart_match.group(1)
            event_date = dtstart[:8]  # Извлекаем только дату (первые 8 символов)
            if event_date == today:
                today_events += 1

    return today_events
    
def is_lesson_now(ical_data, current_time):
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ical_data, re.DOTALL)
    
    for event in events:
        dtstart_match = re.search(r"DTSTART:(\d+T\d+)", event)
        dtend_match = re.search(r"DTEND:(\d+T\d+)", event)
        
        if dtstart_match and dtend_match:
            dtstart = dtstart_match.group(1)
            dtend = dtend_match.group(1)
            
            # Преобразуем дату и время в объекты datetime
            lesson_start = datetime.strptime(dtstart, '%Y%m%dT%H%M%S')
            lesson_end = datetime.strptime(dtend, '%Y%m%dT%H%M%S')
            current_time_trimmed = current_time.replace(microsecond=0)
            
            # Проверяем, попадает ли текущее время в интервал занятия
            if lesson_start <= current_time_trimmed <= lesson_end:
                return True
    
    return False

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

            # Путь к файлу календаря (замените на реальный путь)
            ical_path = "coefficents/RUZ_30.09.2024-06.10.2024_.ics"
            
            # Текущая дата
            today = datetime.now().strftime('%Y%m%d')

            # Загрузка данных календаря
            ical_data = load_icalendar(ical_path)

            # Подсчет количества занятий на сегодня
            Egorov_coeff = count_today_events(ical_data, today)
            if Egorov_coeff == 0:
                Egorov_coeff = 1  # Если нет занятий, присваиваем 1

            current_time = datetime.now()

            # Проверяем, идет ли сейчас пара
            if is_lesson_now(ical_data, current_time):
                lesson_coeff = 10
            else:
                lesson_coeff = 1    

            # Generate a random number between 1 and 100

            
            random_number = (random.randint(1, 10) / 3) * Egorov_coeff * lesson_coeff
            
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

