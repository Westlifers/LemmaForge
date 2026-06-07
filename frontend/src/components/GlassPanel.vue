<template>
  <section class="plain-section glass-panel" :class="variantClass">
    <slot />
  </section>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{ variant?: "default" | "muted" | "danger" }>(), {
  variant: "default"
});

const variantClass = props.variant === "default" ? "" : `glass-panel--${props.variant}`;
</script>
