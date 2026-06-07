<template>
  <span class="progress-bar" :aria-label="label">
    <span :style="{ width: `${normalized}%` }"></span>
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ value: number; label?: string }>(), {
  label: "Progress",
});
const normalized = computed(() => Math.max(0, Math.min(100, Math.round(props.value))));
</script>
