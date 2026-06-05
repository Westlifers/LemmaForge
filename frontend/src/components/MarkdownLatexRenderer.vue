<template>
  <div class="markdown-body" v-html="rendered" />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { renderMarkdownWithTex } from "../utils/texMarkdown";

const props = defineProps<{ body: string }>();
const rendered = computed(() => renderMarkdownWithTex(props.body || ""));
</script>
