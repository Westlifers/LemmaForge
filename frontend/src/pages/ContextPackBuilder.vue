<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Context Packs</h1>
        <p>Manage saved AI context prompts</p>
      </div>
      <RouterLink class="button subtle" to="/topics">
        <Network :size="16" aria-hidden="true" />
        Build From Topic
      </RouterLink>
    </header>

    <div class="split context-pack-manager">
      <section class="plain-section">
        <header class="section-header">
          <h2>Saved Packs</h2>
          <button class="button subtle" type="button" @click="load">
            <RefreshCw :size="16" aria-hidden="true" />
            Refresh
          </button>
        </header>
        <div class="list-stack">
          <article
            v-for="pack in packs"
            :key="pack.id"
            class="context-pack-row"
            :class="{ selected: selectedPackId === pack.id }"
          >
            <button class="context-pack-main" type="button" @click="selectPack(pack)">
              <strong>{{ pack.title }}</strong>
              <span>{{ pack.items.length }} items</span>
              <small>{{ pack.topic_id || "No topic" }}</small>
            </button>
            <div class="action-row">
              <button class="button subtle" type="button" @click="exportPack(pack.id)">
                <Download :size="16" aria-hidden="true" />
                Export
              </button>
              <button class="button danger" type="button" @click="askDelete(pack)">
                <Trash2 :size="16" aria-hidden="true" />
                Delete
              </button>
            </div>
          </article>
          <p v-if="!packs.length" class="muted-panel plain-section">
            Context packs are created from Topic pages.
          </p>
        </div>
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="plain-section">
          <section v-if="selectedPack" class="plain-section context-pack-detail">
          <header class="section-header">
            <div>
              <h2>{{ selectedPack.title }}</h2>
              <p>{{ selectedPack.items.length }} fragments</p>
            </div>
            <button class="button primary" type="button" @click="exportPack(selectedPack.id)">
              <Download :size="16" aria-hidden="true" />
              Export
            </button>
          </header>
          <label>
            Pack name
            <input v-model="editingTitle" />
          </label>
          <div class="action-row">
            <button class="button primary" type="button" :disabled="!canSaveTitle" @click="saveTitle">
              <Save :size="16" aria-hidden="true" />
              Save Name
            </button>
          </div>
          <section>
            <h3>Objective</h3>
            <p>{{ selectedPack.objective }}</p>
          </section>
          <section>
            <h3>Task For AI</h3>
            <p>{{ selectedPack.task_prompt || "No task prompt stored." }}</p>
          </section>
          <section>
            <h3>Items</h3>
            <ol class="context-pack-item-list">
              <li v-for="item in orderedItems(selectedPack)" :key="item.fragment_id">
                <code>{{ item.fragment_id }}</code>
                <span>{{ item.reason || "No reason stored." }}</span>
              </li>
            </ol>
          </section>
        </section>
        <section v-else class="muted-panel plain-section">
          <p>Select a pack to inspect it.</p>
        </section>
        <ContextPackPreview :markdown="exportedMarkdown" />
      </section>
    </div>

    <section v-if="packToDelete" class="modal-backdrop" @click.self="packToDelete = null">
      <div class="modal-panel danger-panel">
        <header class="section-header">
          <h2>Delete Context Pack</h2>
          <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="packToDelete = null">
            <X :size="16" aria-hidden="true" />
          </button>
        </header>
        <p>
          Delete {{ packToDelete.title }}? This removes the saved pack and its vault Markdown export.
        </p>
        <div class="action-row">
          <button class="button subtle" type="button" @click="packToDelete = null">Cancel</button>
          <button class="button danger" type="button" @click="deletePack">
            <Trash2 :size="16" aria-hidden="true" />
            Delete
          </button>
        </div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { Download, Network, RefreshCw, Save, Trash2, X } from "lucide-vue-next";
import ContextPackPreview from "../components/ContextPackPreview.vue";
import { api } from "../api/client";
import type { ContextPack } from "../types";

const packs = ref<ContextPack[]>([]);
const selectedPackId = ref("");
const exportedMarkdown = ref("");
const message = ref("");
const error = ref("");
const packToDelete = ref<ContextPack | null>(null);
const editingTitle = ref("");
const selectedPack = computed(() => packs.value.find((pack) => pack.id === selectedPackId.value) || null);
const canSaveTitle = computed(() => {
  const title = editingTitle.value.trim();
  return !!selectedPack.value && !!title && title !== selectedPack.value.title;
});

async function load() {
  error.value = "";
  packs.value = await api.listContextPacks();
  if (!selectedPackId.value && packs.value[0]) {
    selectedPackId.value = packs.value[0].id;
  }
}

function selectPack(pack: ContextPack) {
  selectedPackId.value = pack.id;
  editingTitle.value = pack.title;
}

function orderedItems(pack: ContextPack) {
  return [...pack.items].sort((left, right) => left.order_index - right.order_index);
}

async function exportPack(id: string) {
  error.value = "";
  message.value = "";
  selectedPackId.value = id;
  try {
    const result = await api.exportContextPack(id);
    exportedMarkdown.value = result.markdown;
    message.value = "Exported context pack.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function saveTitle() {
  if (!selectedPack.value || !editingTitle.value.trim()) return;
  error.value = "";
  message.value = "";
  try {
    const updated = await api.updateContextPack(selectedPack.value.id, {
      title: editingTitle.value.trim(),
    });
    packs.value = packs.value.map((pack) => (pack.id === updated.id ? updated : pack));
    editingTitle.value = updated.title;
    message.value = "Context pack renamed.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function askDelete(pack: ContextPack) {
  packToDelete.value = pack;
}

async function deletePack() {
  if (!packToDelete.value) return;
  error.value = "";
  message.value = "";
  try {
    const deletedId = packToDelete.value.id;
    await api.deleteContextPack(deletedId);
    packs.value = packs.value.filter((pack) => pack.id !== deletedId);
    if (selectedPackId.value === deletedId) {
      selectedPackId.value = packs.value[0]?.id || "";
      exportedMarkdown.value = "";
    }
    packToDelete.value = null;
    message.value = "Deleted context pack.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

onMounted(load);
watch(selectedPack, (pack) => {
  editingTitle.value = pack?.title || "";
});
</script>
