<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>All Fragments</h1>
        <p>Browse the whole local fragment graph by topic, status, and metadata</p>
      </div>
      <button class="button primary" type="button" @click="createQuickFragment">
        <Plus :size="16" aria-hidden="true" />
        New
      </button>
    </header>

    <div class="fragment-browser">
      <main class="fragment-results">
        <section class="batch-toolbar" :class="{ active: selectedIds.length }">
          <div class="batch-toolbar__summary">
            <span class="panel-icon">
              <MousePointer2 :size="16" aria-hidden="true" />
            </span>
            <div>
              <strong>{{ selectedIds.length }} selected</strong>
              <span>{{ visibleFragments.length }} visible in current view</span>
            </div>
          </div>
          <div class="toolbar">
            <button class="button subtle" type="button" :disabled="!visibleFragments.length" @click="selectVisible">
              <CheckSquare :size="16" aria-hidden="true" />
              Select Visible
            </button>
            <button class="button subtle" type="button" :disabled="!selectedIds.length" @click="clearSelection">
              <XCircle :size="16" aria-hidden="true" />
              Clear
            </button>
            <div class="bulk-control-group">
              <select v-model="bulkTopicTarget" :disabled="!selectedIds.length || bulkBusy" aria-label="Bulk topic target">
                <option value="">Move to topic...</option>
                <option :value="unsortedTopicFilter">Unsorted</option>
                <option v-for="topic in topics" :key="topic.id" :value="topic.id">{{ topic.title }}</option>
              </select>
              <button class="button subtle" type="button" :disabled="!canApplyBulkTopic || bulkBusy" @click="applyBulkTopic">
                <MoveRight :size="16" aria-hidden="true" />
                Move
              </button>
            </div>
            <div class="bulk-control-group">
              <select v-model="bulkStatusTarget" :disabled="!selectedIds.length || bulkBusy" aria-label="Bulk status target">
                <option value="">Set status...</option>
                <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
              <button class="button subtle" type="button" :disabled="!canApplyBulkStatus || bulkBusy" @click="applyBulkStatus">
                <RefreshCw :size="16" aria-hidden="true" />
                Update
              </button>
            </div>
            <button class="button danger" type="button" :disabled="!selectedIds.length || bulkBusy" @click="deleteConfirmOpen = true">
              <Trash2 :size="16" aria-hidden="true" />
              Delete
            </button>
          </div>
          <Transition name="collapse">
            <div v-if="deleteConfirmOpen" class="delete-confirmation">
              <div class="warning-heading">
                <AlertTriangle :size="18" aria-hidden="true" />
                <strong>Permanent batch delete</strong>
              </div>
              <p>
                This permanently deletes {{ selectedIds.length }} selected fragment{{ selectedIds.length === 1 ? "" : "s" }},
                plus local relations/source pointers/context-pack links. Marking as rejected is usually safer.
              </p>
              <div class="action-row">
                <button class="button subtle" type="button" @click="deleteConfirmOpen = false">Cancel</button>
                <button class="button danger" type="button" :disabled="bulkBusy" @click="deleteSelected">
                  {{ bulkBusy ? "Deleting..." : "Delete Permanently" }}
                </button>
              </div>
            </div>
          </Transition>
          <p v-if="batchMessage" class="success-text">{{ batchMessage }}</p>
          <p v-if="batchError" class="error-text">{{ batchError }}</p>
        </section>

        <section class="status-filter-row glass-panel" aria-label="Status filters">
          <button
            class="filter-chip"
            :class="{ active: filters.status === '' }"
            type="button"
            @click="setStatusFilter('')"
          >
            All Statuses
            <strong>{{ statusCount('') }}</strong>
          </button>
          <button
            v-for="status in fragmentStatuses"
            :key="status"
            class="filter-chip"
            :class="{ active: filters.status === status }"
            type="button"
            @click="setStatusFilter(status)"
          >
            {{ status }}
            <strong>{{ statusCount(status) }}</strong>
          </button>
        </section>

        <section class="fragment-filter-shell">
          <header class="filter-bar-header">
            <div>
              <h2>
                <ListFilter :size="17" aria-hidden="true" />
                Filters
              </h2>
              <p>{{ activeFilterCount }} active filter{{ activeFilterCount === 1 ? "" : "s" }}</p>
            </div>
            <div class="toolbar">
              <button class="button subtle" type="button" :disabled="!activeFilterCount" @click="clearFilters">
                <XCircle :size="16" aria-hidden="true" />
                Reset
              </button>
              <button class="button subtle" type="button" @click="filtersOpen = !filtersOpen">
                <ChevronDown :class="{ open: filtersOpen }" :size="16" aria-hidden="true" />
                {{ filtersOpen ? "Hide Filters" : "Show Filters" }}
              </button>
            </div>
          </header>
          <Transition name="collapse">
            <div v-if="filtersOpen" class="filter-bar fragment-filter-panel">
              <label>
                <span class="label-title">
                  <Search :size="14" aria-hidden="true" />
                  Search
                </span>
                <input v-model="filters.search" @input="load" />
              </label>
              <label>
                <span class="label-title">
                  <FileText :size="14" aria-hidden="true" />
                  Type
                </span>
                <select v-model="filters.type" @change="load">
                  <option value="">Any</option>
                  <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
                </select>
              </label>
              <label>
                <span class="label-title">
                  <Fingerprint :size="14" aria-hidden="true" />
                  Origin
                </span>
                <select v-model="filters.origin_classification" @change="load">
                  <option value="">Any</option>
                  <option value="user_original">user_original</option>
                  <option value="assistant_generated">assistant_generated</option>
                  <option value="external_source">external_source</option>
                  <option value="mixed">mixed</option>
                  <option value="unknown">unknown</option>
                </select>
              </label>
              <label>
                <span class="label-title">
                  <Quote :size="14" aria-hidden="true" />
                  Exactness
                </span>
                <select v-model="filters.exactness" @change="load">
                  <option value="">Any</option>
                  <option value="quote">quote</option>
                  <option value="close_paraphrase">close_paraphrase</option>
                  <option value="paraphrase">paraphrase</option>
                  <option value="interpretation">interpretation</option>
                  <option value="reconstruction">reconstruction</option>
                  <option value="original">original</option>
                </select>
              </label>
              <label>
                <span class="label-title">
                  <BookKey :size="14" aria-hidden="true" />
                  Source citekey
                </span>
                <input v-model="filters.source_citekey" @input="load" />
              </label>
            </div>
          </Transition>
        </section>

        <p v-if="store.error" class="error-text">{{ store.error }}</p>
        <p v-if="store.loading" class="muted">Loading fragments...</p>
        <div class="list-stack">
          <FragmentCard
            v-for="fragment in visibleFragments"
            :key="fragment.id"
            :fragment="fragment"
            :draggable="true"
            :selectable="true"
            :selected="selectedSet.has(fragment.id)"
            :topic-title="topicTitle(fragment.topic_id)"
            @select="setSelected"
            @dragstart="startDrag(fragment.id)"
          />
          <p v-if="!store.loading && !visibleFragments.length" class="empty-state">No fragments match these filters.</p>
        </div>
      </main>

      <aside class="topic-filter-panel">
        <header class="topic-filter-header">
          <div>
            <h2>
              <Network :size="17" aria-hidden="true" />
              Topics
            </h2>
            <p>{{ visibleFragments.length }} of {{ store.fragments.length }} shown</p>
          </div>
          <RouterLink class="text-button" to="/topics">
            Manage
          </RouterLink>
        </header>
        <div class="topic-filter-grid">
          <button
            class="topic-filter-button"
            :class="{ active: topicFilter === '' }"
            type="button"
            @click="setTopicFilter('')"
          >
            <span><Layers :size="14" aria-hidden="true" /> All Topics</span>
            <strong>{{ store.fragments.length }}</strong>
          </button>
          <button
            class="topic-filter-button"
            :class="{ active: topicFilter === unsortedTopicFilter, dragging: dragOverTopic === unsortedTopicFilter }"
            type="button"
            @dragover.prevent="dragOverTopic = unsortedTopicFilter"
            @dragleave="dragOverTopic = null"
            @drop="dropOnTopic(unsortedTopicFilter)"
            @click="setTopicFilter(unsortedTopicFilter)"
          >
            <span><Inbox :size="14" aria-hidden="true" /> Unsorted</span>
            <strong>{{ unsortedCount }}</strong>
          </button>
          <button
            v-for="topic in topics"
            :key="topic.id"
            class="topic-filter-button"
            :class="{ active: topicFilter === topic.id, dragging: dragOverTopic === topic.id }"
            type="button"
            @dragover.prevent="dragOverTopic = topic.id"
            @dragleave="dragOverTopic = null"
            @drop="dropOnTopic(topic.id)"
            @click="setTopicFilter(topic.id)"
          >
            <span><Network :size="14" aria-hidden="true" /> {{ topic.title }}</span>
            <strong>{{ countForTopic(topic.id) }}</strong>
          </button>
        </div>
      </aside>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  AlertTriangle,
  BookKey,
  CheckSquare,
  ChevronDown,
  FileText,
  Fingerprint,
  Inbox,
  Layers,
  ListFilter,
  MousePointer2,
  MoveRight,
  Network,
  Plus,
  Quote,
  RefreshCw,
  Search,
  Trash2,
  XCircle,
} from "lucide-vue-next";
import FragmentCard from "../components/FragmentCard.vue";
import { api } from "../api/client";
import { useFragmentsStore } from "../stores/fragments";
import type { FragmentStatus, Topic } from "../types";
import { fragmentStatuses, fragmentTypes } from "../types";

const route = useRoute();
const router = useRouter();
const store = useFragmentsStore();
const topics = ref<Topic[]>([]);
const unsortedTopicFilter = "__unsorted__";
const topicFilter = ref(stringQuery(route.query.topic_id));
const selectedIds = ref<string[]>([]);
const bulkTopicTarget = ref("");
const bulkStatusTarget = ref("");
const bulkBusy = ref(false);
const deleteConfirmOpen = ref(false);
const filtersOpen = ref(true);
const batchMessage = ref("");
const batchError = ref("");
const dragOverTopic = ref<string | null>(null);
const filters = reactive({
  search: stringQuery(route.query.search),
  type: stringQuery(route.query.type),
  status: stringQuery(route.query.status),
  origin_classification: stringQuery(route.query.origin_classification),
  exactness: stringQuery(route.query.exactness),
  source_citekey: stringQuery(route.query.source_citekey)
});

const visibleFragments = computed(() => {
  return store.fragments.filter((fragment) => {
    const matchesStatus = !filters.status || fragment.status === filters.status;
    const matchesTopic =
      !topicFilter.value ||
      (topicFilter.value === unsortedTopicFilter && !fragment.topic_id) ||
      fragment.topic_id === topicFilter.value;
    return matchesStatus && matchesTopic;
  });
});

const unsortedCount = computed(() => store.fragments.filter((fragment) => !fragment.topic_id).length);
const selectedSet = computed(() => new Set(selectedIds.value));
const canApplyBulkTopic = computed(() => selectedIds.value.length > 0 && bulkTopicTarget.value !== "");
const canApplyBulkStatus = computed(() => selectedIds.value.length > 0 && bulkStatusTarget.value !== "");
const activeFilterCount = computed(
  () =>
    [
      filters.search,
      filters.type,
      filters.status,
      filters.origin_classification,
      filters.exactness,
      filters.source_citekey,
    ].filter(Boolean).length
);

async function load() {
  await store.load({
    search: filters.search,
    type: filters.type,
    origin_classification: filters.origin_classification,
    exactness: filters.exactness,
    source_citekey: filters.source_citekey
  });
}

function topicTitle(topicId: string | null) {
  if (!topicId) return undefined;
  return topics.value.find((topic) => topic.id === topicId)?.title;
}

function setTopicFilter(value: string) {
  topicFilter.value = value;
}

function setStatusFilter(value: "" | FragmentStatus) {
  filters.status = value;
}

function clearFilters() {
  filters.search = "";
  filters.type = "";
  filters.status = "";
  filters.origin_classification = "";
  filters.exactness = "";
  filters.source_citekey = "";
  void load();
}

function setSelected(fragmentId: string, selected: boolean) {
  batchMessage.value = "";
  batchError.value = "";
  const next = new Set(selectedIds.value);
  if (selected) {
    next.add(fragmentId);
  } else {
    next.delete(fragmentId);
  }
  selectedIds.value = [...next];
}

function selectVisible() {
  selectedIds.value = visibleFragments.value.map((fragment) => fragment.id);
}

function clearSelection() {
  selectedIds.value = [];
  deleteConfirmOpen.value = false;
}

function startDrag(fragmentId: string) {
  if (!selectedSet.value.has(fragmentId)) {
    selectedIds.value = [fragmentId];
  }
}

async function dropOnTopic(topicTarget: string) {
  dragOverTopic.value = null;
  if (!selectedIds.value.length) return;
  bulkTopicTarget.value = topicTarget || unsortedTopicFilter;
  await applyBulkTopic();
}

async function applyBulkTopic() {
  if (!canApplyBulkTopic.value) return;
  const target = bulkTopicTarget.value === unsortedTopicFilter ? null : bulkTopicTarget.value;
  const topicName = target ? topicTitle(target) || target : "Unsorted";
  await runBulkOperation(async () => {
    await api.bulkUpdateFragments({
      ids: selectedIds.value,
      topic_id: target,
      change_note: `Batch moved to ${topicName}.`
    });
    batchMessage.value = `Moved ${selectedIds.value.length} fragment${selectedIds.value.length === 1 ? "" : "s"} to ${topicName}.`;
    bulkTopicTarget.value = "";
  });
}

async function applyBulkStatus() {
  if (!canApplyBulkStatus.value) return;
  const status = bulkStatusTarget.value as FragmentStatus;
  await runBulkOperation(async () => {
    await api.bulkUpdateFragments({
      ids: selectedIds.value,
      status,
      change_note: `Batch set status to ${status}.`
    });
    batchMessage.value = `Set ${selectedIds.value.length} fragment${selectedIds.value.length === 1 ? "" : "s"} to ${status}.`;
    bulkStatusTarget.value = "";
  });
}

async function deleteSelected() {
  if (!selectedIds.value.length) return;
  await runBulkOperation(async () => {
    const count = selectedIds.value.length;
    await api.bulkDeleteFragments(selectedIds.value);
    batchMessage.value = `Deleted ${count} fragment${count === 1 ? "" : "s"}.`;
    clearSelection();
  });
}

async function runBulkOperation(operation: () => Promise<void>) {
  bulkBusy.value = true;
  batchError.value = "";
  batchMessage.value = "";
  try {
    await operation();
    await load();
  } catch (caught) {
    batchError.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    bulkBusy.value = false;
    deleteConfirmOpen.value = false;
  }
}

function countForTopic(topicId: string) {
  return store.fragments.filter((fragment) => fragment.topic_id === topicId).length;
}

function statusCount(status: "" | FragmentStatus) {
  return store.fragments.filter((fragment) => {
    const matchesStatus = !status || fragment.status === status;
    const matchesTopic =
      !topicFilter.value ||
      (topicFilter.value === unsortedTopicFilter && !fragment.topic_id) ||
      fragment.topic_id === topicFilter.value;
    return matchesStatus && matchesTopic;
  }).length;
}

async function createQuickFragment() {
  const fragment = await api.createFragment({
    type: "ContextNote",
    title: "Untitled fragment",
    status: "working",
    body: "Draft body.",
    origin_classification: "user_original",
    exactness: "original"
  });
  await router.push(`/fragments/${fragment.id}`);
}

function stringQuery(value: unknown) {
  return typeof value === "string" ? value : "";
}

onMounted(async () => {
  topics.value = await api.listTopics();
  load();
});
</script>
