<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Local Zotero Library</h1>
        <p>Browse live Zotero items and sync selected papers into LemmaForge Sources</p>
      </div>
      <div class="toolbar">
        <button class="button subtle" type="button" @click="loadStatus">
          <RefreshCw :size="16" aria-hidden="true" />
          Refresh
        </button>
        <button class="button primary" type="button" :disabled="syncing" @click="syncAll">
          <Download :size="16" aria-hidden="true" />
          {{ syncing ? "Syncing..." : "Sync Top Items" }}
        </button>
      </div>
    </header>

    <p v-if="message" class="success-text">{{ message }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>

    <section class="plain-section">
      <header class="section-header">
        <div>
          <h2>Zotero Connection</h2>
          <p>{{ status?.base_url || "http://127.0.0.1:23119" }}</p>
        </div>
        <span class="panel-icon" :class="{ healthy: status?.local_api_available }">
          <BookOpen :size="17" aria-hidden="true" />
        </span>
      </header>
      <div class="metadata-strip">
        <span class="chip" :data-chip="status?.running ? 'topic' : 'warning'">
          {{ status?.running ? "Zotero running" : "Zotero unavailable" }}
        </span>
        <span class="chip" :data-chip="status?.local_api_available ? 'origin' : 'warning'">
          {{ status?.local_api_available ? "Local API available" : "Local API not available" }}
        </span>
        <span v-if="status?.library_name" class="chip" data-chip="exactness">{{ status.library_name }}</span>
      </div>
      <p v-if="status?.error" class="muted">{{ status.error }}</p>
    </section>

    <section class="plain-section editor">
      <header class="section-header">
        <div>
          <h2>Live Zotero Search</h2>
          <p>Select items first, then sync them into durable Source records.</p>
        </div>
        <button class="button subtle" type="button" :disabled="!selectedKeys.length || syncing" @click="syncSelected">
          <CheckSquare :size="16" aria-hidden="true" />
          Sync Selected
        </button>
      </header>
      <div class="inline-search-row">
        <label>
          Search Zotero
          <input v-model="query" placeholder="Title, author, citekey" @keyup.enter="search" />
        </label>
        <button class="button primary" type="button" :disabled="searching" @click="search">
          <Search :size="16" aria-hidden="true" />
          {{ searching ? "Searching..." : "Search" }}
        </button>
      </div>

      <div v-if="zoteroItems.length" class="zotero-item-grid">
        <article v-for="item in zoteroItems" :key="item.key" class="fragment-card zotero-item-card">
          <div class="fragment-card__header">
            <label class="inline-check">
              <input v-model="selectedKeys" type="checkbox" :value="item.key" />
              Select
            </label>
            <span class="badge">{{ item.item_type || "item" }}</span>
            <span v-if="item.attachment_count" class="chip" data-chip="topic">{{ item.attachment_count }} attachments</span>
          </div>
          <h3>{{ item.title }}</h3>
          <p class="muted">{{ item.creator_summary || creatorNames(item) || "Unknown creator" }}</p>
          <div class="metadata-strip">
            <span v-if="item.citation_key" class="chip" data-chip="topic">{{ item.citation_key }}</span>
            <span v-if="item.year" class="chip" data-chip="origin">{{ item.year }}</span>
            <a v-if="item.url" class="chip" data-chip="exactness" :href="item.url" target="_blank" rel="noreferrer">URL</a>
          </div>
        </article>
      </div>
      <p v-else class="muted-panel">Search your local Zotero library to preview live items.</p>
    </section>

    <section class="plain-section">
      <header class="section-header">
        <div>
          <h2>Synced LemmaForge Sources</h2>
          <p>{{ sources.length }} local source record{{ sources.length === 1 ? "" : "s" }}</p>
        </div>
      </header>
      <div class="inline-search-row">
        <label>
          Search sources
          <input v-model="sourceSearch" @input="loadSources" />
        </label>
      </div>
      <ul class="compact-list">
        <li v-for="source in sources" :key="source.id">
          <RouterLink class="text-button" :to="`/sources/${source.id}`">{{ source.title }}</RouterLink>
          <code>{{ source.citekey || source.zotero_item_key || source.id }}</code>
          <span v-if="source.zotero_item_key" class="chip" data-chip="ai">Zotero</span>
        </li>
      </ul>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { BookOpen, CheckSquare, Download, RefreshCw, Search } from "lucide-vue-next";
import { api } from "../api/client";
import type { Source, ZoteroItem, ZoteroStatus } from "../types";

const status = ref<ZoteroStatus | null>(null);
const query = ref("");
const sourceSearch = ref("");
const zoteroItems = ref<ZoteroItem[]>([]);
const selectedKeys = ref<string[]>([]);
const sources = ref<Source[]>([]);
const searching = ref(false);
const syncing = ref(false);
const message = ref("");
const error = ref("");

async function loadStatus() {
  error.value = "";
  status.value = await api.zoteroStatus();
  await loadSources();
}

async function search() {
  searching.value = true;
  error.value = "";
  message.value = "";
  try {
    const response = await api.zoteroSearch(query.value);
    if (!response.available) {
      error.value = response.error || "Zotero Local API is unavailable.";
      zoteroItems.value = [];
      return;
    }
    zoteroItems.value = response.results;
    selectedKeys.value = selectedKeys.value.filter((key) => zoteroItems.value.some((item) => item.key === key));
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    searching.value = false;
  }
}

async function loadSources() {
  sources.value = await api.listSources(sourceSearch.value);
}

async function syncSelected() {
  if (!selectedKeys.value.length) return;
  await syncKeys(selectedKeys.value);
}

async function syncAll() {
  await syncKeys();
}

async function syncKeys(keys?: string[]) {
  syncing.value = true;
  error.value = "";
  message.value = "";
  try {
    const result = await api.zoteroSync(keys);
    if (!result.available) {
      error.value = result.error || "Zotero Local API is unavailable.";
      return;
    }
    message.value = `Synced ${result.synced_count} Zotero item${result.synced_count === 1 ? "" : "s"}.`;
    selectedKeys.value = [];
    await loadSources();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    syncing.value = false;
  }
}

function creatorNames(item: ZoteroItem) {
  return item.creators
    .map((creator) => creator.name || [creator.firstName, creator.lastName].filter(Boolean).join(" "))
    .filter(Boolean)
    .join("; ");
}

onMounted(loadStatus);
</script>
