import { defineStore } from "pinia";

import { api } from "../services/api";

export const useModelsStore = defineStore("models", {
  state: () => ({
    items: [],
    loading: false,
  }),
  actions: {
    async fetchAll() {
      this.loading = true;
      try {
        this.items = await api.listModels();
      } finally {
        this.loading = false;
      }
    },
  },
});
