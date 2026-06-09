<template>
  <section class="page">
    <header class="page-header">
      <div>
        <RouterLink class="back-link" :to="backTarget">
          <ArrowLeft :size="16" aria-hidden="true" />
          {{ backLabel }}
        </RouterLink>
        <h1>{{ fragment?.title || "Fragment" }}</h1>
        <p v-if="fragment">{{ fragment.type }} / {{ fragment.status }}</p>
      </div>
      <button v-if="fragment" class="button subtle" type="button" @click="editing = !editing">
        <Pencil :size="16" aria-hidden="true" />
        {{ editing ? "Preview" : "Edit" }}
      </button>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="!fragment" class="muted">Loading fragment...</p>

    <div v-else class="detail-grid">
      <section class="plain-section">
        <FragmentEditor v-if="editing" :fragment="fragment" :topics="topics" @save="save" />
        <div v-else class="fragment-preview">
          <div class="metadata-strip">
            <span class="badge">{{ fragment.type }}</span>
            <StatusBadge :status="fragment.status" />
            <span class="chip" data-chip="origin">Origin: {{ fragment.origin_classification }}</span>
            <span v-if="isAiExtracted" class="chip" data-chip="ai">AI extracted</span>
            <span class="chip" data-chip="exactness">Exactness: {{ fragment.exactness }}</span>
            <span v-if="fragment.topic_id" class="chip" data-chip="topic">Topic: {{ topicTitle(fragment.topic_id) }}</span>
          </div>
          <MarkdownLatexRenderer :body="fragment.body" />
        </div>
      </section>

      <aside class="side-panel">
        <section class="plain-section topic-panel">
          <header class="section-header">
            <h3>Topic</h3>
            <RouterLink class="text-button" to="/topics">Manage</RouterLink>
          </header>
          <label>
            Assigned topic
            <select :value="fragment.topic_id || ''" @change="assignTopic">
              <option value="">No topic</option>
              <option v-for="topic in topics" :key="topic.id" :value="topic.id">{{ topic.title }}</option>
            </select>
          </label>
          <p v-if="!topics.length" class="muted">Create topics in the topic workspace first.</p>
          <p v-if="topicMessage" class="success-text">{{ topicMessage }}</p>
        </section>
        <section class="plain-section relation-tool">
          <button class="button subtle" type="button" @click="relationEditorOpen = !relationEditorOpen">
            <X v-if="relationEditorOpen" :size="16" aria-hidden="true" />
            <Plus v-else :size="16" aria-hidden="true" />
            {{ relationEditorOpen ? "Cancel Relation" : "Add Relation" }}
          </button>
          <Transition name="collapse">
            <form v-if="relationEditorOpen" class="editor relation-form" @submit.prevent="createRelation">
              <label>
                Kind
                <select v-model="newRelation.kind">
                  <optgroup label="Recommended">
                    <option v-for="kind in relationKindOptions(fragment?.type, newRelation.kind).recommended" :key="kind" :value="kind">{{ kind }}</option>
                  </optgroup>
                  <optgroup label="Other">
                    <option v-for="kind in relationKindOptions(fragment?.type, newRelation.kind).regular" :key="kind" :value="kind">{{ kind }}</option>
                  </optgroup>
                  <optgroup v-if="showAdvancedRelationKinds" label="Advanced">
                    <option v-for="kind in relationKindOptions(fragment?.type, newRelation.kind).advanced" :key="kind" :value="kind">{{ kind }}</option>
                  </optgroup>
                </select>
              </label>
              <label class="inline-check">
                <input v-model="showAdvancedRelationKinds" type="checkbox" />
                Show advanced relations
              </label>
              <label>
                Target
                <select v-model="newRelation.target" required>
                  <option value="">Target fragment</option>
                  <option v-for="item in allFragments" :key="item.id" :value="item.id">{{ item.title }}</option>
                </select>
              </label>
              <label>
                Confidence
                <input v-model.number="newRelation.confidence" min="0" max="1" step="0.01" type="number" />
              </label>
              <button class="button primary" type="submit" :disabled="!newRelation.target">
                Create
              </button>
            </form>
          </Transition>
        </section>
        <RelationList title="Outgoing Relations" :relations="outgoingRelations" :show-advanced="showAdvancedRelationKinds" @update="updateRelation" @delete="deleteRelation" />
        <RelationList title="Incoming Relations" :relations="incomingRelations" :show-advanced="showAdvancedRelationKinds" @update="updateRelation" @delete="deleteRelation" />
        <SourcePointerView :pointers="sourcePointers" />
        <section class="plain-section">
          <h3>Versions</h3>
          <ul class="compact-list">
            <li v-for="version in versions" :key="version.id">
              <span>v{{ version.version_number }}</span>
              <span>{{ version.change_note || "No note" }}</span>
            </li>
          </ul>
        </section>
        <section class="plain-section danger-panel">
          <header class="section-header">
            <h3>Danger Zone</h3>
          </header>
          <p>
            Deleting permanently removes this fragment and its local relations. Marking it rejected is usually safer.
          </p>
          <div class="action-row">
            <button
              class="button subtle"
              type="button"
              :disabled="fragment.status === 'rejected'"
              @click="markRejected"
            >
              <ArchiveX :size="16" aria-hidden="true" />
              Mark Rejected
            </button>
            <button class="button danger" type="button" @click="deleteConfirmOpen = !deleteConfirmOpen">
              <Trash2 :size="16" aria-hidden="true" />
              Delete
            </button>
          </div>
        </section>
      </aside>
    </div>

    <Transition name="modal-fade">
      <section v-if="deleteConfirmOpen" class="modal-backdrop" @click.self="deleteConfirmOpen = false">
        <div class="modal-panel danger-panel">
          <header class="section-header">
            <div class="warning-heading">
              <AlertTriangle :size="18" aria-hidden="true" />
              <h2>Permanent Delete</h2>
            </div>
            <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="deleteConfirmOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <p>
            This removes the fragment from SQLite, deletes related relations/source pointers/context-pack links,
            and removes its Markdown file from the vault.
          </p>
          <div class="action-row">
            <button class="button subtle" type="button" @click="deleteConfirmOpen = false">Cancel</button>
            <button class="button danger" type="button" :disabled="deleteLoading" @click="deleteCurrentFragment">
              <Trash2 :size="16" aria-hidden="true" />
              {{ deleteLoading ? "Deleting..." : "Delete Permanently" }}
            </button>
          </div>
        </div>
      </section>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { AlertTriangle, ArchiveX, ArrowLeft, Pencil, Plus, Trash2, X } from "lucide-vue-next";
import { api } from "../api/client";
import FragmentEditor from "../components/FragmentEditor.vue";
import MarkdownLatexRenderer from "../components/MarkdownLatexRenderer.vue";
import RelationList from "../components/RelationList.vue";
import SourcePointerView from "../components/SourcePointerView.vue";
import StatusBadge from "../components/StatusBadge.vue";
import type { Fragment, FragmentVersion, Relation, SourcePointer, Topic } from "../types";
import { relationKindOptions } from "../utils/relationKinds";

const props = defineProps<{ id: string }>();
const route = useRoute();
const router = useRouter();
const fragment = ref<Fragment | null>(null);
const versions = ref<FragmentVersion[]>([]);
const outgoingRelations = ref<Relation[]>([]);
const incomingRelations = ref<Relation[]>([]);
const sourcePointers = ref<SourcePointer[]>([]);
const allFragments = ref<Fragment[]>([]);
const topics = ref<Topic[]>([]);
const editing = ref(false);
const relationEditorOpen = ref(false);
const deleteConfirmOpen = ref(false);
const deleteLoading = ref(false);
const showAdvancedRelationKinds = ref(false);
const error = ref("");
const topicMessage = ref("");
const newRelation = ref({
  kind: "depends_on",
  target: "",
  confidence: null as number | null
});
const isAiExtracted = computed(() =>
  fragment.value ? ["assistant_generated", "mixed"].includes(fragment.value.origin_classification) : false
);
const backTarget = computed(() => safeBackPath(route.query.from) || "/fragments");
const backLabel = computed(() => stringQuery(route.query.from_label) || "Fragments");

async function load() {
  error.value = "";
  try {
    fragment.value = await api.getFragment(props.id);
    versions.value = await api.listVersions(props.id);
    outgoingRelations.value = await api.listOutgoingRelations(props.id);
    incomingRelations.value = await api.listIncomingRelations(props.id);
    sourcePointers.value = await api.listSourcePointers(props.id);
    allFragments.value = (await api.listFragments()).filter((item) => item.id !== props.id);
    topics.value = await api.listTopics();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function createRelation() {
  if (!fragment.value || !newRelation.value.target) return;
  try {
    await api.createRelation({
      source_fragment_id: fragment.value.id,
      relation_kind: newRelation.value.kind,
      target_fragment_id: newRelation.value.target,
      confidence: newRelation.value.confidence
    });
    newRelation.value.target = "";
    relationEditorOpen.value = false;
    outgoingRelations.value = await api.listOutgoingRelations(fragment.value.id);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function assignTopic(event: Event) {
  if (!fragment.value) return;
  topicMessage.value = "";
  const topicId = (event.target as HTMLSelectElement).value || null;
  try {
    fragment.value = await api.updateFragment(fragment.value.id, {
      topic_id: topicId,
      change_note: topicId ? `Assigned topic ${topicTitle(topicId)}.` : "Cleared topic assignment."
    });
    topicMessage.value = topicId ? "Topic assigned." : "Topic cleared.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function markRejected() {
  if (!fragment.value) return;
  try {
    fragment.value = await api.updateFragment(fragment.value.id, {
      status: "rejected",
      change_note: "Marked rejected instead of deleting."
    });
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function deleteCurrentFragment() {
  if (!fragment.value) return;
  deleteLoading.value = true;
  try {
    await api.deleteFragment(fragment.value.id);
    await router.push(backTarget.value);
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    deleteLoading.value = false;
  }
}

async function updateRelation(id: string, payload: { relation_kind?: string; confidence?: number | null }) {
  if (!fragment.value) return;
  await api.updateRelation(id, payload);
  outgoingRelations.value = await api.listOutgoingRelations(fragment.value.id);
  incomingRelations.value = await api.listIncomingRelations(fragment.value.id);
}

async function deleteRelation(id: string) {
  if (!fragment.value) return;
  await api.deleteRelation(id);
  outgoingRelations.value = await api.listOutgoingRelations(fragment.value.id);
  incomingRelations.value = await api.listIncomingRelations(fragment.value.id);
}

async function save(payload: Partial<Fragment> & { change_note?: string }) {
  if (!fragment.value) return;
  try {
    fragment.value = await api.updateFragment(fragment.value.id, payload);
    versions.value = await api.listVersions(fragment.value.id);
    editing.value = false;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function topicTitle(topicId: string) {
  return topics.value.find((topic) => topic.id === topicId)?.title || topicId;
}

function stringQuery(value: unknown) {
  return typeof value === "string" ? value : "";
}

function safeBackPath(value: unknown) {
  if (typeof value !== "string") return "";
  if (!value.startsWith("/") || value.startsWith("//")) return "";
  return value;
}

onMounted(load);
watch(() => props.id, load);
</script>
