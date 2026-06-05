<template>
  <section class="page">
    <header class="page-header">
      <div>
        <RouterLink class="back-link" to="/zotero">Sources</RouterLink>
        <h1>{{ source?.title || "Source" }}</h1>
        <p v-if="source">{{ source.citekey || source.source_type }}</p>
      </div>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <section v-if="source" class="plain-section">
      <pre class="metadata-json">{{ JSON.stringify(source, null, 2) }}</pre>
    </section>
    <section class="plain-section">
      <h2>Linked Fragments</h2>
      <div class="list-stack">
        <FragmentCard v-for="fragment in fragments" :key="fragment.id" :fragment="fragment" />
        <p v-if="!fragments.length" class="muted">No fragments linked to this source yet.</p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
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

