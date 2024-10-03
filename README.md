# Балл Вкусно и точка

This project displays real-time price data for "Балл финашки" using Vue.js and Chart.js, with a WebSocket connection to a backend server.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

1. **Node.js**: This project requires Node.js version 14.x or later.

   To install Node.js:
   - Visit the official [Node.js website](https://nodejs.org/)
   - Download and install the LTS (Long Term Support) version for your operating system
   - Verify the installation by running these commands in your terminal:
     ```
     node --version
     npm --version
     ```

2. **Vue CLI**: This project uses Vue CLI for development.

   To install Vue CLI globally, run:
   ```
   npm install -g @vue/cli
   ```

## Getting Started

Follow these steps to set up and run the project:

1. **Clone the repository**
   ```
   git clone https://your-repository-url.git
   cd YashaPoints
   ```

2. **Install dependencies**
   ```
   npm install
   ```

3. **Start the development server**
   ```
   npm run serve
   ```

4. **Open the application**
   
   Open your web browser and navigate to `http://localhost:8080` (or the port shown in your terminal).


## Database Configuration
The backend server relies on a database connection, which is configured via the .env file. You need to update the DATABASE_URL environment variable in the .env file with your actual database credentials.
```
DATABASE_URL=postgresql://name:pass@host/db_name
```
Replace name with your database username, pass with your password, host with the database host, and db_name with the name of your database.

## Backend Setup

This frontend application requires a backend server to provide real-time data. Ensure your backend server is running and accessible at `http://localhost:8000`.

To start the backend server using Uvicorn, run the following command in your backend project directory:

```
uvicorn main:app --reload
```

This command starts the Uvicorn server with auto-reload enabled, which is useful for development. Make sure you have Uvicorn installed (`pip install uvicorn`) before running this command.

## Project Structure

- `src/App.vue`: The main component containing the chart and WebSocket logic
- `public/index.html`: The HTML template
- Other configuration files: `package.json`, `vue.config.js`, etc.

## Available Scripts

In the project directory, you can run:

- `npm run serve`: Runs the app in development mode
- `npm run build`: Builds the app for production
- `npm run lint`: Lints and fixes files

## Customization

You can customize the application by modifying the `App.vue` file. Adjust the chart options, styling, or add new features as needed.

## Deployment

To deploy the application:

1. Build the project:
   ```
   npm run build
   ```

2. The built files will be in the `dist/` directory. You can serve these files using any static file server.

## Troubleshooting

- If you encounter WebSocket connection issues, ensure your backend server is running and the WebSocket URL in `App.vue` is correct.
- For chart-related issues, refer to the [Chart.js documentation](https://www.chartjs.org/docs/latest/).

## API Endpoints Documentation

This document describes the available API endpoints for interacting with the server, fetching data, and handling WebSocket connections.

---

### 1. **GET /**

**Description:**  
Returns a welcome message, confirming that the WebSocket random number generator is active.

**Response:**
```json
{
  "message": "Welcome to the WebSocket random number generator!"
}
```

---

### 2. **GET /initial-data**

**Description:**  
Fetches all current values from the database, ordered by timestamp.

**Response:**
```json
[
  25.0,
  15.7,
  ...
]
```

---

### 3. **POST /egorov-data**

**Description:**  
Accepts data for `egorov_para` and `egorov_day`, logs the values, and can be used for further logic.

**Request Body:**
```json
{
  "egorov_para": true,
  "egorov_day": false
}
```

**Response:**
```json
{
  "message": "Data received",
  "egorov_para": true,
  "egorov_day": false
}
```

---

### 4. **GET /api/prices/{coinId}**

**Description:**  
Returns historical price data for the specified coin (`coinId`) within a given time range.

**Example Request:**
```bash
GET /api/prices/BTC?start=1630454400&end=1633046400
```

**Response:**
```json
[
  {"timestamp": 1630454400, "price": 45000.0},
  {"timestamp": 1630464400, "price": 45200.0},
  ...
]
```

---

### 5. **POST /api/prices/{coinId}**

**Description:**  
Inserts new price data for a specified coin (`coinId`).

**Request Body:**
```json
{
  "timestamp": 1630454400,
  "price": 45000.0
}
```

**Response:**
```json
{
  "message": "Price data inserted successfully"
}
```

---

### 6. **DELETE /api/prices/{coinId}**

**Description:**  
Deletes all historical price data for the specified coin (`coinId`).

**Response:**
```json
{
  "message": "All price data deleted for coinId BTC"
}
```

---

### 7. **GET /ws (WebSocket)**

**Description:**  
Connects via WebSocket to receive real-time updates on new price data. When new data is added to the database, it is pushed to all connected clients.

**Client-side usage example (JavaScript):**
```javascript
const ws = new WebSocket("ws://localhost:8080/ws");

ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

---

### 8. **GET /api/monitor/status**

**Description:**  
Fetches the current status of the application, including the number of active WebSocket connections.

**Response:**
```json
{
  "status": "ok",
  "active_connections": 5
}
```

---

### 9. **GET /api/logs**

**Description:**  
Returns the latest logs from the application for debugging purposes.

**Response (Plaintext):**
```plaintext
[2024-10-03 20:38:18,964] INFO: WebSocket connected
[2024-10-03 20:38:19,015] ERROR: WebSocket error: name 'WebSocketState' is not defined
...
```

---

This documentation provides an overview of the key endpoints, including methods for handling price data, monitoring system status, and establishing WebSocket connections.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)