<template>
  <article class="metric-card-v2" :data-tone="tone">
    <header>
      <span class="metric-icon">
        <component :is="icon" :size="19" aria-hidden="true" />
      </span>
      <div>
        <span>{{ label }}</span>
        <strong>{{ value }}</strong>
      </div>
    </header>
    <p>{{ detail }}</p>
    <SparklineChart :values="sparkline" :color="sparkColor" />
  </article>
</template>

<script setup lang="ts">
import SparklineChart from "./SparklineChart.vue";

withDefaults(
  defineProps<{
    label: string;
    value: string | number;
    detail: string;
    sparkline: number[];
    icon: unknown;
    tone?: "accent" | "blue" | "violet" | "warning" | "success" | "danger";
    sparkColor?: string;
  }>(),
  {
    tone: "accent",
    sparkColor: "var(--accent)",
  }
);
</script>
