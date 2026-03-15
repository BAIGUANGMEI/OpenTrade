<template>
  <span class="asset-logo" :class="logoClass" aria-hidden="true">
    <img :src="logoSrc" :alt="`${symbol} logo`" />
  </span>
</template>

<script setup>
import { computed } from "vue";

import bitcoinLogo from "../assets/img/Bitcoin.svg.png";
import ethereumLogo from "../assets/img/Ethereum_Logo.png";
import solanaLogo from "../assets/img/Solana_logo.png";

const props = defineProps({
  symbol: {
    type: String,
    required: true,
  },
});

const logoClass = computed(() => `asset-logo-${props.symbol.replace("USDT", "").toLowerCase()}`);
const logoSrc = computed(() => {
  if (props.symbol === "BTCUSDT") {
    return bitcoinLogo;
  }
  if (props.symbol === "ETHUSDT") {
    return ethereumLogo;
  }
  return solanaLogo;
});
</script>
