<template>
  <svg class="sparkline-chart" viewBox="0 0 120 36" preserveAspectRatio="none" aria-hidden="true">
    <defs>
      <linearGradient :id="fillId" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" :stop-color="color" stop-opacity="0.22" />
        <stop offset="100%" :stop-color="color" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path v-if="areaPath" :d="areaPath" :fill="`url(#${fillId})`" />
    <path v-if="linePath" :d="linePath" fill="none" :stroke="color" stroke-linecap="round" stroke-width="2.2" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(defineProps<{ values: number[]; color?: string }>(), {
  color: "var(--accent)",
});

const fillId = `sparkline-${Math.random().toString(36).slice(2)}`;
const points = computed(() => {
  const values = props.values.length ? props.values : [0, 0];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  return values.map((value, index) => {
    const x = values.length === 1 ? 0 : (index / (values.length - 1)) * 120;
    const y = 32 - ((value - min) / span) * 26;
    return { x, y };
  });
});
const linePath = computed(() =>
  points.value.map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ")
);
const areaPath = computed(() => {
  if (!points.value.length) return "";
  return `${linePath.value} L 120 36 L 0 36 Z`;
});
</script>
