<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Import Fragment</h1>
        <p>Write a fragment and store it immediately as a draft</p>
      </div>
      <RouterLink class="button subtle" :to="{ path: '/fragments', query: { status: 'draft' } }">
        <ListChecks :size="16" aria-hidden="true" />
        View Drafts
      </RouterLink>
    </header>

    <div class="split">
      <form class="plain-section editor" @submit.prevent="storeDraft">
        <label>
          Title
          <input v-model="draft.title" />
        </label>
        <div class="form-grid two">
          <label>
            Type
            <select v-model="draft.type">
              <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
            </select>
          </label>
          <label>
            Topic
            <select v-model="draft.topic_id">
              <option :value="null">No topic</option>
              <option v-for="topic in topics" :key="topic.id" :value="topic.id">{{ topic.title }}</option>
            </select>
          </label>
          <label>
            Origin
            <select v-model="draft.origin_classification">
              <option value="user_original">user_original</option>
              <option value="assistant_generated">assistant_generated</option>
              <option value="external_source">external_source</option>
              <option value="mixed">mixed</option>
              <option value="unknown">unknown</option>
            </select>
          </label>
          <label>
            Exactness
            <select v-model="draft.exactness">
              <option value="quote">quote</option>
              <option value="close_paraphrase">close_paraphrase</option>
              <option value="paraphrase">paraphrase</option>
              <option value="interpretation">interpretation</option>
              <option value="reconstruction">reconstruction</option>
              <option value="original">original</option>
            </select>
          </label>
        </div>
        <label>
          Body
          <textarea v-model="draft.body" required rows="16" />
        </label>
        <button class="button primary" type="submit">
          <Save :size="16" aria-hidden="true" />
          Store Draft
        </button>
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </form>

      <section class="plain-section">
        <h2>Recent Drafts</h2>
        <div class="list-stack">
          <FragmentCard
            v-for="fragment in recentDrafts"
            :key="fragment.id"
            :fragment="fragment"
            :topic-title="topicTitle(fragment.topic_id)"
          />
          <p v-if="!recentDrafts.length" class="muted">No draft fragments yet.</p>
        </div>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ListChecks, Save } from "lucide-vue-next";
import { api } from "../api/client";
import FragmentCard from "../components/FragmentCard.vue";
import { useFragmentsStore } from "../stores/fragments";
import type { Fragment, Topic } from "../types";
import { fragmentTypes } from "../types";

const fragments = useFragmentsStore();
const topics = ref<Topic[]>([]);
const message = ref("");
const error = ref("");
const draft = reactive<Partial<Fragment>>({
  title: "",
  type: "Definition",
  status: "draft",
  body: "",
  topic_id: null,
  origin_classification: "user_original",
  exactness: "original"
});

const recentDrafts = computed(() =>
  fragments.fragments.filter((fragment) => fragment.status === "draft").slice(0, 8)
);

async function load() {
  topics.value = await api.listTopics();
  await fragments.load({ status: "draft" });
}

async function storeDraft() {
  error.value = "";
  message.value = "";
  try {
    const title = (draft.title || "").trim() || firstTitle(draft.body || "");
    const fragment = await api.createFragment({
      ...draft,
      title,
      status: "draft",
      topic_id: draft.topic_id || null
    });
    message.value = `Stored draft fragment ${fragment.id}.`;
    draft.title = "";
    draft.body = "";
    await fragments.load({ status: "draft" });
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function firstTitle(value: string) {
  const compact = value.trim().replace(/\s+/g, " ");
  return compact.split(/[.:\n]/, 1)[0]?.slice(0, 90) || "Untitled draft";
}

function topicTitle(topicId: string | null) {
  if (!topicId) return undefined;
  return topics.value.find((topic) => topic.id === topicId)?.title;
}

onMounted(load);
</script>
