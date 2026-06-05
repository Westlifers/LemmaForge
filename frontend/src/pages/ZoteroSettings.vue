<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Zotero</h1>
        <p>Local references.bib status and citekey search</p>
      </div>
      <button class="button subtle" type="button" @click="loadStatus">
        <RefreshCw :size="16" aria-hidden="true" />
        Refresh
      </button>
      <button class="button primary" type="button" @click="sync">
        <RefreshCw :size="16" aria-hidden="true" />
        Sync
      </button>
    </header>

    <section class="plain-section">
      <pre class="metadata-json">{{ status }}</pre>
    </section>

    <section class="plain-section editor">
      <label>
        Search references
        <input v-model="query" @keyup.enter="search" />
      </label>
      <button class="button primary" type="button" @click="search">
        <Search :size="16" aria-hidden="true" />
        Search
      </button>
      <ul class="compact-list">
        <li v-for="result in results" :key="String(result.citekey)">
          <code>{{ result.citekey }}</code>
          <span>{{ result.title }}</span>
        </li>
      </ul>
    </section>

    <section class="plain-section">
      <h2>Source Records</h2>
      <label>
        Search sources
        <input v-model="sourceSearch" @input="loadSources" />
      </label>
      <ul class="compact-list">
        <li v-for="source in sources" :key="source.id">
          <RouterLink class="text-button" :to="`/sources/${source.id}`">{{ source.title }}</RouterLink>
          <code>{{ source.citekey || source.id }}</code>
        </li>
      </ul>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RefreshCw, Search } from "lucide-vue-next";
import { api } from "../api/client";
import type { Source } from "../types";

const status = ref("");
const query = ref("");
const sourceSearch = ref("");
const results = ref<Array<Record<string, string | null>>>([]);
const sources = ref<Source[]>([]);

async function loadStatus() {
  status.value = JSON.stringify(await api.zoteroStatus(), null, 2);
  await loadSources();
}

async function search() {
  const response = await api.zoteroSearch(query.value);
  results.value = response.results;
}

async function loadSources() {
  sources.value = await api.listSources(sourceSearch.value);
}

async function sync() {
  sources.value = await api.zoteroSync();
}

onMounted(loadStatus);
</script>
