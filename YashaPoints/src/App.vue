<template>
  <div id="app">
    <h1>{{ title }}</h1>
    <p>{{ currentPrice }} Балл финашки</p>
    <div class="chart-container" ref="chartContainer"></div>
    <p v-if="connectionStatus" :class="connectionStatus.toLowerCase()">
      {{ connectionStatus }}
    </p>
    <p class="tick-counter">Ticks: {{ tickCount }}</p>
    <div class="raw-data-container">
      <button @click="toggleRawData" class="toggle-button">
        {{ showRawData ? 'Hide' : 'Show' }} Raw Data
      </button>
      <pre v-if="showRawData" class="raw-data">{{ rawData }}</pre>
    </div>
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
    const tickCount = ref(0);
    const rawData = ref('');
    const showRawData = ref(false);

    const wsUrl = 'wss://turk1.drewnja.xyz:8443/ws';

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
          tickCount.value++; // Increment tick count on each update
          rawData.value = JSON.stringify(newData, null, 2);
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

    const toggleRawData = () => {
      showRawData.value = !showRawData.value;
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
      tickCount,
      rawData,
      showRawData,
      toggleRawData,
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
  overflow: auto; /* Changed from hidden to auto */
}

#app {
  background-color: #1a1a1a;
  color: #ffffff;
  font-family: Arial, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  min-height: 100vh; /* Changed from height to min-height */
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

.raw-data-container {
  width: 100%;
  max-width: 800px;
  margin-top: 2vh;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.toggle-button {
  background-color: #4CAF50;
  border: none;
  color: white;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  margin: 4px 2px;
  cursor: pointer;
  border-radius: 4px;
}

.raw-data {
  background-color: #2c2c2c;
  color: #f0f0f0;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 200px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 14px;
  width: 100%; /* Added to ensure full width */
  box-sizing: border-box; /* Added to include padding in width calculation */
}

@media (max-width: 768px) {
  .raw-data {
    font-size: 12px;
  }
}

.tick-counter {
  font-size: 4vw;
  margin-top: 1vh;
  color: #888;
}

@media (min-width: 768px) {
  .tick-counter {
    font-size: 24px;
  }
}
</style>



