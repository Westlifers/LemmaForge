<template>
  <section class="workspace-panel" :class="{ compact }">
    <header v-if="$slots.title || title" class="workspace-panel-header">
      <div>
        <slot name="title">
          <h2>{{ title }}</h2>
          <p v-if="subtitle">{{ subtitle }}</p>
        </slot>
      </div>
      <slot name="action" />
    </header>
    <slot />
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title?: string; subtitle?: string; compact?: boolean }>(), {
  title: "",
  subtitle: "",
  compact: false,
});
</script>
