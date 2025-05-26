const ws = new WebSocket("ws://localhost:8080");

ws.onopen = () => {
  ws.send(JSON.stringify({
    jsonrpc: "2.0",
    method: "ls",
    params: { args: ["-la"] },
    id: 1
  }));
};

ws.onmessage = (e) => {
  const res = JSON.parse(e.data);
  console.log(res.result?.stdout || res.error);
  ws.close();
};
