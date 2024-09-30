<template>
  <div id="app">
    <h1>{{ title }}</h1>
    <p>{{ currentPrice }} Балл финашки</p>
    <div class="chart-container" ref="chartContainer"></div>
    <p v-if="connectionStatus" :class="connectionStatus.toLowerCase()">
      {{ connectionStatus }}
    </p>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import { createChart } from 'lightweight-charts';

export default {
  name: 'App',
  setup() {
    const title = ref('Балл Вкусно и точка');
    const currentPrice = ref(0);
    const chartContainer = ref(null);
    const priceData = ref([]);
    let chart = null;
    let candleSeries = null;
    let socket = null;
    let previousPrice = null;

    const connectionStatus = ref('');

    const isDevelopment = process.env.NODE_ENV === 'development';
    const wsProtocol = isDevelopment ? 'ws' : 'wss';
    const wsHost = isDevelopment ? 'localhost:8443' : '94.131.123.104:8443';
    const wsUrl = `${wsProtocol}://${wsHost}/ws`;

    const createCandlestickChart = () => {
      if (chart) {
        chart.remove();
      }

      chart = createChart(chartContainer.value, {
        width: chartContainer.value.clientWidth,
        height: chartContainer.value.clientHeight,
        layout: {
          background: { type: 'solid', color: '#1a1a1a' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        crosshair: {
          mode: 0,
        },
        rightPriceScale: {
          borderColor: '#2B2B43',
        },
        timeScale: {
          borderColor: '#2B2B43',
          timeVisible: true,
          secondsVisible: false,
        },
      });

      candleSeries = chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      });

      updateChart();
    };

    const updateChart = () => {
      if (candleSeries && priceData.value.length > 0) {
        candleSeries.setData(priceData.value);
        const lastCandle = priceData.value[priceData.value.length - 1];
        currentPrice.value = lastCandle.close.toFixed(2);
        chart.timeScale().fitContent();
      }
    };

    const connectWebSocket = () => {
      connectionStatus.value = 'Connecting...';
      console.log('Attempting to connect to WebSocket:', wsUrl);
      socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket connection established');
        connectionStatus.value = 'Connected';
      };

      socket.onmessage = (event) => {
        const newData = JSON.parse(event.data);
        if (Array.isArray(newData) && newData.length > 0) {
          priceData.value = newData.map((price, index) => {
            const time = Math.floor(Date.now() / 1000) - (newData.length - 1 - index);
            const open = previousPrice !== null ? previousPrice : price;
            const close = price;
            const highLowOffset = Math.abs((close - open) * 0.1); // 10% of the price difference

            const candlestick = {
              time,
              open,
              close,
              high: Math.max(open, close) + highLowOffset,
              low: Math.min(open, close) - highLowOffset
            };

            previousPrice = close;
            return candlestick;
          });
          updateChart();
        }
      };

      socket.onclose = (event) => {
        console.log('WebSocket connection closed:', event.reason);
        connectionStatus.value = 'Disconnected. Retrying...';
        setTimeout(connectWebSocket, 5000);
      };

      socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        connectionStatus.value = 'Connection Error';
      };
    };

    onMounted(() => {
      createCandlestickChart();
      connectWebSocket();

      window.addEventListener('resize', createCandlestickChart);
    });

    onUnmounted(() => {
      if (socket) {
        socket.close();
      }
      if (chart) {
        chart.remove();
      }
      window.removeEventListener('resize', createCandlestickChart);
    });

    return {
      title,
      currentPrice,
      chartContainer,
      connectionStatus,
    };
  }
}
</script>

<style>
body {
  margin: 0;
  padding: 0;
  background-color: #1a1a1a;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

#app {
  background-color: #1a1a1a;
  color: #ffffff;
  font-family: Arial, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
  width: 100%;
  padding: 5vh 5vw;
  box-sizing: border-box;
}

h1 {
  font-size: 6vw;
  margin-bottom: 2vh;
  text-align: center;
}

p {
  font-size: 8vw;
  margin-bottom: 3vh;
  text-align: center;
}

.chart-container {
  width: 100%;
  height: 60vh;
  max-height: 400px;
}

@media (min-width: 768px) {
  h1 {
    font-size: 36px;
  }

  p {
    font-size: 48px;
  }

  .chart-container {
    max-width: 800px;
  }
}

.connected {
  color: #4caf50;
}

.disconnected {
  color: #f44336;
}

.connecting {
  color: #ffc107;
}

.connection-error {
  color: #ff5722;
}
</style>



