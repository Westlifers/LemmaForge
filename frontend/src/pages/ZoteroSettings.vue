<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Zotero</h1>
        <p>Local references.bib status and citekey search</p>
      </div>
      <div class="toolbar">
        <button class="button subtle" type="button" @click="loadStatus">
          <RefreshCw :size="16" aria-hidden="true" />
          Refresh
        </button>
        <button class="button primary" type="button" @click="sync">
          <RefreshCw :size="16" aria-hidden="true" />
          Sync
        </button>
      </div>
    </header>

    <section class="plain-section">
      <header class="section-header">
        <div>
          <h2>Reference Status</h2>
          <p>Better BibTeX file and local source index</p>
        </div>
        <span class="panel-icon">
          <BookOpen :size="17" aria-hidden="true" />
        </span>
      </header>
      <pre class="metadata-json compact-json">{{ status }}</pre>
    </section>

    <section class="plain-section editor">
      <header class="section-header">
        <div>
          <h2>Citekey Search</h2>
          <p>Search imported Better BibTeX entries.</p>
        </div>
      </header>
      <div class="inline-search-row">
        <label>
          Search references
          <input v-model="query" @keyup.enter="search" />
        </label>
        <button class="button primary" type="button" @click="search">
          <Search :size="16" aria-hidden="true" />
          Search
        </button>
      </div>
      <ul class="compact-list">
        <li v-for="result in results" :key="String(result.citekey)">
          <code>{{ result.citekey }}</code>
          <span>{{ result.title }}</span>
        </li>
      </ul>
    </section>

    <section class="plain-section">
      <header class="section-header">
        <div>
          <h2>Source Records</h2>
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
          <code>{{ source.citekey || source.id }}</code>
        </li>
      </ul>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { BookOpen, RefreshCw, Search } from "lucide-vue-next";
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
