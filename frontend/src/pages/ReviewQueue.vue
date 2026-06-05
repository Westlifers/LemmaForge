<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Review Queue</h1>
        <p>Unaccepted fragments waiting to enter the working collection</p>
      </div>
      <RouterLink class="button primary" to="/import">
        <Plus :size="16" aria-hidden="true" />
        New Draft
      </RouterLink>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <div class="list-stack">
      <article v-for="fragment in drafts" :key="fragment.id" class="edit-card">
        <div class="fragment-card__header">
          <span class="badge">{{ fragment.type }}</span>
          <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
          <span v-if="fragment.topic_id">Topic: {{ topicTitle(fragment.topic_id) }}</span>
        </div>
        <h3>{{ fragment.title }}</h3>
        <p>{{ fragment.body }}</p>
        <footer class="action-row">
          <RouterLink class="button subtle" :to="`/fragments/${fragment.id}`">Edit</RouterLink>
          <button class="button primary" type="button" @click="setStatus(fragment, 'working')">
            <Check :size="16" aria-hidden="true" />
            Accept As Working
          </button>
          <button class="button subtle" type="button" @click="setStatus(fragment, 'rejected')">
            <X :size="16" aria-hidden="true" />
            Reject
          </button>
        </footer>
      </article>
      <p v-if="!drafts.length" class="empty-state">No unaccepted fragments waiting for review.</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Check, Plus, X } from "lucide-vue-next";
import { api } from "../api/client";
import { useFragmentsStore } from "../stores/fragments";
import type { Fragment, FragmentStatus, Topic } from "../types";
import { unacceptedFragmentStatuses } from "../types";

const store = useFragmentsStore();
const topics = ref<Topic[]>([]);
const error = ref("");
const drafts = computed(() =>
  store.fragments.filter((fragment) => unacceptedFragmentStatuses.includes(fragment.status))
);

async function load() {
  topics.value = await api.listTopics();
  await store.load();
}

async function setStatus(fragment: Fragment, status: FragmentStatus) {
  try {
    await api.updateFragment(fragment.id, {
      status,
      change_note: `Status changed from ${fragment.status} to ${status}.`
    });
    await store.load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function topicTitle(topicId: string) {
  return topics.value.find((topic) => topic.id === topicId)?.title || topicId;
}

onMounted(load);
</script>
