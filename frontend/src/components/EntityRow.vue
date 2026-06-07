<template>
  <article class="entity-row">
    <span class="entity-row-icon">
      <component :is="icon" :size="16" aria-hidden="true" />
    </span>
    <div>
      <strong>{{ title }}</strong>
      <small>{{ meta }}</small>
    </div>
    <slot />
  </article>
</template>

<script setup lang="ts">
defineProps<{ icon: unknown; title: string; meta: string }>();
</script>
