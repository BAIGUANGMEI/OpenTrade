<template>
  <section>
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Observability</div>
        <h2 class="headline">Audit</h2>
        <p class="muted">Inspect structured decision output, fallback events, and model execution behavior.</p>
      </div>
      <button class="button" @click="load">Refresh</button>
    </div>

    <div class="stats-strip">
      <div class="stat-card">
        <div class="stat-label">Total Decisions</div>
        <div class="stat-value">{{ decisions.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Accepted</div>
        <div class="stat-value">{{ acceptedCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Fallback / Failed</div>
        <div class="stat-value">{{ fallbackCount }}</div>
      </div>
    </div>

    <DecisionLogTable :decisions="decisions" />
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import DecisionLogTable from "../components/DecisionLogTable.vue";
import { api } from "../services/api";

const decisions = ref([]);
const acceptedCount = computed(() => decisions.value.filter((item) => item.status === "accepted").length);
const fallbackCount = computed(() =>
  decisions.value.filter((item) => String(item.status).includes("fallback") || String(item.status).includes("failed")).length
);

async function load() {
  decisions.value = await api.getDecisions();
}

onMounted(load);
</script>
