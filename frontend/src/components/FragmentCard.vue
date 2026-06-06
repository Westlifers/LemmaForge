<template>
  <article class="fragment-card" :class="{ selectable, selected }">
    <div class="fragment-card__top">
      <label v-if="selectable" class="batch-select-control" @click.stop>
        <input
          :checked="selected"
          type="checkbox"
          @change="$emit('select', fragment.id, ($event.target as HTMLInputElement).checked)"
        />
        <span class="sr-only">Select {{ fragment.title }}</span>
      </label>
      <div class="fragment-card__header">
        <span class="badge">{{ fragment.type }}</span>
        <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
      </div>
    </div>
    <RouterLink class="fragment-card__link" :to="`/fragments/${fragment.id}`">
      <h3>{{ fragment.title }}</h3>
      <p>{{ fragment.body }}</p>
      <footer>
        <span class="chip" data-chip="origin">Origin: {{ fragment.origin_classification }}</span>
        <span v-if="isAiExtracted" class="chip" data-chip="ai">AI extracted</span>
        <span class="chip" data-chip="exactness">Exactness: {{ fragment.exactness }}</span>
        <span v-if="fragment.topic_id" class="chip" data-chip="topic">
          Topic: {{ topicTitle || fragment.topic_id }}
        </span>
      </footer>
    </RouterLink>
  </article>
</template>

<script setup lang="ts">
import type { Fragment } from "../types";
import { computed } from "vue";

const props = withDefaults(
  defineProps<{ fragment: Fragment; topicTitle?: string; selectable?: boolean; selected?: boolean }>(),
  {
    selectable: false,
    selected: false
  }
);
defineEmits<{
  select: [fragmentId: string, selected: boolean];
}>();
const isAiExtracted = computed(() =>
  ["assistant_generated", "mixed"].includes(props.fragment.origin_classification)
);
</script>
