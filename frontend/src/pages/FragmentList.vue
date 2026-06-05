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
        <section class="status-filter-row" aria-label="Status filters">
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

        <section class="filter-bar">
          <label>
            Search
            <input v-model="filters.search" @input="load" />
          </label>
          <label>
            Type
            <select v-model="filters.type" @change="load">
              <option value="">Any</option>
              <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label>
            Status
            <select v-model="filters.status">
              <option value="">Any</option>
              <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
            </select>
          </label>
          <label>
            Origin
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
            Exactness
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
            Source citekey
            <input v-model="filters.source_citekey" @input="load" />
          </label>
        </section>

        <p v-if="store.error" class="error-text">{{ store.error }}</p>
        <p v-if="store.loading" class="muted">Loading fragments...</p>
        <div class="list-stack">
          <FragmentCard
            v-for="fragment in visibleFragments"
            :key="fragment.id"
            :fragment="fragment"
            :topic-title="topicTitle(fragment.topic_id)"
          />
          <p v-if="!store.loading && !visibleFragments.length" class="empty-state">No fragments match these filters.</p>
        </div>
      </main>

      <aside class="topic-filter-panel">
        <header class="topic-filter-header">
          <div>
            <h2>Topics</h2>
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
            <span>All Topics</span>
            <strong>{{ store.fragments.length }}</strong>
          </button>
          <button
            class="topic-filter-button"
            :class="{ active: topicFilter === unsortedTopicFilter }"
            type="button"
            @click="setTopicFilter(unsortedTopicFilter)"
          >
            <span>Unsorted</span>
            <strong>{{ unsortedCount }}</strong>
          </button>
          <button
            v-for="topic in topics"
            :key="topic.id"
            class="topic-filter-button"
            :class="{ active: topicFilter === topic.id }"
            type="button"
            @click="setTopicFilter(topic.id)"
          >
            <span>{{ topic.title }}</span>
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
import { Plus } from "lucide-vue-next";
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

function load() {
  void store.load({
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
