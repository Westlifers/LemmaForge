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
        <span class="badge">
          <FileText :size="13" aria-hidden="true" />
          {{ fragment.type }}
        </span>
        <span class="status" :data-status="fragment.status">
          <CircleDot :size="13" aria-hidden="true" />
          {{ fragment.status }}
        </span>
      </div>
    </div>
    <RouterLink class="fragment-card__link" :to="`/fragments/${fragment.id}`">
      <h3>{{ fragment.title }}</h3>
      <MarkdownLatexRenderer class="card-tex-preview" :body="fragment.body" />
      <footer>
        <span class="chip" data-chip="origin">
          <Fingerprint :size="13" aria-hidden="true" />
          {{ fragment.origin_classification }}
        </span>
        <span v-if="isAiExtracted" class="chip" data-chip="ai">
          <Sparkles :size="13" aria-hidden="true" />
          AI extracted
        </span>
        <span class="chip" data-chip="exactness">
          <Quote :size="13" aria-hidden="true" />
          {{ fragment.exactness }}
        </span>
        <span v-if="fragment.topic_id" class="chip" data-chip="topic">
          <Network :size="13" aria-hidden="true" />
          {{ topicTitle || fragment.topic_id }}
        </span>
      </footer>
    </RouterLink>
  </article>
</template>

<script setup lang="ts">
import type { Fragment } from "../types";
import { computed } from "vue";
import { CircleDot, FileText, Fingerprint, Network, Quote, Sparkles } from "lucide-vue-next";
import MarkdownLatexRenderer from "./MarkdownLatexRenderer.vue";

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
