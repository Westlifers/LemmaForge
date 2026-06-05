<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Topic Workspace</h1>
        <p>Create and maintain local topic ids for fragment grouping</p>
      </div>
      <button class="button primary" type="button" @click="create">
        <Plus :size="16" aria-hidden="true" />
        Create
      </button>
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
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="plain-section">
        <article v-for="topic in topics" :key="topic.id" class="edit-card">
          <h3>{{ topic.title }}</h3>
          <code>{{ topic.id }}</code>
          <p>{{ topic.description || "No description." }}</p>
          <section class="plain-section">
            <h4>Fragments</h4>
            <ul class="compact-list">
              <li v-for="fragment in fragmentsFor(topic.id)" :key="fragment.id">
                <RouterLink class="text-button" :to="`/fragments/${fragment.id}`">{{ fragment.title }}</RouterLink>
                <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
              </li>
            </ul>
            <p v-if="!fragmentsFor(topic.id).length" class="muted">No fragments assigned.</p>
          </section>
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
import { Pencil, Plus, Trash2 } from "lucide-vue-next";
import { api } from "../api/client";
import type { Topic } from "../types";
import { useFragmentsStore } from "../stores/fragments";

const topics = ref<Topic[]>([]);
const fragments = useFragmentsStore();
const editingId = ref("");
const message = ref("");
const error = ref("");
const draft = reactive({ title: "", description: "" });

async function load() {
  topics.value = await api.listTopics();
  await fragments.load();
}

async function create() {
  error.value = "";
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
    editingId.value = "";
    draft.title = "";
    draft.description = "";
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

function fragmentsFor(topicId: string) {
  return fragments.fragments.filter((fragment) => fragment.topic_id === topicId);
}

async function remove(id: string) {
  await api.deleteTopic(id);
  await load();
}

onMounted(load);
</script>
