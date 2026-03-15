<template>
  <div class="ticker-grid">
    <article v-for="ticker in tickers" :key="ticker.symbol" class="card ticker-card compact">
      <div class="ticker-label">
        <div class="ticker-identity">
          <AssetLogo :symbol="ticker.symbol" />
          <div>
            <div class="ticker-symbol">{{ ticker.symbol.replace("USDT", "") }}</div>
            <div class="ticker-pair muted">{{ ticker.symbol }}</div>
          </div>
        </div>
        <span class="tag">Live</span>
      </div>
      <div class="ticker-price">${{ Number(ticker.price || 0).toFixed(2) }}</div>
      <div
        class="ticker-change"
        :class="Number(ticker.change_percent || 0) >= 0 ? 'positive' : 'negative'"
      >
        {{ Number(ticker.change_percent || 0).toFixed(2) }}%
      </div>
    </article>
  </div>
</template>

<script setup>
import AssetLogo from "./AssetLogo.vue";

defineProps({
  tickers: {
    type: Array,
    default: () => [],
  },
});
</script>
