<template>
  <form class="card" @submit.prevent="submit">
    <div class="panel-header">
      <div>
        <div class="panel-title">{{ editing ? "Edit model connection" : "New model connection" }}</div>
        <div class="panel-subtitle">Manage provider routing, credentials, and generation defaults.</div>
      </div>
      <span class="tag">{{ editing ? "Editing" : "Create" }}</span>
    </div>
    <div class="form-grid">
      <label class="field">
        <span>Name</span>
        <input v-model="form.name" class="input" placeholder="OpenAI Primary" required />
        <span class="helper-text">Internal display name for this model configuration.</span>
      </label>
      <label class="field">
        <span>Provider</span>
        <select v-model="form.provider" class="select">
          <option value="openai">openai-compatible</option>
          <option value="anthropic">anthropic</option>
          <option value="google">google/gemini-compatible</option>
          <option value="moonshot">moonshot-compatible</option>
        </select>
        <span class="helper-text">Used for compatibility routing and response handling.</span>
      </label>
      <label class="field">
        <span>Model</span>
        <input v-model="form.model" class="input" placeholder="gpt-4.1-mini" required />
        <span class="helper-text">Exact model identifier exposed by the provider.</span>
      </label>
      <label class="field">
        <span>Base URL</span>
        <input v-model="form.base_url" class="input mono" required />
        <span class="helper-text">OpenAI-compatible root URL such as `https://api.openai.com/v1`.</span>
      </label>
      <label class="field">
        <span>API Key</span>
        <input v-model="form.api_key" class="input mono" :placeholder="editing ? 'Leave blank to keep current key' : 'sk-...'" />
        <span class="helper-text">Stored encrypted on the backend and never shown in full.</span>
      </label>
      <label class="field">
        <span>Timeout (seconds)</span>
        <input v-model.number="form.timeout_seconds" class="input" type="number" min="5" max="120" />
        <span class="helper-text">Provider timeout before the engine falls back to `HOLD`.</span>
      </label>
      <label class="field">
        <span>Temperature</span>
        <input v-model.number="form.temperature" class="input" type="number" min="0" max="2" step="0.1" />
        <span class="helper-text">Lower values are more stable for structured trading output.</span>
      </label>
      <label class="field">
        <span>Max tokens</span>
        <input v-model.number="form.max_tokens" class="input" type="number" min="1" max="16000" />
        <span class="helper-text">Upper bound for JSON decision plus rationale.</span>
      </label>
      <label class="field">
        <span>Connection status</span>
        <span class="checkbox-card">
          <input v-model="form.enabled" type="checkbox" />
          Enabled for platform use
        </span>
      </label>
      <label class="field">
        <span>Strategy participation</span>
        <span class="checkbox-card">
          <input v-model="form.include_in_strategy" type="checkbox" />
          Include this model in scheduled decisions
        </span>
      </label>
    </div>
    <div class="actions" style="margin-top: 16px">
      <button class="button" type="submit">{{ editing ? "Update model" : "Create model" }}</button>
      <button v-if="editing" class="button secondary" type="button" @click="$emit('cancel')">Cancel</button>
    </div>
    <div class="grid-note">Tip: keep one stable production model and one experimental model for side-by-side comparison.</div>
  </form>
</template>

<script setup>
import { computed, reactive, watch } from "vue";

const props = defineProps({
  initialValue: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["submit", "cancel"]);

const emptyForm = () => ({
  name: "",
  provider: "openai",
  model: "",
  base_url: "https://api.openai.com/v1",
  api_key: "",
  timeout_seconds: 20,
  temperature: 0.2,
  max_tokens: 800,
  enabled: true,
  include_in_strategy: true,
});

const form = reactive(emptyForm());

const editing = computed(() => Boolean(props.initialValue?.id));

watch(
  () => props.initialValue,
  (value) => {
    Object.assign(form, emptyForm(), value || {});
    form.api_key = "";
  },
  { immediate: true }
);

function submit() {
  const payload = { ...form };
  if (!payload.api_key) {
    delete payload.api_key;
  }
  emit("submit", payload);
  if (!editing.value) {
    Object.assign(form, emptyForm());
  }
}
</script>
