<template>
  <section class="page problem-page">
    <header class="page-header">
      <div>
        <span class="eyebrow">Research units</span>
        <h1>Problems</h1>
        <p>Concrete mathematical objectives that organize topics, fragments, and future attempts.</p>
      </div>
      <button class="button primary" type="button" @click="newProblem">
        <CirclePlus :size="16" aria-hidden="true" />
        New Problem
      </button>
    </header>

    <section class="filter-card problem-filter-card">
      <label>
        Search
        <input v-model="filters.search" placeholder="Search title, objective, formulation..." @input="load" />
      </label>
      <label>
        Status
        <select v-model="filters.status" @change="load">
          <option value="">All statuses</option>
          <option v-for="status in problemStatuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
    </section>

    <div class="problem-list-grid">
      <section class="plain-section problem-editor">
        <header class="section-header">
          <div>
            <h2>{{ editingId ? "Edit Problem" : "Create Problem" }}</h2>
            <p>Problem is the research unit above fragments and topics.</p>
          </div>
        </header>
        <label>
          Title
          <input v-model="draft.title" />
        </label>
        <label>
          Status
          <select v-model="draft.status">
            <option v-for="status in problemStatuses" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
        <label>
          Objective
          <textarea v-model="draft.objective" rows="4" />
        </label>
        <label>
          Current formulation
          <textarea v-model="draft.current_formulation" rows="4" />
        </label>
        <label>
          Motivation
          <textarea v-model="draft.motivation" rows="3" />
        </label>
        <label>
          Why it matters
          <textarea v-model="draft.why_it_matters" rows="3" />
        </label>
        <footer class="action-row">
          <button class="button primary" type="button" :disabled="saving" @click="saveProblem">
            <Save :size="16" aria-hidden="true" />
            {{ editingId ? "Save" : "Create" }}
          </button>
          <button v-if="editingId" class="button subtle" type="button" @click="resetDraft">Cancel</button>
        </footer>
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="problem-card-list">
        <article v-for="problem in problems" :key="problem.id" class="workspace-panel problem-card">
          <header>
            <div>
              <RouterLink class="problem-title-link" :to="`/problems/${problem.id}`">
                {{ problem.title }}
              </RouterLink>
              <p>{{ problem.objective }}</p>
            </div>
            <span class="status" :data-status="problem.status">{{ problem.status }}</span>
          </header>
          <div class="problem-card-meta">
            <span><Network :size="14" aria-hidden="true" /> {{ problem.topic_links.length }} topics</span>
            <span><Library :size="14" aria-hidden="true" /> {{ problem.fragment_links.length }} fragments</span>
          </div>
          <footer class="action-row">
            <RouterLink class="button primary" :to="`/problems/${problem.id}`">
              <PanelRightOpen :size="16" aria-hidden="true" />
              Workspace
            </RouterLink>
            <button class="button subtle" type="button" @click="editProblem(problem)">
              <Pencil :size="16" aria-hidden="true" />
              Edit
            </button>
            <button class="button danger" type="button" @click="problemToDelete = problem">
              <Trash2 :size="16" aria-hidden="true" />
              Delete
            </button>
          </footer>
        </article>
        <p v-if="!problems.length" class="empty-state">No problems yet. Create one from a current topic or fragment cluster.</p>
      </section>
    </div>

    <Transition name="modal-fade">
      <section v-if="problemToDelete" class="modal-backdrop" @click.self="problemToDelete = null">
        <div class="modal-panel danger-panel">
          <header>
            <div>
              <h2>Delete problem?</h2>
              <p>This removes only the problem and its links. Fragments and topics stay intact.</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="problemToDelete = null">
              <X :size="18" aria-hidden="true" />
            </button>
          </header>
          <footer class="action-row">
            <button class="button subtle" type="button" @click="problemToDelete = null">Cancel</button>
            <button class="button danger" type="button" @click="deleteProblem">Delete Problem</button>
          </footer>
        </div>
      </section>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import {
  CirclePlus,
  Library,
  Network,
  PanelRightOpen,
  Pencil,
  Save,
  Trash2,
  X
} from "lucide-vue-next";
import { api } from "../api/client";
import type { ProblemStatus, ResearchProblem } from "../types";
import { problemStatuses } from "../types";

const problems = ref<ResearchProblem[]>([]);
const editingId = ref("");
const saving = ref(false);
const message = ref("");
const error = ref("");
const problemToDelete = ref<ResearchProblem | null>(null);
const filters = reactive({ search: "", status: "" });
const draft = reactive({
  title: "",
  status: "open" as ProblemStatus,
  objective: "",
  current_formulation: "",
  motivation: "",
  why_it_matters: ""
});

async function load() {
  problems.value = await api.listProblems({
    search: filters.search,
    status: filters.status
  });
}

function newProblem() {
  resetDraft();
}

function editProblem(problem: ResearchProblem) {
  editingId.value = problem.id;
  draft.title = problem.title;
  draft.status = problem.status;
  draft.objective = problem.objective;
  draft.current_formulation = problem.current_formulation || "";
  draft.motivation = problem.motivation || "";
  draft.why_it_matters = problem.why_it_matters || "";
}

function resetDraft() {
  editingId.value = "";
  draft.title = "";
  draft.status = "open";
  draft.objective = "";
  draft.current_formulation = "";
  draft.motivation = "";
  draft.why_it_matters = "";
}

async function saveProblem() {
  error.value = "";
  message.value = "";
  saving.value = true;
  try {
    const payload = {
      title: draft.title,
      status: draft.status,
      objective: draft.objective,
      current_formulation: draft.current_formulation || null,
      motivation: draft.motivation || null,
      why_it_matters: draft.why_it_matters || null
    };
    if (editingId.value) {
      await api.updateProblem(editingId.value, payload);
      message.value = "Problem updated.";
    } else {
      await api.createProblem(payload);
      message.value = "Problem created.";
    }
    resetDraft();
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    saving.value = false;
  }
}

async function deleteProblem() {
  if (!problemToDelete.value) return;
  await api.deleteProblem(problemToDelete.value.id);
  problemToDelete.value = null;
  await load();
}

onMounted(load);
</script>
