<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Context Pack Builder</h1>
        <p>Select, order, annotate, and export Markdown context</p>
      </div>
      <button class="button primary" type="button" @click="createPack">
        <PackagePlus :size="16" aria-hidden="true" />
        Create
      </button>
    </header>

    <div class="split">
      <section class="plain-section editor">
        <label>
          Title
          <input v-model="title" />
        </label>
        <label>
          Objective
          <textarea v-model="objective" rows="5" />
        </label>
        <label>
          Search fragments
          <input v-model="search" @input="loadFragments" />
        </label>
        <section class="plain-section">
          <h2>Available Fragments</h2>
          <div class="select-list">
            <label v-for="fragment in availableFragments" :key="fragment.id" class="check-row">
              <input :checked="isSelected(fragment.id)" type="checkbox" @change="toggle(fragment.id)" />
              <span>{{ fragment.title }}</span>
              <small>{{ fragment.type }} / {{ fragment.status }}</small>
            </label>
          </div>
        </section>
        <section class="plain-section">
          <h2>Selected Order</h2>
          <article v-for="(item, index) in selectedItems" :key="item.fragment_id" class="edit-card">
            <strong>{{ titleFor(item.fragment_id) }}</strong>
            <label>
              Reason
              <input v-model="item.reason" />
            </label>
            <footer class="action-row">
              <button class="button subtle" type="button" @click="move(index, -1)">Up</button>
              <button class="button subtle" type="button" @click="move(index, 1)">Down</button>
              <button class="button subtle" type="button" @click="toggle(item.fragment_id)">Remove</button>
            </footer>
          </article>
        </section>
        <p v-if="message" class="success-text">{{ message }}</p>
        <p v-if="error" class="error-text">{{ error }}</p>
      </section>

      <section class="plain-section">
        <header class="section-header">
          <h2>Existing Packs</h2>
          <button v-if="packs.length" class="button subtle" type="button" @click="exportFirst">
            <Download :size="16" aria-hidden="true" />
            Export Latest
          </button>
        </header>
        <ul class="compact-list">
          <li v-for="pack in packs" :key="pack.id">
            <button class="text-button" type="button" @click="exportPack(pack.id)">
              {{ pack.title }}
            </button>
            <span>{{ pack.items.length }} items</span>
          </li>
        </ul>
        <ContextPackPreview :markdown="exportedMarkdown" />
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Download, PackagePlus } from "lucide-vue-next";
import ContextPackPreview from "../components/ContextPackPreview.vue";
import { api } from "../api/client";
import { useFragmentsStore } from "../stores/fragments";
import type { ContextPack, ContextPackItemInput } from "../types";
import { acceptedFragmentStatuses } from "../types";

const fragments = useFragmentsStore();
const packs = ref<ContextPack[]>([]);
const selectedItems = ref<ContextPackItemInput[]>([]);
const search = ref("");
const title = ref("Working context pack");
const objective = ref("State the current mathematical objective here.");
const exportedMarkdown = ref("");
const message = ref("");
const error = ref("");
const availableFragments = computed(() =>
  fragments.fragments.filter((fragment) => acceptedFragmentStatuses.includes(fragment.status))
);

async function load() {
  await loadFragments();
  packs.value = await api.listContextPacks();
}

async function loadFragments() {
  await fragments.load({ search: search.value });
}

function isSelected(fragmentId: string) {
  return selectedItems.value.some((item) => item.fragment_id === fragmentId);
}

function toggle(fragmentId: string) {
  const index = selectedItems.value.findIndex((item) => item.fragment_id === fragmentId);
  if (index >= 0) {
    selectedItems.value.splice(index, 1);
  } else {
    selectedItems.value.push({
      fragment_id: fragmentId,
      order_index: selectedItems.value.length,
      reason: "Selected for current objective."
    });
  }
  normalizeOrder();
}

function move(index: number, delta: number) {
  const target = index + delta;
  if (target < 0 || target >= selectedItems.value.length) return;
  const [item] = selectedItems.value.splice(index, 1);
  selectedItems.value.splice(target, 0, item);
  normalizeOrder();
}

function normalizeOrder() {
  selectedItems.value.forEach((item, index) => {
    item.order_index = index;
  });
}

function titleFor(fragmentId: string) {
  return fragments.fragments.find((fragment) => fragment.id === fragmentId)?.title || fragmentId;
}

async function createPack() {
  error.value = "";
  message.value = "";
  try {
    const pack = await api.createContextPack({
      title: title.value,
      objective: objective.value,
      items: selectedItems.value
    });
    packs.value = [pack, ...packs.value];
    message.value = `Created ${pack.title}.`;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function exportPack(id: string) {
  error.value = "";
  try {
    const result = await api.exportContextPack(id);
    exportedMarkdown.value = result.markdown;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function exportFirst() {
  if (packs.value[0]) void exportPack(packs.value[0].id);
}

onMounted(load);
</script>
