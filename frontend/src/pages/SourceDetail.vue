<template>
  <section class="page">
    <header class="page-header">
      <div>
        <RouterLink class="back-link" to="/zotero">
          <ArrowLeft :size="16" aria-hidden="true" />
          Sources
        </RouterLink>
        <h1>{{ source?.title || "Source" }}</h1>
        <p v-if="source">{{ source.citekey || source.source_type }}</p>
      </div>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <section v-if="source" class="plain-section source-summary-panel">
      <header class="section-header">
        <div>
          <h2>Source Metadata</h2>
          <p>{{ source.source_type }}{{ source.year ? ` / ${source.year}` : "" }}</p>
        </div>
        <span class="panel-icon">
          <BookOpen :size="17" aria-hidden="true" />
        </span>
      </header>
      <div class="metadata-strip">
        <span v-if="source.citekey" class="chip" data-chip="topic">{{ source.citekey }}</span>
        <span v-if="source.zotero_item_key" class="chip" data-chip="ai">Zotero: {{ source.zotero_item_key }}</span>
        <span v-if="source.authors" class="chip" data-chip="origin">{{ source.authors }}</span>
        <a v-if="source.url" class="chip" data-chip="exactness" :href="source.url" rel="noreferrer" target="_blank">
          Open URL
        </a>
        <button v-if="source.zotero_item_key" class="chip chip-button" type="button" @click="loadZoteroItem">
          <RefreshCw :size="14" aria-hidden="true" />
          Refresh Zotero
        </button>
        <a v-if="zoteroItem?.zotero_url" class="chip" data-chip="exactness" :href="zoteroItem.zotero_url" rel="noreferrer" target="_blank">
          <ExternalLink :size="14" aria-hidden="true" />
          View in Zotero
        </a>
      </div>
      <div v-if="zoteroItem" class="plain-section source-live-panel">
        <h3>Live Zotero Metadata</h3>
        <p v-if="zoteroItem.abstract_note" class="muted">{{ zoteroItem.abstract_note }}</p>
        <ul v-if="zoteroItem.attachments.length" class="compact-list">
          <li
            v-for="(attachment, index) in zoteroItem.attachments"
            :key="attachment.key || attachment.title || attachment.filename || index"
          >
            <span>{{ attachment.title || attachment.filename }}</span>
            <code>{{ attachment.content_type }}</code>
          </li>
        </ul>
      </div>
      <p v-if="zoteroError" class="error-text">{{ zoteroError }}</p>
      <details>
        <summary>Raw metadata</summary>
        <pre class="metadata-json">{{ JSON.stringify(source, null, 2) }}</pre>
      </details>
    </section>
    <section class="plain-section">
      <header class="section-header">
        <div>
          <h2>Linked Fragments</h2>
          <p>{{ fragments.length }} fragment{{ fragments.length === 1 ? "" : "s" }}</p>
        </div>
      </header>
      <div class="list-stack">
        <FragmentCard v-for="fragment in fragments" :key="fragment.id" :fragment="fragment" />
        <p v-if="!fragments.length" class="muted">No fragments linked to this source yet.</p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { ArrowLeft, BookOpen, ExternalLink, RefreshCw } from "lucide-vue-next";
import FragmentCard from "../components/FragmentCard.vue";
import { api } from "../api/client";
import type { Fragment, Source, ZoteroItem } from "../types";

const props = defineProps<{ id: string }>();
const source = ref<Source | null>(null);
const fragments = ref<Fragment[]>([]);
const zoteroItem = ref<ZoteroItem | null>(null);
const error = ref("");
const zoteroError = ref("");

async function load() {
  try {
    source.value = await api.getSource(props.id);
    fragments.value = await api.listSourceFragments(props.id);
    zoteroItem.value = null;
    zoteroError.value = "";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function loadZoteroItem() {
  if (!source.value?.zotero_item_key) return;
  zoteroError.value = "";
  try {
    const result = await api.getZoteroItem(source.value.zotero_item_key);
    if (!result.available || !result.item) {
      zoteroError.value = result.error || "Zotero Local API is unavailable.";
      zoteroItem.value = null;
      return;
    }
    zoteroItem.value = result.item;
  } catch (caught) {
    zoteroError.value = caught instanceof Error ? caught.message : String(caught);
  }
}

onMounted(load);
watch(() => props.id, load);
</script>
