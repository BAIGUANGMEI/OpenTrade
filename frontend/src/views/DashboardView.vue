<template>
  <section>
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Trading Desk</div>
        <h2 class="headline">Dashboard</h2>
        <p class="muted">Realtime market overview, model capital allocation, and latest AI trade decisions.</p>
      </div>
      <div class="actions">
        <button class="button" @click="refreshAll">Refresh</button>
      </div>
    </div>

    <MarketTickerPanel :tickers="marketStore.tickers" />

    <div class="split" style="margin-top: 16px">
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">AI Return Curve</div>
            <div class="panel-subtitle">Each model is redrawn from ordered NAV snapshots plus the latest marked NAV using `(NAV - capital) / capital`.</div>
          </div>
          <span class="tag">{{ navReturnSeries.length }} models</span>
        </div>
        <NavChart title="Return Curve" :series="navReturnSeries" y-axis-formatter="percent" />
      </div>
    </div>

    <div class="split" style="margin-top: 16px">
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Portfolio Overview</div>
            <div class="panel-subtitle">Capital distribution and current marked-to-market model performance.</div>
          </div>
          <span class="tag">{{ portfolio.models?.length || 0 }} models</span>
        </div>
        <div v-if="!(portfolio.models || []).length" class="empty-state">
          <strong>No portfolios yet</strong>
          <span class="muted">Add a model configuration to create an isolated paper account.</span>
        </div>
        <table v-else class="table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Cash</th>
              <th>Positions</th>
              <th>NAV</th>
              <th>Unrealized</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="model in portfolio.models || []" :key="model.model_config_id">
              <td>{{ model.model_name }}</td>
              <td>${{ Number(model.cash_balance).toFixed(2) }}</td>
              <td>${{ Number(model.positions_value).toFixed(2) }}</td>
              <td>${{ Number(model.total_nav).toFixed(2) }}</td>
              <td :class="model.unrealized_pnl >= 0 ? 'positive' : 'negative'">
                ${{ Number(model.unrealized_pnl).toFixed(2) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="split" style="margin-top: 16px">
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Open Positions</div>
            <div class="panel-subtitle">Live paper positions currently held across model books.</div>
          </div>
          <span class="tag">{{ openPositions }}</span>
        </div>
        <div v-if="!portfolio.positions?.length" class="empty-state">
          <strong>No active positions</strong>
          <span class="muted">Models are flat or have not placed any buy decisions yet.</span>
        </div>
        <div v-else class="key-value-list">
          <div v-for="position in sortedPositions" :key="`${position.model_config_id}-${position.symbol}`" class="key-value-item">
            <div>
              <div class="key-value">{{ position.symbol }}</div>
              <div class="key-label">{{ position.model_name || `Model #${position.model_config_id}` }}</div>
            </div>
            <div class="key-value">
              {{ Number(position.quantity).toFixed(4) }}
              <div class="key-label">Avg ${{ Number(position.avg_price).toFixed(2) }}</div>
            </div>
          </div>
        </div>
      </div>
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Recent Orders</div>
            <div class="panel-subtitle">Most recent filled paper executions created by accepted decisions.</div>
          </div>
          <span class="tag">{{ recentOrders.length }}</span>
        </div>
        <div v-if="!recentOrders.length" class="empty-state">
          <strong>No orders yet</strong>
          <span class="muted">Run a strategy cycle to generate the first simulated execution.</span>
        </div>
        <div v-else class="key-value-list">
          <div v-for="order in recentOrders" :key="order.id" class="key-value-item">
            <div>
              <div class="key-value">{{ order.symbol }}</div>
              <div class="key-label">{{ order.model_name || `Model #${order.model_config_id}` }}</div>
            </div>
            <div>
              <div class="key-label">{{ order.side }} at ${{ Number(order.price).toFixed(2) }}</div>
            </div>
            <div class="key-value">
              {{ Number(order.quantity).toFixed(4) }}
              <div class="key-label">{{ formatTime(order.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="section-stack" style="margin-top: 16px">
      <div class="panel-header">
        <div>
          <div class="panel-title">Recent Decisions</div>
          <div class="panel-subtitle">Structured model outputs with confidence, action sizing, and fallback status.</div>
        </div>
        <span class="tag">{{ latestDecisionTime }}</span>
      </div>
      <DecisionLogTable :decisions="decisions" />
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import DecisionLogTable from "../components/DecisionLogTable.vue";
import MarketTickerPanel from "../components/MarketTickerPanel.vue";
import NavChart from "../components/NavChart.vue";
import { api } from "../services/api";
import { useMarketStore } from "../stores/market";
import { useModelsStore } from "../stores/models";
import { formatDateTime, formatTime, toTimestamp } from "../utils/time";

const marketStore = useMarketStore();
const modelsStore = useModelsStore();
const portfolio = ref({ models: [], positions: [], recent_orders: [] });
const decisions = ref([]);
const navSeriesByModel = ref({});
let refreshTimer = null;

function calculateReturnPct(totalNav, capital) {
  const nav = Number(totalNav || 0);
  const initialCapital = Number(capital || 0);
  if (!initialCapital) {
    return 0;
  }
  return ((nav - initialCapital) / initialCapital) * 100;
}

function buildReturnSeries(model, rawPoints) {
  const capital = Number(model.initial_capital || 0);
  if (!capital) {
    return null;
  }

  const orderedPoints = [...(rawPoints || [])]
    .map((point) => ({
      created_at: point.created_at,
      total_nav: Number(point.total_nav || 0),
      ts: toTimestamp(point.created_at),
    }))
    .filter((point) => point.ts && Number.isFinite(point.total_nav))
    .sort((left, right) => left.ts - right.ts);

  const dedupedPoints = [];
  for (const point of orderedPoints) {
    const lastPoint = dedupedPoints[dedupedPoints.length - 1];
    if (lastPoint && lastPoint.ts === point.ts) {
      dedupedPoints[dedupedPoints.length - 1] = point;
    } else {
      dedupedPoints.push(point);
    }
  }

  const currentTimestamp = toTimestamp(portfolio.value.generated_at);
  const currentNav = Number(model.total_nav || 0);
  const lastPoint = dedupedPoints[dedupedPoints.length - 1];

  if (
    currentTimestamp &&
    Number.isFinite(currentNav) &&
    (!lastPoint || lastPoint.ts !== currentTimestamp || Math.abs(lastPoint.total_nav - currentNav) > 1e-9)
  ) {
    dedupedPoints.push({
      created_at: portfolio.value.generated_at,
      total_nav: currentNav,
      ts: currentTimestamp,
    });
  }

  if (!dedupedPoints.length && currentTimestamp && Number.isFinite(currentNav)) {
    dedupedPoints.push({
      created_at: portfolio.value.generated_at,
      total_nav: currentNav,
      ts: currentTimestamp,
    });
  }

  if (!dedupedPoints.length) {
    return null;
  }

  return {
    name: model.model_name,
    data: dedupedPoints.map((point) => [point.ts, calculateReturnPct(point.total_nav, capital)]),
  };
}

const openPositions = computed(() => (portfolio.value.positions || []).length);
const portfolioModels = computed(() => portfolio.value.models || []);
const navReturnSeries = computed(() =>
  portfolioModels.value
    .map((model) => buildReturnSeries(model, navSeriesByModel.value[model.model_config_id]))
    .filter(Boolean)
);
const sortedPositions = computed(() =>
  [...(portfolio.value.positions || [])]
    .sort((left, right) => {
      const leftName = left.model_name || "";
      const rightName = right.model_name || "";
      return leftName.localeCompare(rightName) || left.symbol.localeCompare(right.symbol);
    })
    .slice(0, 6)
);
const recentOrders = computed(() =>
  [...(portfolio.value.recent_orders || [])]
    .sort((left, right) => {
      const leftName = left.model_name || "";
      const rightName = right.model_name || "";
      return leftName.localeCompare(rightName) || toTimestamp(right.created_at) - toTimestamp(left.created_at);
    })
    .slice(0, 6)
);
const latestDecisionTime = computed(() =>
  decisions.value.length ? formatDateTime(decisions.value[0].created_at) : "No runs yet"
);

async function refreshAll() {
  await Promise.all([
    marketStore.refreshTickers(),
    modelsStore.fetchAll(),
    loadPortfolio(),
    loadDecisions(),
  ]);
  await loadAllNav();
}

async function loadPortfolio() {
  portfolio.value = await api.getPortfolioOverview();
}

async function loadDecisions() {
  decisions.value = await api.getDecisions();
}

async function loadAllNav() {
  const entries = await Promise.all(
    portfolioModels.value.map(async (model) => [model.model_config_id, await api.getNavSeries(model.model_config_id)])
  );
  navSeriesByModel.value = Object.fromEntries(entries);
}

onMounted(async () => {
  marketStore.connect();
  await refreshAll();
  refreshTimer = window.setInterval(async () => {
    await Promise.all([loadPortfolio(), loadDecisions()]);
    await loadAllNav();
  }, 10000);
});

onBeforeUnmount(() => {
  if (refreshTimer) {
    window.clearInterval(refreshTimer);
  }
});
</script>
