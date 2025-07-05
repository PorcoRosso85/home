/**
 * WebSocket Server - モックなし実装
 * 実際のWebSocketサーバー（Deno）
 */

const PORT = 8080;
const clients = new Set<WebSocket>();

console.log(`WebSocket server starting on ws://localhost:${PORT}`);

Deno.serve({ port: PORT }, (req) => {
  if (req.headers.get("upgrade") !== "websocket") {
    return new Response("Not a websocket request", { status: 400 });
  }

  const { socket, response } = Deno.upgradeWebSocket(req);

  socket.addEventListener("open", () => {
    console.log("Client connected");
    clients.add(socket);
  });

  socket.addEventListener("message", (event) => {
    console.log("Received:", event.data);
    
    // 他のクライアントにブロードキャスト
    for (const client of clients) {
      if (client !== socket && client.readyState === WebSocket.OPEN) {
        client.send(event.data);
      }
    }
  });

  socket.addEventListener("close", () => {
    console.log("Client disconnected");
    clients.delete(socket);
  });

  return response;
});