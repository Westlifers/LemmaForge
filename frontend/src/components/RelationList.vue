<template>
  <section class="plain-section">
    <header class="section-header">
      <div>
        <h3>{{ title }}</h3>
        <p>{{ relations.length }} relation{{ relations.length === 1 ? "" : "s" }}</p>
      </div>
      <span class="panel-icon">
        <GitBranch :size="16" aria-hidden="true" />
      </span>
    </header>
    <p v-if="!relations.length" class="empty-state">No relations recorded.</p>
    <ul v-else class="compact-list">
      <li v-for="relation in relations" :key="relation.id" class="relation-row">
        <code>{{ relation.source_fragment_id }}</code>
        <select :value="relation.relation_kind" @change="updateKind(relation, $event)">
          <option v-if="isLegacyRelationKind(relation.relation_kind)" :value="relation.relation_kind" disabled>
            Legacy: {{ relation.relation_kind }}
          </option>
          <optgroup label="Recommended">
            <option v-for="kind in relationKindOptions(null, relation.relation_kind).recommended" :key="kind" :value="kind">{{ kind }}</option>
          </optgroup>
          <optgroup label="Other">
            <option v-for="kind in relationKindOptions(null, relation.relation_kind).regular" :key="kind" :value="kind">{{ kind }}</option>
          </optgroup>
          <optgroup v-if="showAdvanced" label="Advanced">
            <option v-for="kind in relationKindOptions(null, relation.relation_kind).advanced" :key="kind" :value="kind">{{ kind }}</option>
          </optgroup>
        </select>
        <span v-if="isLegacyRelationKind(relation.relation_kind)" class="chip" data-chip="warning">Legacy</span>
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
        <button class="icon-button" type="button" aria-label="Delete relation" title="Delete relation" @click="$emit('delete', relation.id)">
          <Trash2 :size="16" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { GitBranch, Trash2 } from "lucide-vue-next";
import type { Relation } from "../types";
import { isLegacyRelationKind, relationKindOptions } from "../utils/relationKinds";

defineProps<{ title: string; relations: Relation[]; showAdvanced?: boolean }>();
const emit = defineEmits<{
  update: [id: string, payload: { relation_kind?: string; confidence?: number | null }];
  delete: [id: string];
}>();

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
