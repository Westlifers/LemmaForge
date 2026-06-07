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
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Moon, Save, Sun } from "lucide-vue-next";
import { useSettingsStore } from "../stores/settings";
import { useThemeStore } from "../stores/theme";

const settings = useSettingsStore();
const theme = useThemeStore();
const timeoutSeconds = ref(settings.settings.aiTimeoutSeconds);
const message = ref("");

function save() {
  settings.updateSettings({ aiTimeoutSeconds: timeoutSeconds.value });
  message.value = "Settings saved.";
}

function reset() {
  settings.resetSettings();
  timeoutSeconds.value = settings.settings.aiTimeoutSeconds;
  message.value = "Settings reset.";
}
</script>
