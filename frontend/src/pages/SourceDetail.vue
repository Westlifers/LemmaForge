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
        <span v-if="source.authors" class="chip" data-chip="origin">{{ source.authors }}</span>
        <a v-if="source.url" class="chip" data-chip="exactness" :href="source.url" rel="noreferrer" target="_blank">
          Open URL
        </a>
      </div>
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
import { ArrowLeft, BookOpen } from "lucide-vue-next";
import FragmentCard from "../components/FragmentCard.vue";
import { api } from "../api/client";
import type { Fragment, Source } from "../types";

const props = defineProps<{ id: string }>();
const source = ref<Source | null>(null);
const fragments = ref<Fragment[]>([]);
const error = ref("");

async function load() {
  try {
    source.value = await api.getSource(props.id);
    fragments.value = await api.listSourceFragments(props.id);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

onMounted(load);
watch(() => props.id, load);
</script>
