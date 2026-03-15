import { defineStore } from "pinia";

import { api } from "../services/api";

export const useMarketStore = defineStore("market", {
  state: () => ({
    tickers: [],
    scheduler: null,
    socket: null,
    connected: false,
  }),
  actions: {
    async refreshTickers() {
      this.tickers = await api.getTickers();
    },
    connect() {
      if (this.socket) {
        return;
      }
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      this.socket = new WebSocket(`${protocol}//${window.location.host}/ws/market`);
      this.socket.onopen = () => {
        this.connected = true;
        this.socket.send("subscribe");
      };
      this.socket.onmessage = (event) => {
        const payload = JSON.parse(event.data);
        if (payload.type === "tickers") {
          this.tickers = payload.data;
        }
      };
      this.socket.onclose = () => {
        this.connected = false;
        this.socket = null;
        window.setTimeout(() => this.connect(), 2000);
      };
    },
  },
});
