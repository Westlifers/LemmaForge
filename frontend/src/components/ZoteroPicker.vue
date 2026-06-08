<template>
  <div class="zotero-picker">
    <div class="inline-search-row">
      <label>
        Zotero search
        <input
          v-model="query"
          :disabled="disabled || searching"
          placeholder="Search title, author, citekey"
          @keyup.enter="search"
        />
      </label>
      <button class="button subtle" type="button" :disabled="disabled || searching" @click="search">
        <Search :size="15" aria-hidden="true" />
        {{ searching ? "Searching..." : "Search" }}
      </button>
    </div>
    <p v-if="error" class="error-text">{{ error }}</p>
    <ul v-if="results.length" class="compact-list zotero-picker-results">
      <li v-for="item in results" :key="item.key">
        <button class="text-button zotero-result-main" type="button" :disabled="disabled" @click="$emit('select', item)">
          <span>{{ item.title }}</span>
          <code>{{ item.citation_key || item.key }}</code>
        </button>
        <small>{{ item.creator_summary || creatorNames(item) || item.item_type }}</small>
      </li>
    </ul>
    <p v-else-if="searched && !error" class="muted">No Zotero items found.</p>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { Search } from "lucide-vue-next";
import { api } from "../api/client";
import type { ZoteroItem } from "../types";

defineProps<{ disabled?: boolean }>();
defineEmits<{ select: [item: ZoteroItem] }>();

const query = ref("");
const results = ref<ZoteroItem[]>([]);
const searching = ref(false);
const searched = ref(false);
const error = ref("");

async function search() {
  error.value = "";
  searching.value = true;
  searched.value = true;
  try {
    const response = await api.zoteroSearch(query.value, 12);
    if (!response.available) {
      error.value = response.error || "Zotero Local API is unavailable.";
      results.value = [];
      return;
    }
    results.value = response.results;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
    results.value = [];
  } finally {
    searching.value = false;
  }
}

function creatorNames(item: ZoteroItem) {
  return item.creators
    .map((creator) => creator.name || [creator.firstName, creator.lastName].filter(Boolean).join(" "))
    .filter(Boolean)
    .join("; ");
}
</script>
