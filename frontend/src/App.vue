<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <span class="brand-badge">Market Intelligence</span>
        <h1>OpenTrade</h1>
        <p class="muted">AI-driven crypto research and paper execution workspace.</p>
      </div>
      <nav class="nav">
        <RouterLink to="/dashboard">Dashboard</RouterLink>
        <RouterLink to="/models">Models</RouterLink>
        <RouterLink to="/strategies">Strategies</RouterLink>
        <RouterLink to="/audit">Audit</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <strong>Coverage</strong>
        <div class="muted">Spot only: BTC, ETH, SOL</div>
      </div>
    </aside>
    <main class="content">
      <div class="surface">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { RouterLink, RouterView } from "vue-router";
</script>
