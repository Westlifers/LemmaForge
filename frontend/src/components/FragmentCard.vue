<template>
  <RouterLink class="fragment-card" :to="`/fragments/${fragment.id}`">
    <div class="fragment-card__header">
      <span class="badge">{{ fragment.type }}</span>
      <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
    </div>
    <h3>{{ fragment.title }}</h3>
    <p>{{ fragment.body }}</p>
    <footer>
      <span class="chip" data-chip="origin">Origin: {{ fragment.origin_classification }}</span>
      <span class="chip" data-chip="exactness">Exactness: {{ fragment.exactness }}</span>
      <span v-if="fragment.topic_id" class="chip" data-chip="topic">
        Topic: {{ topicTitle || fragment.topic_id }}
      </span>
    </footer>
  </RouterLink>
</template>

<script setup lang="ts">
import type { Fragment } from "../types";

defineProps<{ fragment: Fragment; topicTitle?: string }>();
</script>
