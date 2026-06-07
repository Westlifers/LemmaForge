<template>
  <span class="status-indicator" :data-tone="tone">
    <span aria-hidden="true"></span>
    <slot />
  </span>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ tone?: "success" | "warning" | "danger" | "info" | "muted" }>(), {
  tone: "info",
});
</script>
