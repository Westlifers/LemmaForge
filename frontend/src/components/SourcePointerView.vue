<template>
  <section class="plain-section">
    <h3>Source Pointers</h3>
    <p v-if="!pointers.length" class="muted">No source pointers recorded.</p>
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
import type { SourcePointer } from "../types";

defineProps<{ pointers: SourcePointer[] }>();
</script>
