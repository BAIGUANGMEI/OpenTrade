const JSON_HEADERS = { "Content-Type": "application/json" };

async function request(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export const api = {
  getHealth: () => request("/api/health"),
  getTickers: () => request("/api/market/tickers"),
  getKlines: (symbol, interval = "1m", limit = 60) =>
    request(`/api/market/klines/${symbol}?interval=${interval}&limit=${limit}`),
  listModels: () => request("/api/models"),
  createModel: (payload) =>
    request("/api/models", {
      method: "POST",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    }),
  updateModel: (id, payload) =>
    request(`/api/models/${id}`, {
      method: "PUT",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    }),
  deleteModel: (id) => request(`/api/models/${id}`, { method: "DELETE" }),
  getDecisions: () => request("/api/decisions?limit=50"),
  runDecisionCycle: () => request("/api/decisions/run", { method: "POST" }),
  getPortfolioOverview: () => request("/api/portfolio/overview"),
  getNavSeries: (modelId, limit = 100) => request(`/api/portfolio/nav/${modelId}?limit=${limit}`),
  getStrategySettings: () => request("/api/strategies/settings"),
  updateStrategySettings: (payload) =>
    request("/api/strategies/settings", {
      method: "PUT",
      headers: JSON_HEADERS,
      body: JSON.stringify(payload),
    }),
  getStrategyRuns: () => request("/api/strategies/runs?limit=30"),
  getSchedulerState: () => request("/api/strategies/state"),
  resetTradingData: () => request("/api/strategies/reset", { method: "POST" }),
};
