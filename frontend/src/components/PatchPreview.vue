<template>
  <section class="patch-preview">
    <header class="section-header">
      <div>
        <h2>Patch Preview</h2>
        <p>{{ preview.fragment_count }} fragments, {{ preview.relation_count }} relations, {{ preview.source_pointer_count }} source pointers</p>
      </div>
      <button class="button primary" type="button" @click="$emit('accept')">
        <Check :size="16" aria-hidden="true" />
        Accept
      </button>
    </header>

    <div v-if="preview.warnings.length" class="warning-list">
      <p v-for="warning in preview.warnings" :key="warning">{{ warning }}</p>
    </div>

    <div class="list-stack">
      <article v-for="fragment in preview.patch.fragments" :key="fragment.local_id" class="fragment-card">
        <div class="fragment-card__header">
          <span class="badge">{{ fragment.type }}</span>
          <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
        </div>
        <h3>{{ fragment.title }}</h3>
        <p>{{ fragment.body }}</p>
        <footer>
          <span>{{ fragment.origin_classification }}</span>
          <span>{{ fragment.exactness }}</span>
          <span v-if="fragment.confidence !== null">confidence {{ fragment.confidence }}</span>
        </footer>
      </article>
    </div>

    <section v-if="preview.patch.relations.length" class="plain-section">
      <h3>Relations</h3>
      <ul class="compact-list">
        <li v-for="relation in preview.patch.relations" :key="`${relation.source}-${relation.kind}-${relation.target}`">
          <code>{{ relation.source }}</code> {{ relation.kind }} <code>{{ relation.target }}</code>
        </li>
      </ul>
    </section>

    <section v-if="preview.patch.source_pointers.length" class="plain-section">
      <h3>Source Pointers</h3>
      <ul class="compact-list">
        <li v-for="pointer in preview.patch.source_pointers" :key="`${pointer.fragment_local_id}-${pointer.citekey}-${pointer.locator}`">
          <code>{{ pointer.fragment_local_id }}</code>
          <span>{{ pointer.citekey || "inline source" }}</span>
          <span v-if="pointer.locator">{{ pointer.locator }}</span>
          <span>{{ pointer.exactness }}</span>
        </li>
      </ul>
    </section>
  </section>
</template>

<script setup lang="ts">
import { Check } from "lucide-vue-next";
import type { ImportPreview } from "../types";

defineProps<{ preview: ImportPreview }>();
defineEmits<{ accept: [] }>();
</script>

