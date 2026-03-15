<template>
  <section>
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Provider Routing</div>
        <h2 class="headline">Models</h2>
        <p class="muted">Configure API credentials, provider adapters, and execution defaults for each AI model.</p>
      </div>
    </div>

    <div class="stats-strip">
      <div class="stat-card">
        <div class="stat-label">Configured Models</div>
        <div class="stat-value">{{ store.items.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Enabled</div>
        <div class="stat-value">{{ enabledCount }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Providers</div>
        <div class="stat-value">{{ providerCount }}</div>
      </div>
    </div>

    <div class="split split-models">
      <ModelConfigForm :initial-value="editingItem" @submit="saveModel" @cancel="editingItem = null" />
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Configured Models</div>
            <div class="panel-subtitle">Review connection health, routing provider, and strategy participation.</div>
          </div>
          <span class="tag">{{ store.items.length }} total</span>
        </div>
        <div v-if="!store.items.length" class="empty-state">
          <strong>No model connections yet</strong>
          <span class="muted">Create your first provider configuration to start testing AI decisions.</span>
        </div>
        <div v-else class="table-scroll">
          <table class="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Provider</th>
                <th>Model</th>
                <th>Base URL</th>
                <th>Key</th>
                <th>State</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in store.items" :key="item.id">
                <td>{{ item.name }}</td>
                <td>{{ item.provider || "-" }}</td>
                <td>{{ item.model }}</td>
                <td class="mono">{{ item.base_url }}</td>
                <td>{{ item.api_key_masked || "-" }}</td>
                <td>
                  <span class="status-pill" :class="item.enabled ? 'success' : 'warning'">
                    {{ item.enabled ? "enabled" : "disabled" }}
                  </span>
                </td>
                <td class="table-actions">
                  <button class="button secondary small" @click="editingItem = item">Edit</button>
                  <button class="button secondary small" @click="removeModel(item.id)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="grid-note">Disabled models stay saved but will not be routed into live strategy decisions.</div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";

import ModelConfigForm from "../components/ModelConfigForm.vue";
import { api } from "../services/api";
import { useModelsStore } from "../stores/models";

const store = useModelsStore();
const editingItem = ref(null);
const enabledCount = computed(() => store.items.filter((item) => item.enabled).length);
const providerCount = computed(() => new Set(store.items.map((item) => item.provider || "unknown")).size);

async function saveModel(payload) {
  if (editingItem.value?.id) {
    await api.updateModel(editingItem.value.id, payload);
    editingItem.value = null;
  } else {
    await api.createModel(payload);
  }
  await store.fetchAll();
}

async function removeModel(id) {
  await api.deleteModel(id);
  await store.fetchAll();
  if (editingItem.value?.id === id) {
    editingItem.value = null;
  }
}

onMounted(() => {
  store.fetchAll();
});
</script>
