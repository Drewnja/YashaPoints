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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)