<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/">
        <Sigma :size="22" aria-hidden="true" />
        <span>LemmaForge</span>
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
    <main class="main-panel">
      <RouterView />
    </main>
    <AILogDock />
  </div>
</template>

<script setup lang="ts">
import AILogDock from "./components/AILogDock.vue";
import {
  BookOpen,
  FileText,
  Inbox,
  LayoutDashboard,
  Library,
  Network,
  SlidersHorizontal,
  SquareTerminal,
  Sigma,
} from "lucide-vue-next";
</script>
