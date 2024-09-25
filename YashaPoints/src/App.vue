<template>
  <div id="app">
    <h1>{{ title }}</h1>
    <p>{{ currentPrice }} Балл финашки</p>
    <canvas ref="graph" width="800" height="400"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue';
import Chart from 'chart.js/auto';

export default {
  name: 'App',
  setup() {
    const title = ref('Балл Вкусно и точка');
    const currentPrice = ref(0);
    const graph = ref(null);
    const priceData = ref([]);
    let ws = null;
    let reconnectTimeout = null;
    let chart = null;

    const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    const apiUrl = isDevelopment ? 'http://localhost:8000' : 'https://94.131.123.104:8443';

    const createChart = () => {
      if (chart) {
        chart.destroy();
      }
      const ctx = graph.value.getContext('2d');
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: Array.from({ length: priceData.value.length }, (_, i) => i + 1),
          datasets: [{
            label: 'Балл финашки',
            data: priceData.value,
            borderColor: '#00ff00',
            tension: 0.1
          }]
        },
        options: {
          responsive: true,
          animation: false,
          scales: {
            y: {
              beginAtZero: false,
              suggestedMin: Math.min(...priceData.value) - 5,
              suggestedMax: Math.max(...priceData.value) + 5
            }
          }
        }
      });
    };

    const updateChart = () => {
      if (chart) {
        chart.data.labels = Array.from({ length: priceData.value.length }, (_, i) => i + 1);
        chart.data.datasets[0].data = priceData.value;
        chart.options.scales.y.suggestedMin = Math.min(...priceData.value) - 5;
        chart.options.scales.y.suggestedMax = Math.max(...priceData.value) + 5;
        chart.update();
      } else {
        createChart();
      }
    };

    const fetchInitialData = async () => {
      try {
        const response = await fetch(`${apiUrl}/initial-data`);
        const data = await response.json();
        priceData.value = data;
        if (data.length > 0) {
          currentPrice.value = data[data.length - 1].toFixed(2);
        }
        updateChart();
      } catch (error) {
        console.error('Error fetching initial data:', error);
      }
    };

    const connectWebSocket = () => {
      if (ws) {
        ws.close();
      }

      const wsUrl = isDevelopment ? 'ws://localhost:8000/ws' : 'wss://94.131.123.104:8443/ws';
      ws = new WebSocket(wsUrl);

      ws.onopen = (event) => {
        console.log("WebSocket connection established");
        if (reconnectTimeout) {
          clearTimeout(reconnectTimeout);
          reconnectTimeout = null;
        }
      };

      ws.onmessage = (event) => {
        try {
          const newPrices = JSON.parse(event.data);
          priceData.value = newPrices;
          if (newPrices.length > 0) {
            currentPrice.value = newPrices[newPrices.length - 1].toFixed(2);
          }
          updateChart();
        } catch (error) {
          console.error("Error parsing WebSocket data:", error);
        }
      };

      ws.onclose = (event) => {
        console.log("WebSocket closed:", event);
        reconnectTimeout = setTimeout(connectWebSocket, 5000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    };

    onMounted(async () => {
      await fetchInitialData();
      connectWebSocket();
    });

    onUnmounted(() => {
      if (ws) {
        ws.close();
      }
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (chart) {
        chart.destroy();
      }
    });

    return {
      title,
      currentPrice,
      graph,
      priceData
    };
  }
}
</script>

<style>
#app {
  background-color: #1a1a1a;
  color: #ffffff;
  font-family: Arial, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  margin: 0;
}

h1 {
  font-size: 36px;
  margin-bottom: 10px;
  text-align: center;
}

p {
  font-size: 48px;
  margin-bottom: 20px;
}

canvas {
  border: 1px solid #333;
}
</style>
