<template>
  <section class="plain-section">
    <h3>Export Preview</h3>
    <MarkdownLatexRenderer v-if="markdown" :body="markdown" />
    <pre v-else class="markdown-preview">No export generated yet.</pre>
  </section>
</template>

<script setup lang="ts">
import MarkdownLatexRenderer from "./MarkdownLatexRenderer.vue";

defineProps<{ markdown: string }>();
</script>
