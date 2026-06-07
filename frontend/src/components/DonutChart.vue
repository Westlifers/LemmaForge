<template>
  <svg class="donut-chart" viewBox="0 0 120 120" role="img" :aria-label="label">
    <circle cx="60" cy="60" r="48" class="donut-track" />
    <circle
      cx="60"
      cy="60"
      r="48"
      class="donut-value"
      :stroke-dasharray="dashArray"
      :stroke-dashoffset="dashOffset"
    />
    <text x="60" y="57" text-anchor="middle" class="donut-number">{{ normalized }}%</text>
    <text x="60" y="76" text-anchor="middle" class="donut-label">{{ caption }}</text>
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ value: number; caption?: string; label?: string }>(), {
  caption: "Coverage",
  label: "Donut chart",
});
const circumference = 2 * Math.PI * 48;
const normalized = computed(() => Math.max(0, Math.min(100, Math.round(props.value))));
const dashArray = `${circumference.toFixed(2)} ${circumference.toFixed(2)}`;
const dashOffset = computed(() => ((1 - normalized.value / 100) * circumference).toFixed(2));
</script>
