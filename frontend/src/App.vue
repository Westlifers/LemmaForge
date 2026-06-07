<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <span class="brand-mark">
          <Sigma :size="26" aria-hidden="true" />
        </span>
        <span>
          LemmaForge
          <small>Local-first Research</small>
        </span>
      </RouterLink>

      <nav class="sidebar-nav">
        <section>
          <p>Research</p>
          <RouterLink to="/">
            <LayoutDashboard :size="18" aria-hidden="true" />
            Dashboard
          </RouterLink>
          <RouterLink to="/fragments">
            <Library :size="18" aria-hidden="true" />
            Fragments
          </RouterLink>
          <RouterLink to="/topics">
            <Network :size="18" aria-hidden="true" />
            Topics
          </RouterLink>
          <RouterLink to="/context-packs">
            <Box :size="18" aria-hidden="true" />
            Context Packs
          </RouterLink>
          <RouterLink to="/zotero">
            <BookOpen :size="18" aria-hidden="true" />
            Sources
          </RouterLink>
        </section>

        <section>
          <p>Ops</p>
          <RouterLink to="/import">
            <Inbox :size="18" aria-hidden="true" />
            Import
          </RouterLink>
          <RouterLink to="/review">
            <ClipboardCheck :size="18" aria-hidden="true" />
            Review Queue
          </RouterLink>
          <RouterLink to="/rejected">
            <ArchiveX :size="18" aria-hidden="true" />
            Rejected
          </RouterLink>
          <RouterLink to="/agent">
            <SquareTerminal :size="18" aria-hidden="true" />
            AI Jobs
          </RouterLink>
          <RouterLink to="/settings">
            <SlidersHorizontal :size="18" aria-hidden="true" />
            Settings
          </RouterLink>
        </section>
      </nav>

      <section class="sidebar-status-stack">
        <article class="sidebar-status-card">
          <header>
            <MonitorCheck :size="17" aria-hidden="true" />
            <strong>Local Engine</strong>
          </header>
          <StatusIndicator tone="success">Running</StatusIndicator>
          <small>FastAPI + Vite local</small>
        </article>
        <article class="sidebar-status-card">
          <header>
            <Database :size="17" aria-hidden="true" />
            <strong>Storage</strong>
          </header>
          <StatusIndicator :tone="storageStatusTone">{{ storageStatusText }}</StatusIndicator>
          <span class="storage-meter" aria-hidden="true">
            <span :style="{ width: `${storageUsagePercent}%` }"></span>
          </span>
          <small>{{ storageDetailText }}</small>
        </article>
      </section>
    </aside>

    <div class="workspace-shell">
      <header class="topbar">
        <div class="topbar-workspace">
          <button class="icon-button topbar-menu" type="button" aria-label="Workspace menu">
            <Menu :size="18" aria-hidden="true" />
          </button>
          <div>
            <span class="eyebrow">Workspace</span>
            <strong>{{ routeTitle }}</strong>
          </div>
        </div>

        <div class="topbar-status-strip">
          <StatusIndicator tone="success">
            <RefreshCw :size="14" aria-hidden="true" />
            Local sync saved
          </StatusIndicator>
          <StatusIndicator tone="success">
            <ShieldCheck :size="14" aria-hidden="true" />
            Vault healthy
          </StatusIndicator>
          <StatusIndicator :tone="aiLogs.runningCount ? 'warning' : 'muted'">
            <Bot :size="14" aria-hidden="true" />
            {{ aiLogs.runningCount }} AI running
          </StatusIndicator>
        </div>

        <div class="topbar-actions">
          <RouterLink class="topbar-search" to="/fragments">
            <Search :size="16" aria-hidden="true" />
            <span>Search fragments</span>
          </RouterLink>
          <BaseTooltip label="AI jobs">
            <RouterLink class="icon-button" to="/agent" aria-label="AI jobs">
              <SquareTerminal :size="18" aria-hidden="true" />
            </RouterLink>
          </BaseTooltip>
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
import { computed, onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import AILogDock from "./components/AILogDock.vue";
import BaseTooltip from "./components/BaseTooltip.vue";
import StatusIndicator from "./components/StatusIndicator.vue";
import { api } from "./api/client";
import { useAILogsStore } from "./stores/aiLogs";
import { useThemeStore } from "./stores/theme";
import type { AppHealth } from "./types";
import {
  ArchiveX,
  BookOpen,
  Bot,
  Box,
  ClipboardCheck,
  Database,
  Inbox,
  LayoutDashboard,
  Library,
  Menu,
  MonitorCheck,
  Moon,
  Network,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sigma,
  SlidersHorizontal,
  SquareTerminal,
  Sun,
} from "lucide-vue-next";

const route = useRoute();
const theme = useThemeStore();
const aiLogs = useAILogsStore();
const health = ref<AppHealth | null>(null);
const routeTitles: Record<string, string> = {
  dashboard: "Research Dashboard",
  import: "Import Assistant",
  review: "Review Queue",
  rejected: "Rejected Fragments",
  fragments: "Fragment Library",
  "fragment-detail": "Fragment Detail",
  topics: "Topic Workspace",
  "topic-detail": "Topic Workspace",
  "context-packs": "Context Packs",
  zotero: "Sources",
  "source-detail": "Source Detail",
  agent: "AI Jobs",
  settings: "Settings",
};
theme.apply();

const routeTitle = computed(() => routeTitles[String(route.name || "")] || "LemmaForge");
const themeLabel = computed(() => (theme.mode === "light" ? "Switch to dark mode" : "Switch to light mode"));
const storageUsagePercent = computed(() => {
  const storage = health.value?.storage;
  if (!storage?.disk_total_bytes) return 0;
  const diskUsed = storage.disk_total_bytes - storage.disk_free_bytes;
  return Math.min(100, Math.max(0, Math.round((diskUsed / storage.disk_total_bytes) * 100)));
});
const storageStatusTone = computed(() => {
  if (!health.value?.storage) return "muted";
  return storageUsagePercent.value > 90 ? "warning" : "success";
});
const storageStatusText = computed(() => {
  const storage = health.value?.storage;
  if (!storage) return "Checking...";
  return `${formatBytes(storage.app_bytes)} app data`;
});
const storageDetailText = computed(() => {
  const storage = health.value?.storage;
  if (!storage) return "Loading storage details";
  return `DB ${formatBytes(storage.database_bytes)} / Vault ${formatBytes(storage.vault_bytes)} / Free ${formatBytes(storage.disk_free_bytes)}`;
});

onMounted(async () => {
  try {
    health.value = await api.health();
  } catch {
    health.value = null;
  }
});

function formatBytes(bytes: number) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unitIndex = 0;
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }
  return `${value >= 10 || unitIndex === 0 ? value.toFixed(0) : value.toFixed(1)} ${units[unitIndex]}`;
}
</script>
