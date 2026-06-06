import { defineStore } from "pinia";
import { useStorage } from "@vueuse/core";

export type ThemeMode = "light" | "dark";

export const useThemeStore = defineStore("theme", () => {
  const mode = useStorage<ThemeMode>("lemmaforge-theme", "light");

  function apply() {
    document.documentElement.dataset.theme = mode.value;
  }

  function setMode(nextMode: ThemeMode) {
    mode.value = nextMode;
    apply();
  }

  function toggle() {
    setMode(mode.value === "light" ? "dark" : "light");
  }

  return { mode, apply, setMode, toggle };
});
