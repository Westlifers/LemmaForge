<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Rejected Fragments</h1>
        <p>Fragments removed from the active working collection</p>
      </div>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <div class="list-stack">
      <article v-for="fragment in rejected" :key="fragment.id" class="edit-card">
        <div class="fragment-card__header">
          <span class="badge">{{ fragment.type }}</span>
          <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
        </div>
        <h3>{{ fragment.title }}</h3>
        <MarkdownLatexRenderer class="card-tex-preview" :body="fragment.body" />
        <footer class="action-row">
          <RouterLink class="button subtle" :to="`/fragments/${fragment.id}`">Inspect</RouterLink>
          <button class="button primary" type="button" @click="restore(fragment)">
            Restore To Draft
          </button>
        </footer>
      </article>
      <p v-if="!rejected.length" class="empty-state">No rejected fragments.</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { api } from "../api/client";
import MarkdownLatexRenderer from "../components/MarkdownLatexRenderer.vue";
import { useFragmentsStore } from "../stores/fragments";
import type { Fragment } from "../types";

const store = useFragmentsStore();
const error = ref("");
const rejected = computed(() => store.fragments.filter((fragment) => fragment.status === "rejected"));

async function load() {
  await store.load({ status: "rejected" });
}

async function restore(fragment: Fragment) {
  try {
    await api.updateFragment(fragment.id, {
      status: "draft",
      change_note: "Restored from rejected to draft."
    });
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

onMounted(load);
</script>
