<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">
          <Sigma :size="22" aria-hidden="true" />
        </span>
        <span>
          LemmaForge
          <small>Research Console</small>
        </span>
      </RouterLink>
      <nav>
        <RouterLink to="/">
          <LayoutDashboard :size="18" aria-hidden="true" />
          Dashboard
        </RouterLink>
        <RouterLink to="/import">
          <Inbox :size="18" aria-hidden="true" />
          Import
        </RouterLink>
        <RouterLink to="/fragments">
          <Library :size="18" aria-hidden="true" />
          Fragments
        </RouterLink>
        <RouterLink to="/context-packs">
          <FileText :size="18" aria-hidden="true" />
          Context Packs
        </RouterLink>
        <RouterLink to="/topics">
          <Network :size="18" aria-hidden="true" />
          Topics
        </RouterLink>
        <RouterLink to="/zotero">
          <BookOpen :size="18" aria-hidden="true" />
          Zotero
        </RouterLink>
        <RouterLink to="/agent">
          <SquareTerminal :size="18" aria-hidden="true" />
          Agent
        </RouterLink>
        <RouterLink to="/settings">
          <SlidersHorizontal :size="18" aria-hidden="true" />
          Settings
        </RouterLink>
      </nav>
    </aside>
    <div class="workspace-shell">
      <header class="topbar">
        <div>
          <span class="eyebrow">Local workspace</span>
          <strong>{{ routeTitle }}</strong>
        </div>
        <div class="topbar-actions">
          <RouterLink class="topbar-search" to="/fragments">
            <Search :size="16" aria-hidden="true" />
            <span>Search fragments</span>
          </RouterLink>
          <BaseTooltip label="Settings">
            <RouterLink class="icon-button" to="/settings" aria-label="Settings">
              <Settings :size="18" aria-hidden="true" />
            </RouterLink>
          </BaseTooltip>
          <BaseTooltip :label="themeLabel">
            <button class="icon-button" type="button" :aria-label="themeLabel" @click="theme.toggle">
              <Moon v-if="theme.mode === 'light'" :size="18" aria-hidden="true" />
              <Sun v-else :size="18" aria-hidden="true" />
            </button>
          </BaseTooltip>
        </div>
      </header>
      <main class="main-panel">
        <RouterView />
      </main>
    </div>
    <AILogDock />
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AILogDock from "./components/AILogDock.vue";
import BaseTooltip from "./components/BaseTooltip.vue";
import { useThemeStore } from "./stores/theme";
import {
  BookOpen,
  FileText,
  Inbox,
  LayoutDashboard,
  Library,
  Moon,
  Network,
  Search,
  Settings,
  SlidersHorizontal,
  SquareTerminal,
  Sigma,
  Sun,
} from "lucide-vue-next";

const route = useRoute();
const theme = useThemeStore();
const routeTitles: Record<string, string> = {
  dashboard: "Research Dashboard",
  import: "Import Assistant",
  review: "Review Queue",
  rejected: "Rejected Fragments",
  fragments: "Fragment Library",
  "fragment-detail": "Fragment Detail",
  topics: "Topic Workspace",
  "topic-detail": "Topic Graph",
  "context-packs": "Context Packs",
  zotero: "Zotero",
  "source-detail": "Source Detail",
  agent: "Agent Console",
  settings: "Settings"
};
theme.apply();

const routeTitle = computed(() => routeTitles[String(route.name || "")] || "LemmaForge");
const themeLabel = computed(() => (theme.mode === "light" ? "Switch to dark mode" : "Switch to light mode"));
</script>
