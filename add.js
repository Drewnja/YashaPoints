const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = function(event) {
    console.log("Received: " + event.data);
    // Здесь можно обновить элемент на странице с полученным числом
    document.getElementById('random-number').innerText = "Random number: " + event.data;
};

ws.onclose = function(event) {
    console.log("WebSocket closed: ", event);
};

ws.onerror = function(error) {
    console.log("WebSocket error: ", error);
};
