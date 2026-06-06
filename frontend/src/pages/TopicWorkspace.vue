<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Topic Workspace</h1>
        <p>Create and maintain local topic ids for fragment grouping</p>
      </div>
    </header>

    <div class="split">
      <section class="plain-section editor">
        <label>
          Title
          <input v-model="draft.title" />
        </label>
        <label>
          Description
          <textarea v-model="draft.description" rows="6" />
        </label>
        <footer class="action-row">
          <button class="button primary" type="button" @click="saveTopic">
            {{ editingId ? "Save Topic" : "Create Topic" }}
          </button>
          <button v-if="editingId" class="button subtle" type="button" @click="resetDraft">
            Cancel
          </button>
        </footer>
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="plain-section">
        <article v-for="topic in topics" :key="topic.id" class="edit-card">
          <header class="topic-card-header">
            <div>
              <h3>{{ topic.title }}</h3>
              <code>{{ topic.id }}</code>
            </div>
            <span class="chip" data-chip="topic">{{ fragmentsFor(topic.id).length }} fragments</span>
          </header>
          <p>{{ topic.description || "No description." }}</p>
          <button class="topic-fragment-toggle" type="button" @click="toggleFragments(topic.id)">
            <ChevronRight
              :class="{ open: fragmentsOpen(topic.id) }"
              :size="18"
              aria-hidden="true"
            />
            <span>Attached Fragments</span>
            <strong>{{ fragmentsFor(topic.id).length }}</strong>
          </button>
          <Transition name="collapse">
            <section v-if="fragmentsOpen(topic.id)" class="topic-fragment-list">
              <RouterLink
                v-for="fragment in fragmentsFor(topic.id)"
                :key="fragment.id"
                class="topic-fragment-item"
                :to="`/fragments/${fragment.id}`"
              >
                <div>
                  <strong>{{ fragment.title }}</strong>
                  <small>{{ fragment.origin_classification }} / {{ fragment.exactness }}</small>
                </div>
                <span class="badge">{{ fragment.type }}</span>
                <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
              </RouterLink>
              <p v-if="!fragmentsFor(topic.id).length" class="muted">No fragments assigned.</p>
            </section>
          </Transition>
          <footer class="action-row">
            <button class="button subtle" type="button" @click="edit(topic)">
              <Pencil :size="16" aria-hidden="true" />
              Edit
            </button>
            <button class="button subtle" type="button" @click="remove(topic.id)">
              <Trash2 :size="16" aria-hidden="true" />
              Delete
            </button>
          </footer>
        </article>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { ChevronRight, Pencil, Trash2 } from "lucide-vue-next";
import { api } from "../api/client";
import type { Topic } from "../types";
import { useFragmentsStore } from "../stores/fragments";

const topics = ref<Topic[]>([]);
const fragments = useFragmentsStore();
const editingId = ref("");
const expandedTopicIds = ref<Record<string, boolean>>({});
const message = ref("");
const error = ref("");
const draft = reactive({ title: "", description: "" });

async function load() {
  topics.value = await api.listTopics();
  await fragments.load();
}

async function saveTopic() {
  error.value = "";
  message.value = "";
  try {
    if (editingId.value) {
      await api.updateTopic(editingId.value, {
        title: draft.title,
        description: draft.description || null
      });
      message.value = "Topic updated.";
    } else {
      await api.createTopic({ title: draft.title, description: draft.description || null });
      message.value = "Topic created.";
    }
    resetDraft();
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function edit(topic: Topic) {
  editingId.value = topic.id;
  draft.title = topic.title;
  draft.description = topic.description || "";
}

function resetDraft() {
  editingId.value = "";
  draft.title = "";
  draft.description = "";
}

function fragmentsFor(topicId: string) {
  return fragments.fragments.filter((fragment) => fragment.topic_id === topicId);
}

function fragmentsOpen(topicId: string) {
  return Boolean(expandedTopicIds.value[topicId]);
}

function toggleFragments(topicId: string) {
  expandedTopicIds.value = {
    ...expandedTopicIds.value,
    [topicId]: !expandedTopicIds.value[topicId]
  };
}

async function remove(id: string) {
  await api.deleteTopic(id);
  await load();
}

onMounted(load);
</script>
