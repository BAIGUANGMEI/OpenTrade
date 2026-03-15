<template>
  <section>
    <div class="page-header">
      <div>
        <div class="page-eyebrow">Execution Control</div>
        <h2 class="headline">Strategies</h2>
        <p class="muted">Manage scheduler cadence, prompt policy, and manual cycle execution.</p>
      </div>
      <div class="actions">
        <button class="button" @click="runNow">Run Now</button>
        <button class="button secondary" @click="saveSettings">Save Settings</button>
        <button class="button secondary danger" @click="resetTradingData">Restart</button>
      </div>
    </div>

    <div class="stats-strip">
      <div class="stat-card">
        <div class="stat-label">Scheduler</div>
        <div class="stat-value">{{ settings.enabled ? "On" : "Off" }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Interval</div>
        <div class="stat-value">{{ settings.decision_interval_seconds || 0 }}s</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Run History</div>
        <div class="stat-value">{{ runs.length }}</div>
      </div>
    </div>

    <div class="split">
      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Scheduler Settings</div>
            <div class="panel-subtitle">Define how often the strategy executes and what system prompt governs output.</div>
          </div>
        </div>
        <div class="form-grid">
          <label class="field">
            <span>Automation</span>
            <span class="checkbox-card">
              <input v-model="settings.enabled" type="checkbox" />
              Enable automatic scheduling
            </span>
          </label>
          <label class="field">
            <span>Decision interval (seconds)</span>
            <input v-model.number="settings.decision_interval_seconds" class="input" type="number" min="30" />
            <span class="helper-text">The engine sleeps for this period between automatic decision rounds.</span>
          </label>
          <label class="field full">
            <span>System Prompt Template</span>
            <textarea v-model="settings.prompt_template" class="textarea"></textarea>
            <span class="helper-text">Keep this concise and strict so models return JSON without extra commentary.</span>
          </label>
        </div>
      </div>

      <div class="card">
        <div class="panel-header">
          <div>
            <div class="panel-title">Scheduler State</div>
            <div class="panel-subtitle">Realtime runtime state reported by the backend process.</div>
          </div>
          <span class="status-pill" :class="state.last_run_status === 'completed' ? 'success' : 'info'">
            {{ state.last_run_status || "idle" }}
          </span>
        </div>
        <div class="key-value-list">
          <div class="key-value-item">
            <div class="key-label">Loop running</div>
            <div class="key-value">{{ state.running ? "Yes" : "No" }}</div>
          </div>
          <div class="key-value-item">
            <div class="key-label">Last run</div>
            <div class="key-value">{{ state.last_run_at ? formatDateTime(state.last_run_at) : "-" }}</div>
          </div>
          <div class="key-value-item">
            <div class="key-label">Default interval</div>
            <div class="key-value">{{ state.default_interval_seconds || "-" }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="card" style="margin-top: 16px">
      <div class="panel-header">
        <div>
          <div class="panel-title">Recent Runs</div>
          <div class="panel-subtitle">Chronological execution records for manual and scheduled strategy cycles.</div>
        </div>
      </div>
      <div v-if="!runs.length" class="empty-state">
        <strong>No runs available</strong>
        <span class="muted">Use `Run Now` or enable scheduling to generate the first execution record.</span>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Started</th>
            <th>Finished</th>
            <th>Duration</th>
            <th>Error</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.id">
            <td>{{ run.id }}</td>
            <td>{{ run.status }}</td>
            <td>{{ formatDateTime(run.started_at) }}</td>
            <td>{{ run.finished_at ? formatDateTime(run.finished_at) : "-" }}</td>
            <td>{{ run.duration_ms ? `${Math.round(run.duration_ms)} ms` : "-" }}</td>
            <td>{{ run.error || "-" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";

import { api } from "../services/api";
import { formatDateTime } from "../utils/time";

const settings = reactive({
  enabled: false,
  decision_interval_seconds: 300,
  prompt_template: "",
});
const state = reactive({});
const runs = ref([]);

async function load() {
  Object.assign(settings, await api.getStrategySettings());
  Object.assign(state, await api.getSchedulerState());
  runs.value = await api.getStrategyRuns();
}

async function saveSettings() {
  const response = await api.updateStrategySettings({
    enabled: settings.enabled,
    decision_interval_seconds: settings.decision_interval_seconds,
    prompt_template: settings.prompt_template,
  });
  Object.assign(settings, response);
  Object.assign(state, await api.getSchedulerState());
}

async function runNow() {
  await api.runDecisionCycle();
  await load();
}

async function resetTradingData() {
  const confirmed = window.confirm(
    "This will clear all trading data, including decisions, orders, positions, NAV history, run history, and audit logs. Model configuration and strategy settings will be kept. Continue?",
  );
  if (!confirmed) {
    return;
  }
  await api.resetTradingData();
  await load();
}

onMounted(load);
</script>
