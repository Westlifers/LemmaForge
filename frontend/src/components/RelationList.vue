<template>
  <section class="plain-section">
    <h3>{{ title }}</h3>
    <p v-if="!relations.length" class="muted">No relations recorded.</p>
    <ul v-else class="compact-list">
      <li v-for="relation in relations" :key="relation.id" class="relation-row">
        <code>{{ relation.source_fragment_id }}</code>
        <select :value="relation.relation_kind" @change="updateKind(relation, $event)">
          <option v-for="kind in relationKinds" :key="kind" :value="kind">{{ kind }}</option>
        </select>
        <code>{{ relation.target_fragment_id }}</code>
        <input
          :value="relation.confidence ?? ''"
          min="0"
          max="1"
          step="0.01"
          type="number"
          aria-label="Relation confidence"
          @change="updateConfidence(relation, $event)"
        />
        <button class="icon-button" type="button" title="Delete relation" @click="$emit('delete', relation.id)">
          <Trash2 :size="16" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { Trash2 } from "lucide-vue-next";
import type { Relation } from "../types";

defineProps<{ title: string; relations: Relation[] }>();
const emit = defineEmits<{
  update: [id: string, payload: { relation_kind?: string; confidence?: number | null }];
  delete: [id: string];
}>();

const relationKinds = [
  "depends_on",
  "uses",
  "proves",
  "proof_of",
  "refines",
  "replaces",
  "contradicts",
  "generalizes",
  "specializes_to",
  "is_example_of",
  "is_counterexample_to",
  "cites",
  "quotes",
  "paraphrases",
  "restates",
  "adopts_notation_from",
  "depends_on_notation",
  "inspired_by",
  "generalizes_external_result",
  "specializes_external_result",
  "questions_external_claim",
  "compares_with",
  "came_from"
];

function updateKind(relation: Relation, event: Event) {
  emit("update", relation.id, {
    relation_kind: (event.target as HTMLSelectElement).value
  });
}

function updateConfidence(relation: Relation, event: Event) {
  const value = (event.target as HTMLInputElement).value;
  emit("update", relation.id, {
    confidence: value === "" ? null : Number(value)
  });
}
</script>

