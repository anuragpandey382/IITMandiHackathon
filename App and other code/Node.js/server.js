import { WebSocket, WebSocketServer } from "ws";

const wss = new WebSocketServer({ port: 8080 });

wss.on("connection", (ws) => {
  ws.send('{"event":"connection","data":"connected"}');
  ws.on("message", (data, isbinary) => {
    // Broadcasting to other client except sender
    wss.clients.forEach((client) => {
      if (client != ws && client.readyState == WebSocket.OPEN) {
        client.send(data, { binary: false });
      }
    });
  });
});
