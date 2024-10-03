import random
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, Float, DateTime, String, Integer
from sqlalchemy.sql import func
import logging
from datetime import datetime
from pydantic import BaseModel
import subprocess
import sys
import re
import ssl
import os
from dotenv import load_dotenv
from typing import List, Optional
from starlette.websockets import WebSocketState  # Correct import for WebSocketState

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# Initialize the Database object
database = Database(DATABASE_URL)

# Initialize SQLAlchemy metadata
metadata = MetaData()

# Define table for storing historical point_value data
point_value_prices_table = Table(
    "point_value_prices",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", DateTime, server_default=func.now(), index=True),
    Column("price", Float, nullable=False)
)

# Optionally, retain the 'numbers' table if needed
numbers_table = Table(
    "numbers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("value", Float),
    Column("timestamp", DateTime, server_default=func.now())
)

# Create the database engine and create tables
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI(
    title="Point Value API",
    description="API for managing and monitoring point_value data with real-time updates.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://drewnja.xyz",
        "https://94.131.123.104",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging to write to a file
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Global variables for coefficients
previous_egorov_coeff: Optional[float] = None
previous_lesson_coeff: Optional[float] = None

# Connection Manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"WebSocket disconnected: {websocket.client}")

    async def broadcast(self, message: dict):
        to_remove = []
        for connection in self.active_connections:
            if connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logging.exception(f"Error sending message to {connection.client}: {e}")
                    to_remove.append(connection)
            else:
                to_remove.append(connection)
        for conn in to_remove:
            self.disconnect(conn)

manager = ConnectionManager()

# Pydantic models
class EgorovData(BaseModel):
    egorov_para: bool
    egorov_day: bool

class PriceData(BaseModel):
    timestamp: datetime
    price: float

class StatusResponse(BaseModel):
    status: str
    active_websockets: int

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    message: str

# Database interaction functions
async def save_point_value(price: float):
    query = point_value_prices_table.insert().values(price=price)
    await database.execute(query)

async def get_all_point_values(limit: int = 100, offset: int = 0) -> List[PriceData]:
    query = point_value_prices_table.select().order_by(point_value_prices_table.c.timestamp.desc()).limit(limit).offset(offset)
    rows = await database.fetch_all(query)
    return [PriceData(timestamp=row["timestamp"], price=row["price"]) for row in rows]

async def get_latest_point_value() -> Optional[PriceData]:
    query = point_value_prices_table.select().order_by(point_value_prices_table.c.timestamp.desc()).limit(1)
    row = await database.fetch_one(query)
    if row:
        return PriceData(timestamp=row["timestamp"], price=row["price"])
    return None

async def clear_historical_data():
    query = point_value_prices_table.delete()
    await database.execute(query)

# Application Endpoints

@app.get("/", summary="Welcome Message", tags=["General"])
async def root():
    logging.info("Root endpoint accessed.")
    return {"message": "Welcome to the Point Value API!"}

@app.get("/initial-data", summary="Get Initial Data", tags=["Data Retrieval"])
async def get_initial_data():
    logging.info("Initial data requested.")
    all_numbers = await get_all_point_values(limit=10)
    return all_numbers

@app.post("/egorov-data", summary="Set Egorov Data", tags=["Data Management"])
async def set_egorov_data(data: EgorovData):
    logging.info(f"Egorov data received: para={data.egorov_para}, day={data.egorov_day}")
    # Placeholder for processing Egorov data
    return {"message": "Data received", "egorov_para": data.egorov_para, "egorov_day": data.egorov_day}

@app.get("/api/prices", response_model=List[PriceData], summary="Fetch Historical Prices", tags=["Data Retrieval"])
async def get_point_value_prices(
    start: datetime,
    end: datetime,
    limit: int = 100,
    offset: int = 0
):
    if start > end:
        raise HTTPException(status_code=400, detail="Start time must be before end time.")
    
    query = point_value_prices_table.select().where(
        (point_value_prices_table.c.timestamp >= start) &
        (point_value_prices_table.c.timestamp <= end)
    ).order_by(point_value_prices_table.c.timestamp.asc()).limit(limit).offset(offset)
    
    rows = await database.fetch_all(query)
    return [PriceData(timestamp=row["timestamp"], price=row["price"]) for row in rows]

@app.get("/api/prices/latest", response_model=PriceData, summary="Get Latest Price", tags=["Data Retrieval"])
async def get_latest_price():
    latest = await get_latest_point_value()
    if latest:
        return latest
    raise HTTPException(status_code=404, detail="No point_value data found.")

@app.delete("/api/prices", summary="Clear Historical Prices", tags=["Data Management"])
async def delete_historical_prices():
    await clear_historical_data()
    logging.info("All historical point_value data cleared.")
    return {"message": "All historical point_value data has been cleared."}

@app.get("/status", response_model=StatusResponse, summary="Application Status", tags=["Monitoring"])
async def get_status():
    active_ws = len(manager.active_connections)
    return StatusResponse(status="running", active_websockets=active_ws)

@app.get("/logs", response_model=List[LogEntry], summary="Retrieve Logs", tags=["Monitoring"])
async def get_logs(limit: int = 100):
    log_file = "app.log"  # Ensure logging is configured to write to this file
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Log file not found.")
    
    with open(log_file, "r") as f:
        lines = f.readlines()
    
    # Parse log lines into LogEntry models
    log_entries = []
    for line in lines[-limit:]:
        try:
            parts = line.strip().split(" - ", 2)
            if len(parts) < 3:
                continue  # Skip malformed lines
            timestamp_str, level, message = parts
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            log_entries.append(LogEntry(timestamp=timestamp, level=level, message=message))
        except ValueError:
            continue  # Skip malformed lines
    
    return log_entries

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive by waiting for a message or ping
            # You can customize this behavior based on your requirements
            data = await websocket.receive_text()
            logging.info(f"Received message from {websocket.client}: {data}")
            # Echo the received message or handle accordingly
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logging.warning("WebSocket disconnected")
    except Exception as e:
        logging.exception(f"WebSocket error: {e}")
        manager.disconnect(websocket)
    finally:
        manager.disconnect(websocket)

# Background Task for Data Ingestion
async def data_ingestion_task():
    global previous_egorov_coeff, previous_lesson_coeff
    while True:
        try:
            # Path to the iCalendar file (replace with the actual path)
            ical_path = "coefficents/RUZ_30.09.2024-06.10.2024_.ics"
            
            # Current date in YYYYMMDD format
            today = datetime.now().strftime('%Y%m%d')

            # Load calendar data
            ical_data = load_icalendar(ical_path)
            if not ical_data:
                logging.error("iCalendar data could not be loaded.")
                await asyncio.sleep(60)  # Retry after 60 seconds
                continue

            # Count today's events
            Egorov_coeff = (count_today_events(ical_data, today) / 10) + 1
            Egorov_coeff = Egorov_coeff if Egorov_coeff != 0 else 1  # Default to 1 if no events

            current_time = datetime.now()

            # Check if a lesson is ongoing
            lesson_coeff = 1.25 if is_lesson_now(ical_data, current_time) else 1

            # Log changes in coefficients
            if Egorov_coeff != previous_egorov_coeff or lesson_coeff != previous_lesson_coeff:
                logging.info(f"Egorov_coeff changed: {Egorov_coeff}, Lesson_coeff changed: {lesson_coeff}")
                previous_egorov_coeff = Egorov_coeff
                previous_lesson_coeff = lesson_coeff

            # Generate random number
            random_number = random.randint(1, 150) / 100
            point_value = 5 * Egorov_coeff * lesson_coeff + random_number

            # Save to database
            await save_point_value(point_value)
            logging.info(f"New point_value saved: {point_value}")

            # Create message for clients
            message = {"timestamp": datetime.now().isoformat(), "price": point_value}

            # Broadcast to all connected clients
            await manager.broadcast(message)

            # Wait for 1 second before next update
            await asyncio.sleep(1)
        except Exception as e:
            logging.exception(f"Data ingestion error: {e}")
            await asyncio.sleep(60)  # Wait before retrying

# Functions for handling iCalendar data
def load_icalendar(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logging.error(f"iCalendar file not found: {file_path}")
    except Exception as e:
        logging.error(f"Error loading iCalendar file: {e}")
    return ""

def count_today_events(ical_data: str, today: str) -> int:
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ical_data, re.DOTALL)
    today_events = 0
    for event in events:
        dtstart_match = re.search(r"DTSTART:(\d+T\d+)", event)
        if dtstart_match:
            dtstart = dtstart_match.group(1)
            event_date = dtstart[:8]
            if event_date == today:
                today_events += 1
    return today_events

def is_lesson_now(ical_data: str, current_time: datetime) -> bool:
    events = re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ical_data, re.DOTALL)
    for event in events:
        dtstart_match = re.search(r"DTSTART:(\d+T\d+)", event)
        dtend_match = re.search(r"DTEND:(\d+T\d+)", event)
        if dtstart_match and dtend_match:
            dtstart = dtstart_match.group(1)
            dtend = dtend_match.group(1)
            try:
                lesson_start = datetime.strptime(dtstart, '%Y%m%dT%H%M%S')
                lesson_end = datetime.strptime(dtend, '%Y%m%dT%H%M%S')
            except ValueError as ve:
                logging.error(f"Date parsing error: {ve}")
                continue
            current_time_trimmed = current_time.replace(microsecond=0)
            if lesson_start <= current_time_trimmed <= lesson_end:
                return True
    return False

# Startup and Shutdown Events
# Global variable to store the subprocess
ical_process = None

@app.on_event("startup")
async def startup_event():
    # Connect to the database
    await database.connect()
    logging.info("Connected to the database.")

    # Start the icalupdate.py script if it exists
    global ical_process
    script_path = os.path.join(os.path.dirname(__file__), "icalupdate.py")
    if os.path.exists(script_path):
        try:
            ical_process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(script_path),
                env=os.environ.copy()
            )
            logging.info(f"Script {script_path} started with PID {ical_process.pid}.")
        except Exception as e:
            logging.exception(f"Failed to start script {script_path}: {e}")
    else:
        logging.error(f"Script {script_path} not found.")

    # Start the background data ingestion task
    asyncio.create_task(data_ingestion_task())
    logging.info("Data ingestion task started.")

@app.on_event("shutdown")
async def shutdown_event():
    # Disconnect from the database
    await database.disconnect()
    logging.info("Disconnected from the database.")

    # Terminate the icalupdate.py script if it's running
    global ical_process
    if ical_process:
        try:
            ical_process.terminate()
            ical_process.wait(timeout=10)
            logging.info(f"Script {ical_process.pid} terminated successfully.")
        except subprocess.TimeoutExpired:
            ical_process.kill()
            logging.warning(f"Script {ical_process.pid} killed after timeout.")
        except Exception as e:
            logging.exception(f"Error terminating script {ical_process.pid}: {e}")

# Optional Endpoint to Trigger Manual Data Ingestion
@app.post("/api/prices/ingest", summary="Manual Data Ingestion", tags=["Data Management"])
async def manual_data_ingest():
    # Implement your data ingestion logic here
    global previous_egorov_coeff, previous_lesson_coeff

    ical_path = "coefficients/schedule.ics"
    today = datetime.now().strftime('%Y%m%d')
    ical_data = load_icalendar(ical_path)

    if not ical_data:
        raise HTTPException(status_code=500, detail="Failed to load iCalendar data.")

    Egorov_coeff = (count_today_events(ical_data, today) / 10) + 1
    Egorov_coeff = Egorov_coeff if Egorov_coeff != 0 else 1

    current_time = datetime.now()

    lesson_coeff = 1.25 if is_lesson_now(ical_data, current_time) else 1

    if Egorov_coeff != previous_egorov_coeff or lesson_coeff != previous_lesson_coeff:
        logging.info(f"Egorov_coeff changed: {Egorov_coeff}, Lesson_coeff changed: {lesson_coeff}")
        previous_egorov_coeff = Egorov_coeff
        previous_lesson_coeff = lesson_coeff

    random_number = random.randint(1, 150) / 100
    point_value = 5 * Egorov_coeff * lesson_coeff + random_number

    await save_point_value(point_value)
    logging.info(f"New point_value saved via manual ingestion: {point_value}")

    message = {"timestamp": datetime.now().isoformat(), "price": point_value}
    await manager.broadcast(message)

    return {"message": "Manual data ingestion successful.", "data": message}

# Run the application using Uvicorn
if __name__ == "__main__":
    import uvicorn

    # Determine if the environment is production based on an environment variable
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

    if ENVIRONMENT == 'production':
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # Ensure you have the certificate and key files
        cert_file = "cert.pem"
        key_file = "key.pem"
        if os.path.exists(cert_file) and os.path.exists(key_file):
            ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)
            uvicorn.run(app, host="0.0.0.0", port=8443, ssl=ssl_context)
        else:
            logging.error("SSL certificate or key file not found. Running without SSL.")
            uvicorn.run(app, host="0.0.0.0", port=8443)
    else:
        uvicorn.run(app, host="0.0.0.0", port=8080)
