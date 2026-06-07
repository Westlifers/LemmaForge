<template>
  <section class="plain-section">
    <header class="section-header">
      <div>
        <h3>Source Pointers</h3>
        <p>{{ pointers.length }} pointer{{ pointers.length === 1 ? "" : "s" }}</p>
      </div>
      <span class="panel-icon">
        <BookOpen :size="16" aria-hidden="true" />
      </span>
    </header>
    <p v-if="!pointers.length" class="empty-state">No source pointers recorded.</p>
    <ul v-else class="compact-list">
      <li v-for="pointer in pointers" :key="pointer.id">
        <code>{{ pointer.source_id }}</code>
        <span v-if="pointer.locator">{{ pointer.locator }}</span>
        <span>{{ pointer.exactness }}</span>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { BookOpen } from "lucide-vue-next";
import type { SourcePointer } from "../types";

defineProps<{ pointers: SourcePointer[] }>();
</script>
