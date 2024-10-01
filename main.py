import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Float, DateTime
from sqlalchemy.sql import func
import logging
from datetime import datetime
from pydantic import BaseModel
import json
import re
import ssl
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создаем объект Database
database = Database(DATABASE_URL)

# Метаданные для создания таблицы
metadata = MetaData()

# Определяем таблицу для хранения чисел
numbers_table = Table(
    "numbers",
    metadata,
    Column("id", Float, primary_key=True, autoincrement=True),
    Column("value", Float),
    Column("timestamp", DateTime, server_default=func.now())
)

# Создаем движок для взаимодействия с базой
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://drewnja.xyz", "https://94.131.123.104", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

previous_egorov_coeff = None
previous_lesson_coeff = None

# Функции для работы с базой данных
async def save_number_to_db(value: float):
    query = numbers_table.insert().values(value=value)
    await database.execute(query)

async def get_all_numbers():
    query = numbers_table.select().order_by(numbers_table.c.timestamp.desc())
    return await database.fetch_all(query)

# Pydantic модель для данных Egorov
class EgorovData(BaseModel):
    egorov_para: bool
    egorov_day: bool

# HTTP эндпоинты
@app.get("/", summary="Welcome Message", description="Returns a welcome message for the WebSocket random number generator.")
async def root():
    logging.info("Root endpoint accessed.")
    return {"message": "Welcome to the WebSocket random number generator!"}

@app.get("/initial-data")
async def get_initial_data():
    logging.info("Initial data requested.")
    all_numbers = await get_all_numbers()
    all_numbers_values = [row['value'] for row in all_numbers]
    return all_numbers_values

@app.post("/egorov-data")
async def set_egorov_data(data: EgorovData):
    logging.info(f"Egorov data received: para={data.egorov_para}, day={data.egorov_day}")
    
    # Логика обработки данных может быть добавлена здесь
    return {"message": "Data received", "egorov_para": data.egorov_para, "egorov_day": data.egorov_day}

# WebSocket эндпоинт
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global previous_egorov_coeff, previous_lesson_coeff
    
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
            Egorov_coeff = (count_today_events(ical_data, today) / 10) + 1
            if Egorov_coeff == 0:
                Egorov_coeff = 1  # Если нет занятий, присваиваем 1

            current_time = datetime.now()

            # Проверяем, идет ли сейчас пара
            if is_lesson_now(ical_data, current_time):
                lesson_coeff = 1.25
            else:
                lesson_coeff = 1    

            # Только логируем при изменении коэффициентов
            if Egorov_coeff != previous_egorov_coeff or lesson_coeff != previous_lesson_coeff:
                logging.info(f"Egorov_coeff changed: {Egorov_coeff}, Lesson_coeff changed: {lesson_coeff}")
                previous_egorov_coeff = Egorov_coeff
                previous_lesson_coeff = lesson_coeff

            # Генерация случайного числа
            random_number = random.randint(1, 150) / 100
            point_value = 5 * Egorov_coeff * lesson_coeff + random_number
            
            # Сохраняем значение в базу данных
            await save_number_to_db(point_value)
            
            # Получаем все значения из базы данных
            all_numbers = await get_all_numbers()
            all_numbers_values = [row['value'] for row in all_numbers]
            
            # Отправляем данные через WebSocket
            await websocket.send_json(all_numbers_values)

            # Ожидание 1 секунды
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logging.warning("WebSocket disconnected")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        logging.info("WebSocket connection closed")

# Функции для работы с iCalendar
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

# События старта и завершения приложения
@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    
    if os.environ.get('ENVIRONMENT') == 'production':
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain("cert.pem", "key.pem")
        uvicorn.run(app, host="0.0.0.0", port=8443, ssl=ssl_context)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080)  # Изменён порт на 8080 для разработки
