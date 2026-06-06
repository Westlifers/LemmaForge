import { defineStore } from "pinia";

const SETTINGS_KEY = "lemmaforge.settings";

export interface LemmaForgeSettings {
  aiTimeoutSeconds: number;
}

const defaultSettings: LemmaForgeSettings = {
  aiTimeoutSeconds: 900,
};

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    settings: loadSettings(),
  }),
  actions: {
    updateSettings(next: Partial<LemmaForgeSettings>) {
      this.settings = {
        ...this.settings,
        ...next,
      };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
    },
    resetSettings() {
      this.settings = { ...defaultSettings };
      localStorage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
    },
  },
});

function loadSettings(): LemmaForgeSettings {
  const raw = localStorage.getItem(SETTINGS_KEY);
  if (!raw) return { ...defaultSettings };
  try {
    const parsed = JSON.parse(raw) as Partial<LemmaForgeSettings>;
    const timeout = Number(parsed.aiTimeoutSeconds);
    return {
      aiTimeoutSeconds: Number.isFinite(timeout) ? clampTimeout(timeout) : defaultSettings.aiTimeoutSeconds,
    };
  } catch {
    return { ...defaultSettings };
  }
}

function clampTimeout(value: number) {
  return Math.min(1800, Math.max(30, Math.round(value)));
}
