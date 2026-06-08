<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Settings</h1>
        <p>Local preferences for LemmaForge</p>
      </div>
    </header>

    <section class="plain-section settings-panel">
      <h2>Appearance</h2>
      <div class="segmented-control" role="group" aria-label="Theme mode">
        <button
          class="button subtle"
          :class="{ active: theme.mode === 'light' }"
          type="button"
          @click="theme.setMode('light')"
        >
          <Sun :size="16" aria-hidden="true" />
          Light
        </button>
        <button
          class="button subtle"
          :class="{ active: theme.mode === 'dark' }"
          type="button"
          @click="theme.setMode('dark')"
        >
          <Moon :size="16" aria-hidden="true" />
          Dark
        </button>
      </div>
      <p class="muted">
        Light mode is the primary design; dark mode uses the same research-console tokens for late sessions.
      </p>
    </section>

    <section class="plain-section settings-panel">
      <h2>AI Operations</h2>
      <label>
        Default timeout
        <select v-model.number="timeoutSeconds">
          <option :value="300">5 minutes</option>
          <option :value="480">8 minutes</option>
          <option :value="600">10 minutes</option>
          <option :value="900">15 minutes</option>
          <option :value="1200">20 minutes</option>
          <option :value="1800">30 minutes</option>
        </select>
      </label>
      <p class="muted">
        Used by Codex-backed actions such as fragment extraction and topic context suggestions.
      </p>
      <div class="action-row">
        <button class="button primary" type="button" @click="save">
          <Save :size="16" aria-hidden="true" />
          Save
        </button>
        <button class="button subtle" type="button" @click="reset">
          Reset
        </button>
      </div>
      <p v-if="message" class="success-text">{{ message }}</p>
    </section>

    <section class="plain-section settings-panel">
      <h2>Zotero Local API</h2>
      <label>
        Local API URL
        <input v-model="zoteroLocalApiUrl" placeholder="http://127.0.0.1:23119" />
      </label>
      <div class="metadata-strip">
        <span class="chip" :data-chip="zoteroStatus?.local_api_available ? 'topic' : 'warning'">
          {{ zoteroStatus?.local_api_available ? "Available" : "Not connected" }}
        </span>
        <span v-if="zoteroStatus?.library_name" class="chip" data-chip="origin">{{ zoteroStatus.library_name }}</span>
        <span v-if="zoteroStatus?.base_url" class="chip">{{ zoteroStatus.base_url }}</span>
      </div>
      <p v-if="zoteroStatus?.error" class="muted">{{ zoteroStatus.error }}</p>
      <div class="action-row">
        <button class="button primary" type="button" :disabled="savingZotero" @click="saveZotero">
          <Save :size="16" aria-hidden="true" />
          {{ savingZotero ? "Saving..." : "Save Zotero" }}
        </button>
        <button class="button subtle" type="button" @click="loadZoteroStatus">
          Test Connection
        </button>
      </div>
      <p v-if="zoteroMessage" class="success-text">{{ zoteroMessage }}</p>
      <p v-if="zoteroError" class="error-text">{{ zoteroError }}</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Moon, Save, Sun } from "lucide-vue-next";
import { api } from "../api/client";
import { useSettingsStore } from "../stores/settings";
import { useThemeStore } from "../stores/theme";
import type { ZoteroStatus } from "../types";

const settings = useSettingsStore();
const theme = useThemeStore();
const timeoutSeconds = ref(settings.settings.aiTimeoutSeconds);
const message = ref("");
const zoteroStatus = ref<ZoteroStatus | null>(null);
const zoteroLocalApiUrl = ref("http://127.0.0.1:23119");
const savingZotero = ref(false);
const zoteroMessage = ref("");
const zoteroError = ref("");

function save() {
  settings.updateSettings({ aiTimeoutSeconds: timeoutSeconds.value });
  message.value = "Settings saved.";
}

function reset() {
  settings.resetSettings();
  timeoutSeconds.value = settings.settings.aiTimeoutSeconds;
  message.value = "Settings reset.";
}

async function loadZoteroStatus() {
  zoteroError.value = "";
  try {
    zoteroStatus.value = await api.zoteroStatus();
    zoteroLocalApiUrl.value = zoteroStatus.value.base_url || zoteroLocalApiUrl.value;
  } catch (caught) {
    zoteroError.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function saveZotero() {
  savingZotero.value = true;
  zoteroMessage.value = "";
  zoteroError.value = "";
  try {
    await api.saveZoteroSettings({ zotero_local_api_url: zoteroLocalApiUrl.value.trim() || null });
    await loadZoteroStatus();
    zoteroMessage.value = "Zotero settings saved.";
  } catch (caught) {
    zoteroError.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    savingZotero.value = false;
  }
}

onMounted(loadZoteroStatus);
</script>
