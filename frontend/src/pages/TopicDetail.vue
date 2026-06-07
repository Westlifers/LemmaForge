<template>
  <section class="page topic-map-page">
    <header class="page-header topic-workspace-header">
      <div>
        <RouterLink class="back-link" to="/topics">
          <ArrowLeft :size="16" aria-hidden="true" />
          Topics
        </RouterLink>
        <h1>{{ graph?.topic.title || "Topic" }}</h1>
        <p v-if="graph">
          {{ graph.fragments.length }} fragments / {{ graph.relations.length }} relations /
          {{ topicContextPacks.length }} packs
        </p>
      </div>
      <div class="toolbar">
        <button class="button subtle" type="button" @click="load">
          <RefreshCw :size="16" aria-hidden="true" />
          Refresh
        </button>
        <button class="button subtle" type="button" :disabled="!graph?.fragments.length" @click="autoArrangeGraph">
          <Network :size="16" aria-hidden="true" />
          Auto Arrange
        </button>
        <button class="button subtle" type="button" @click="addDrawerOpen = true">
          <FolderPlus :size="16" aria-hidden="true" />
          Add Fragments
        </button>
        <RouterLink class="button subtle" to="/fragments">
          <List :size="16" aria-hidden="true" />
          All Fragments
        </RouterLink>
      </div>
    </header>

    <p v-if="error" class="error-text">{{ error }}</p>
    <p v-if="message" class="success-text">{{ message }}</p>

    <nav class="tabs topic-workspace-tabs" aria-label="Topic workspace tabs">
      <button
        v-for="tab in workspaceTabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeTab === tab.id }"
        @click="changeTab(tab.id)"
      >
        <component :is="tab.icon" :size="16" aria-hidden="true" />
        {{ tab.label }}
      </button>
    </nav>

    <Transition name="tab-fade" mode="out-in">
      <section v-if="activeTab === 'graph'" key="graph" class="topic-workspace-panel">
        <section class="topic-graph-panel topic-graph-panel--workspace">
          <div class="topic-graph-toolbar">
            <div>
              <span class="panel-icon">
                <Network :size="16" aria-hidden="true" />
              </span>
              <div>
                <strong>Topic Graph</strong>
                <small>Drag nodes, connect handles, click to inspect, double-click to open detail.</small>
              </div>
            </div>
            <div class="topic-graph-legend">
              <span class="chip" data-chip="topic">{{ graph?.fragments.length || 0 }} nodes</span>
              <span class="chip" data-chip="exactness">{{ graph?.relations.length || 0 }} relations</span>
              <span v-if="selectedContextItems.length" class="chip" data-chip="ai">
                {{ selectedContextItems.length }} in context
              </span>
            </div>
          </div>
          <VueFlow
            v-model:nodes="nodes"
            v-model:edges="edges"
            class="topic-flow topic-flow--workspace"
            :fit-view-on-init="true"
            :default-edge-options="{ updatable: true, type: 'smoothstep' }"
            @connect="createGraphRelation"
            @edge-click="selectEdge"
            @edge-update="reconnectEdge"
            @node-click="selectNode"
            @node-double-click="openFragment"
            @node-drag-stop="saveLayout"
          />
        </section>
      </section>

      <section v-else-if="activeTab === 'fragments'" key="fragments" class="topic-workspace-panel">
        <section class="plain-section topic-fragments-workspace">
          <header class="section-header">
            <div>
              <span class="eyebrow">Topic fragments</span>
              <h2>Manage This Topic</h2>
              <p>{{ filteredTopicFragments.length }} shown / {{ topicFragments.length }} attached</p>
            </div>
            <button class="button primary" type="button" @click="addDrawerOpen = true">
              <FolderPlus :size="16" aria-hidden="true" />
              Add Fragments
            </button>
          </header>

          <section class="topic-fragment-filters">
            <label class="filter-field filter-field--search">
              <span class="label-title">
                <Search :size="14" aria-hidden="true" />
                Search
              </span>
              <input v-model="topicFragmentSearch" placeholder="Title or body..." />
            </label>
            <label class="filter-field">
              <span class="label-title">Status</span>
              <select v-model="topicFragmentStatus">
                <option value="">Any</option>
                <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </label>
            <label class="filter-field">
              <span class="label-title">Type</span>
              <select v-model="topicFragmentType">
                <option value="">Any</option>
                <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
              </select>
            </label>
            <label class="filter-field">
              <span class="label-title">Origin</span>
              <select v-model="topicFragmentOrigin">
                <option value="">Any</option>
                <option value="user_original">user_original</option>
                <option value="assistant_generated">assistant_generated</option>
                <option value="external_source">external_source</option>
                <option value="mixed">mixed</option>
                <option value="unknown">unknown</option>
              </select>
            </label>
          </section>

          <section class="topic-bulk-toolbar">
            <button class="button subtle" type="button" :disabled="!filteredTopicFragments.length" @click="toggleAllTopicFragments">
              <CheckSquare v-if="allFilteredTopicFragmentsSelected" :size="16" aria-hidden="true" />
              <Square v-else :size="16" aria-hidden="true" />
              {{ allFilteredTopicFragmentsSelected ? "Clear Selection" : "Select Shown" }}
            </button>
            <label>
              Set status
              <select v-model="bulkStatusTarget" :disabled="!selectedTopicFragmentIds.length || bulkBusy">
                <option value="">Choose...</option>
                <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </label>
            <button class="button subtle" type="button" :disabled="!bulkStatusTarget || !selectedTopicFragmentIds.length || bulkBusy" @click="applyBulkStatus">
              <Save :size="16" aria-hidden="true" />
              Apply
            </button>
            <button class="button subtle" type="button" :disabled="!selectedTopicFragmentIds.length || bulkBusy" @click="removeSelectedFromTopic">
              <Unlink :size="16" aria-hidden="true" />
              Remove From Topic
            </button>
            <button class="button danger" type="button" :disabled="!selectedTopicFragmentIds.length || bulkBusy" @click="deleteTopicFragmentsConfirmOpen = true">
              <Trash2 :size="16" aria-hidden="true" />
              Delete
            </button>
            <span class="muted">{{ selectedTopicFragmentIds.length }} selected</span>
          </section>

          <section class="topic-fragment-card-grid">
            <article
              v-for="fragment in filteredTopicFragments"
              :key="fragment.id"
              class="topic-workspace-fragment-card"
              :class="{ selected: selectedTopicFragmentSet.has(fragment.id), rejected: fragment.status === 'rejected' }"
            >
              <button class="topic-select-button" type="button" :aria-label="`Select ${fragment.title}`" @click="toggleTopicFragmentSelection(fragment.id)">
                <CheckSquare v-if="selectedTopicFragmentSet.has(fragment.id)" :size="17" aria-hidden="true" />
                <Square v-else :size="17" aria-hidden="true" />
              </button>
              <div>
                <header>
                  <strong>{{ fragment.title }}</strong>
                  <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
                </header>
                <p class="topic-card-meta">{{ fragment.type }} / {{ fragment.origin_classification }} / {{ fragment.exactness }}</p>
                <div class="card-tex-preview">
                  <MarkdownLatexRenderer :body="fragment.body" />
                </div>
              </div>
              <footer class="action-row">
                <button class="button subtle" type="button" @click="inspectFragment(fragment.id)">
                  <PanelRightOpen :size="16" aria-hidden="true" />
                  Inspect
                </button>
                <RouterLink class="button subtle" :to="fragmentDetailLocation(fragment.id)">Open</RouterLink>
              </footer>
            </article>
            <p v-if="!filteredTopicFragments.length" class="empty-state">No fragments match these filters.</p>
          </section>
        </section>
      </section>

      <section v-else-if="activeTab === 'context'" key="context" class="topic-workspace-panel">
        <div class="topic-context-workspace">
          <section class="plain-section context-drawer-controls">
            <header class="section-header">
              <div>
                <span class="eyebrow">Prompt builder</span>
                <h2>AI Context Pack</h2>
                <p>AI suggests selection and order; exported prompt keeps fragment text unchanged.</p>
              </div>
            </header>
            <label>
              Title
              <input v-model="contextTitle" />
            </label>
            <label>
              Objective
              <textarea v-model="contextObjective" rows="4" />
            </label>
            <label>
              Task For AI
              <textarea v-model="contextTaskPrompt" rows="4" />
            </label>
            <div class="context-action-row">
              <button class="button primary" type="button" :disabled="contextSuggesting || !contextObjective || !contextTaskPrompt" @click="suggestContextPack">
                <Brain :size="16" aria-hidden="true" />
                {{ contextSuggesting ? "Suggesting..." : "Suggest Pack" }}
              </button>
              <button class="button subtle" type="button" :disabled="!contextCandidateFragments.length" @click="selectAllContextCandidates">
                Select All
              </button>
              <button class="button danger" type="button" :disabled="!hasContextSuggestionState" @click="discardContextSuggestion">
                <RotateCcw :size="16" aria-hidden="true" />
                Discard
              </button>
            </div>
            <p v-if="contextError" class="error-text">{{ contextError }}</p>
            <section v-if="contextWarnings.length || missingContextQuestions.length" class="warning-list">
              <p v-for="warning in contextWarnings" :key="`warning-${warning}`">{{ warning }}</p>
              <p v-for="question in missingContextQuestions" :key="`missing-${question}`">Missing context: {{ question }}</p>
            </section>
            <label>
              Add fragment
              <input v-model="contextCandidateSearch" placeholder="Search topic fragments..." />
            </label>
            <section class="context-candidate-list">
              <button
                v-for="fragment in filteredContextCandidates"
                :key="fragment.id"
                class="context-candidate-row"
                :class="{ selected: selectedContextIds.has(fragment.id), rejected: fragment.status === 'rejected' }"
                type="button"
                @click="toggleContextFragment(fragment.id)"
              >
                <span>{{ fragment.title }}</span>
                <small>{{ fragment.type }} / {{ fragment.status }}</small>
              </button>
            </section>
          </section>

          <section class="plain-section context-order-panel">
            <header class="section-header">
              <div>
                <h2>Prompt Order</h2>
                <p>{{ selectedContextItems.length }} selected in dependency order</p>
              </div>
            </header>
            <section class="context-selection-list">
              <article v-for="(item, index) in selectedContextItems" :key="item.fragment_id" class="context-selection-item">
                <span class="order-badge">{{ index + 1 }}</span>
                <div>
                  <strong>{{ fragmentTitle(item.fragment_id) }}</strong>
                  <small>{{ fragmentMeta(item.fragment_id) }}</small>
                </div>
                <label>
                  Reason
                  <input v-model="item.reason" />
                </label>
                <footer class="action-row">
                  <button class="button subtle" type="button" @click="moveContextItem(index, -1)">Up</button>
                  <button class="button subtle" type="button" @click="moveContextItem(index, 1)">Down</button>
                  <button class="button subtle" type="button" @click="toggleContextFragment(item.fragment_id)">Remove</button>
                </footer>
              </article>
              <p v-if="!selectedContextItems.length" class="muted">
                Select fragments manually or ask Codex for a suggestion.
              </p>
            </section>
            <div class="action-row">
              <button class="button primary" type="button" :disabled="!selectedContextItems.length || contextSaving" @click="saveContextPack">
                <PackagePlus :size="16" aria-hidden="true" />
                {{ contextSaving ? "Saving..." : "Save And Export" }}
              </button>
            </div>
          </section>

          <section class="plain-section context-preview-panel">
            <ContextPackPreview :markdown="contextExportedMarkdown" />
          </section>
        </div>
      </section>

      <section v-else key="history" class="topic-workspace-panel">
        <section class="plain-section topic-pack-history">
          <header class="section-header">
            <div>
              <span class="eyebrow">Context history</span>
              <h2>Topic Packs</h2>
              <p>{{ topicContextPacks.length }} saved prompt pack{{ topicContextPacks.length === 1 ? "" : "s" }}</p>
            </div>
          </header>
          <section class="topic-pack-list">
            <article v-for="pack in topicContextPacks" :key="pack.id" class="topic-pack-card">
              <header>
                <div>
                  <input
                    v-if="packEditingId === pack.id"
                    v-model="packTitleDraft"
                    aria-label="Context pack title"
                  />
                  <h3 v-else>{{ pack.title }}</h3>
                  <small>{{ pack.items.length }} items / {{ formatDate(pack.updated_at) }}</small>
                </div>
                <span class="chip" data-chip="topic">{{ pack.topic_id || "No topic" }}</span>
              </header>
              <p>{{ pack.objective }}</p>
              <footer class="action-row">
                <button v-if="packEditingId === pack.id" class="button primary" type="button" @click="savePackTitle(pack)">
                  <Save :size="16" aria-hidden="true" />
                  Save
                </button>
                <button v-if="packEditingId === pack.id" class="button subtle" type="button" @click="cancelPackRename">
                  <X :size="16" aria-hidden="true" />
                  Cancel
                </button>
                <button v-else class="button subtle" type="button" @click="startPackRename(pack)">
                  <Pencil :size="16" aria-hidden="true" />
                  Rename
                </button>
                <button class="button subtle" type="button" @click="exportContextPack(pack.id)">
                  <Download :size="16" aria-hidden="true" />
                  Export
                </button>
                <button class="button danger" type="button" @click="packToDelete = pack">
                  <Trash2 :size="16" aria-hidden="true" />
                  Delete
                </button>
              </footer>
            </article>
            <p v-if="!topicContextPacks.length" class="empty-state">No context packs saved for this topic yet.</p>
          </section>
          <ContextPackPreview :markdown="contextExportedMarkdown" />
        </section>
      </section>
    </Transition>

    <Transition name="drawer-fade">
      <div v-if="inspectorOpen" class="context-drawer-scrim" @click.self="closeInspector">
        <section class="context-drawer topic-inspector-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">{{ selectedFragment ? "Fragment inspector" : "Relation inspector" }}</span>
              <h2>{{ selectedFragment?.title || "Relation" }}</h2>
              <p v-if="selectedFragment">{{ selectedFragment.type }} / {{ selectedFragment.status }}</p>
              <p v-else-if="selectedRelation">{{ relationTitle(selectedRelation) }}</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close inspector" @click="closeInspector">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>

          <section v-if="selectedFragment" class="topic-inspector-body">
            <span v-if="fragmentDirty" class="dirty-pill">
              <span aria-hidden="true"></span>
              Unsaved changes
            </span>
            <label>
              Title
              <input v-model="fragmentDraft.title" />
            </label>
            <div class="form-grid two">
              <label>
                Type
                <select v-model="fragmentDraft.type">
                  <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
                </select>
              </label>
              <label>
                Status
                <select v-model="fragmentDraft.status">
                  <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
                </select>
              </label>
            </div>
            <div class="field-block">
              <div class="field-block-header">
                <span>Body</span>
                <button class="text-button" type="button" @click="bodyEditing = !bodyEditing">
                  {{ bodyEditing ? "Preview" : "Edit" }}
                </button>
              </div>
              <textarea v-if="bodyEditing" v-model="fragmentDraft.body" rows="12" @blur="bodyEditing = false" />
              <button v-else class="body-preview-button" type="button" @click="bodyEditing = true">
                <MarkdownLatexRenderer :body="fragmentDraft.body" />
              </button>
            </div>
            <div class="action-row">
              <button class="button primary" type="button" :class="{ dirty: fragmentDirty }" @click="saveFragment">
                <Save :size="16" aria-hidden="true" />
                Save
              </button>
              <button class="button subtle" type="button" @click="removeFragmentFromTopic">
                <Unlink :size="16" aria-hidden="true" />
                Remove From Topic
              </button>
              <RouterLink class="button subtle" :to="fragmentDetailLocation(selectedFragment.id)">Open Detail</RouterLink>
            </div>
          </section>

          <section v-else-if="selectedRelation" class="topic-inspector-body">
            <span v-if="relationDirty" class="dirty-pill">
              <span aria-hidden="true"></span>
              Unsaved changes
            </span>
            <p class="muted">{{ relationTitle(selectedRelation) }}</p>
            <label>
              Kind
              <select v-model="relationDraft.relation_kind">
                <option v-for="kind in relationKinds" :key="kind" :value="kind">{{ kind }}</option>
              </select>
            </label>
            <label>
              Confidence
              <input v-model.number="relationDraft.confidence" min="0" max="1" step="0.01" type="number" />
            </label>
            <div class="action-row">
              <button class="button primary" type="button" :class="{ dirty: relationDirty }" @click="saveRelation">
                <Save :size="16" aria-hidden="true" />
                Save
              </button>
              <button class="button danger" type="button" @click="deleteSelectedRelation">
                <Trash2 :size="16" aria-hidden="true" />
                Delete
              </button>
            </div>
          </section>
        </section>
      </div>
    </Transition>

    <Transition name="drawer-fade">
      <div v-if="addDrawerOpen" class="context-drawer-scrim" @click.self="addDrawerOpen = false">
        <section class="context-drawer topic-add-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">Attach fragments</span>
              <h2>Add To Topic</h2>
              <p>{{ selectedAddFragmentIds.length }} selected / {{ filteredAddableFragments.length }} candidates</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close add fragments drawer" @click="addDrawerOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <section class="topic-add-body">
            <label>
              Search candidates
              <input v-model="addSearch" placeholder="Title, body, type..." />
            </label>
            <div class="action-row">
              <button class="button subtle" type="button" :disabled="!filteredAddableFragments.length" @click="toggleAllAddCandidates">
                <CheckSquare v-if="allFilteredAddCandidatesSelected" :size="16" aria-hidden="true" />
                <Square v-else :size="16" aria-hidden="true" />
                {{ allFilteredAddCandidatesSelected ? "Clear Shown" : "Select Shown" }}
              </button>
              <button class="button primary" type="button" :disabled="!selectedAddFragmentIds.length || bulkBusy" @click="addSelectedFragmentsToTopic">
                <FolderPlus :size="16" aria-hidden="true" />
                Add Selected
              </button>
            </div>
            <section class="topic-add-candidate-list">
              <article
                v-for="fragment in filteredAddableFragments"
                :key="fragment.id"
                class="topic-add-candidate"
                :class="{ selected: selectedAddFragmentSet.has(fragment.id), unsorted: !fragment.topic_id }"
              >
                <button class="topic-select-button" type="button" :aria-label="`Select ${fragment.title}`" @click="toggleAddFragmentSelection(fragment.id)">
                  <CheckSquare v-if="selectedAddFragmentSet.has(fragment.id)" :size="17" aria-hidden="true" />
                  <Square v-else :size="17" aria-hidden="true" />
                </button>
                <div>
                  <strong>{{ fragment.title }}</strong>
                  <small>{{ candidateTopicLabel(fragment) }} / {{ fragment.type }} / {{ fragment.status }}</small>
                </div>
                <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
              </article>
              <p v-if="!filteredAddableFragments.length" class="empty-state">No fragments available to add.</p>
            </section>
          </section>
        </section>
      </div>
    </Transition>

    <Transition name="modal-fade">
      <section v-if="deleteTopicFragmentsConfirmOpen" class="modal-backdrop" @click.self="deleteTopicFragmentsConfirmOpen = false">
        <div class="modal-panel danger-panel">
          <header class="section-header">
            <div>
              <span class="eyebrow">Permanent delete</span>
              <h2>Delete selected fragments?</h2>
              <p>This removes fragments, relations, source pointers, and context-pack links. Rejected is usually safer.</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="deleteTopicFragmentsConfirmOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="action-row">
            <button class="button subtle" type="button" @click="deleteTopicFragmentsConfirmOpen = false">Cancel</button>
            <button class="button danger" type="button" @click="deleteSelectedTopicFragments">
              <Trash2 :size="16" aria-hidden="true" />
              Delete {{ selectedTopicFragmentIds.length }}
            </button>
          </div>
        </div>
      </section>
    </Transition>

    <Transition name="modal-fade">
      <section v-if="packToDelete" class="modal-backdrop" @click.self="packToDelete = null">
        <div class="modal-panel danger-panel">
          <header class="section-header">
            <div>
              <span class="eyebrow">Delete pack</span>
              <h2>{{ packToDelete.title }}</h2>
              <p>This deletes the saved context pack record. It does not delete fragments.</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="packToDelete = null">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="action-row">
            <button class="button subtle" type="button" @click="packToDelete = null">Cancel</button>
            <button class="button danger" type="button" @click="deletePack">
              <Trash2 :size="16" aria-hidden="true" />
              Delete Pack
            </button>
          </div>
        </div>
      </section>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";

import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import {
  ArrowLeft,
  Brain,
  CheckSquare,
  Download,
  FileText,
  FolderPlus,
  History,
  Layers,
  List,
  Network,
  PackagePlus,
  PanelRightOpen,
  Pencil,
  RefreshCw,
  RotateCcw,
  Route,
  Save,
  Search,
  Square,
  Trash2,
  Unlink,
  X,
} from "lucide-vue-next";
import {
  MarkerType,
  Position,
  VueFlow,
  type Connection,
  type EdgeMouseEvent,
  type EdgeUpdateEvent,
  type NodeDragEvent,
  type NodeMouseEvent,
} from "@vue-flow/core";
import { api } from "../api/client";
import ContextPackPreview from "../components/ContextPackPreview.vue";
import MarkdownLatexRenderer from "../components/MarkdownLatexRenderer.vue";
import { useAILogsStore } from "../stores/aiLogs";
import { useSettingsStore } from "../stores/settings";
import type {
  ContextPack,
  ContextPackItemInput,
  ContextPackSuggestJob,
  ContextPackSuggestResult,
  Fragment,
  FragmentStatus,
  FragmentType,
  Relation,
  TopicGraph,
} from "../types";
import { fragmentStatuses, fragmentTypes } from "../types";

type WorkspaceTab = "graph" | "fragments" | "context" | "history";

const props = defineProps<{ id: string }>();
const router = useRouter();
const aiLogs = useAILogsStore();
const settings = useSettingsStore();
const graph = ref<TopicGraph | null>(null);
const allFragments = ref<Fragment[]>([]);
const nodes = ref<any[]>([]);
const edges = ref<any[]>([]);
const activeTab = ref<WorkspaceTab>("graph");
const selectedFragmentId = ref("");
const selectedRelationId = ref("");
const error = ref("");
const message = ref("");
const bodyEditing = ref(false);
const addDrawerOpen = ref(false);
const bulkBusy = ref(false);
const topicFragmentSearch = ref("");
const topicFragmentStatus = ref("");
const topicFragmentType = ref("");
const topicFragmentOrigin = ref("");
const selectedTopicFragmentIds = ref<string[]>([]);
const bulkStatusTarget = ref("");
const deleteTopicFragmentsConfirmOpen = ref(false);
const addSearch = ref("");
const selectedAddFragmentIds = ref<string[]>([]);
const contextSuggesting = ref(false);
const contextSaving = ref(false);
const contextTitle = ref("AI context pack");
const contextObjective = ref("State the current mathematical objective here.");
const contextTaskPrompt = ref("Help me reason about this objective. Identify useful dependencies, gaps, and next steps.");
const contextCandidateSearch = ref("");
const selectedContextItems = ref<ContextPackItemInput[]>([]);
const contextWarnings = ref<string[]>([]);
const missingContextQuestions = ref<string[]>([]);
const contextLogs = ref<string[]>([]);
const contextError = ref("");
const contextExportedMarkdown = ref("");
const topicContextPacks = ref<ContextPack[]>([]);
const currentContextJob = ref<ContextPackSuggestJob | null>(null);
const appliedContextJobId = ref("");
const packEditingId = ref("");
const packTitleDraft = ref("");
const packToDelete = ref<ContextPack | null>(null);
let contextPollTimer: number | undefined;

const workspaceTabs = [
  { id: "graph" as const, label: "Graph", icon: Network },
  { id: "fragments" as const, label: "Fragments", icon: Layers },
  { id: "context" as const, label: "Context", icon: Brain },
  { id: "history" as const, label: "History", icon: History },
];

const fragmentDraft = reactive({
  title: "",
  type: "ContextNote" as FragmentType,
  status: "working" as FragmentStatus,
  body: "",
});
const relationDraft = reactive({
  relation_kind: "depends_on",
  confidence: null as number | null,
});
const relationKinds = [
  "depends_on",
  "uses",
  "proves",
  "proof_of",
  "refines",
  "replaces",
  "contradicts",
  "generalizes",
  "specializes_to",
  "is_example_of",
  "is_counterexample_to",
  "cites",
  "quotes",
  "paraphrases",
  "restates",
  "adopts_notation_from",
  "depends_on_notation",
  "inspired_by",
  "generalizes_external_result",
  "specializes_external_result",
  "questions_external_claim",
  "compares_with",
  "came_from",
];

const selectedFragment = computed(() =>
  graph.value?.fragments.find((fragment) => fragment.id === selectedFragmentId.value) || null
);
const selectedRelation = computed(() =>
  graph.value?.relations.find((relation) => relation.id === selectedRelationId.value) || null
);
const inspectorOpen = computed(() => activeTab.value === "graph" && (!!selectedFragment.value || !!selectedRelation.value));
const fragmentDirty = computed(() => {
  if (!selectedFragment.value) return false;
  return (
    fragmentDraft.title !== selectedFragment.value.title ||
    fragmentDraft.type !== selectedFragment.value.type ||
    fragmentDraft.status !== selectedFragment.value.status ||
    fragmentDraft.body !== selectedFragment.value.body
  );
});
const relationDirty = computed(() => {
  if (!selectedRelation.value) return false;
  return (
    relationDraft.relation_kind !== selectedRelation.value.relation_kind ||
    relationDraft.confidence !== selectedRelation.value.confidence
  );
});
const hasUnsavedChanges = computed(() => fragmentDirty.value || relationDirty.value);
const topicFragments = computed(() => graph.value?.fragments || []);
const topicFragmentSet = computed(() => new Set(topicFragments.value.map((fragment) => fragment.id)));
const selectedTopicFragmentSet = computed(() => new Set(selectedTopicFragmentIds.value));
const addableFragments = computed(() =>
  allFragments.value
    .filter((fragment) => !topicFragmentSet.value.has(fragment.id))
    .sort((left, right) => Number(Boolean(left.topic_id)) - Number(Boolean(right.topic_id)) || left.title.localeCompare(right.title))
);
const selectedAddFragmentSet = computed(() => new Set(selectedAddFragmentIds.value));
const filteredTopicFragments = computed(() => {
  const query = topicFragmentSearch.value.trim().toLowerCase();
  return topicFragments.value.filter((fragment) => {
    const matchesSearch =
      !query ||
      fragment.title.toLowerCase().includes(query) ||
      fragment.body.toLowerCase().includes(query);
    const matchesStatus = !topicFragmentStatus.value || fragment.status === topicFragmentStatus.value;
    const matchesType = !topicFragmentType.value || fragment.type === topicFragmentType.value;
    const matchesOrigin = !topicFragmentOrigin.value || fragment.origin_classification === topicFragmentOrigin.value;
    return matchesSearch && matchesStatus && matchesType && matchesOrigin;
  });
});
const allFilteredTopicFragmentsSelected = computed(
  () =>
    !!filteredTopicFragments.value.length &&
    filteredTopicFragments.value.every((fragment) => selectedTopicFragmentSet.value.has(fragment.id))
);
const filteredAddableFragments = computed(() => {
  const query = addSearch.value.trim().toLowerCase();
  return addableFragments.value.filter(
    (fragment) =>
      !query ||
      fragment.title.toLowerCase().includes(query) ||
      fragment.body.toLowerCase().includes(query) ||
      fragment.type.toLowerCase().includes(query)
  );
});
const allFilteredAddCandidatesSelected = computed(
  () =>
    !!filteredAddableFragments.value.length &&
    filteredAddableFragments.value.every((fragment) => selectedAddFragmentSet.value.has(fragment.id))
);
const contextCandidateFragments = computed(() =>
  topicFragments.value.filter((fragment) => fragment.status !== "rejected")
);
const selectedContextIds = computed(() => new Set(selectedContextItems.value.map((item) => item.fragment_id)));
const filteredContextCandidates = computed(() => {
  const query = contextCandidateSearch.value.trim().toLowerCase();
  return contextCandidateFragments.value.filter(
    (fragment) =>
      !query ||
      fragment.title.toLowerCase().includes(query) ||
      fragment.body.toLowerCase().includes(query) ||
      fragment.type.toLowerCase().includes(query)
  );
});
const hasContextSuggestionState = computed(
  () =>
    !!selectedContextItems.value.length ||
    !!contextWarnings.value.length ||
    !!missingContextQuestions.value.length ||
    !!contextLogs.value.length ||
    !!contextExportedMarkdown.value ||
    !!currentContextJob.value
);

async function load() {
  if (!confirmDiscardChanges()) return;
  error.value = "";
  message.value = "";
  try {
    graph.value = await api.getTopicGraph(props.id);
    allFragments.value = await api.listFragments();
    topicContextPacks.value = await api.listTopicContextPacks(props.id);
    if (graph.value && contextTitle.value === "AI context pack") {
      contextTitle.value = `${graph.value.topic.title} AI context`;
    }
    pruneLocalSelections();
    syncFlowElements();
    syncDrafts();
    restoreContextSuggestionFromGlobalRun();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function changeTab(tab: WorkspaceTab) {
  if (tab !== activeTab.value && !confirmDiscardChanges()) return;
  activeTab.value = tab;
  bodyEditing.value = false;
  if (tab !== "graph") {
    selectedFragmentId.value = "";
    selectedRelationId.value = "";
  }
  syncFlowElements();
}

function syncFlowElements() {
  if (!graph.value) {
    nodes.value = [];
    edges.value = [];
    return;
  }
  const positionsById = fragmentPositions();
  nodes.value = graph.value.fragments.map((fragment, index) => {
    const position = positionsById[fragment.id] || defaultPosition(index);
    const handles = handlePositionsFor(fragment.id, positionsById);
    return {
      id: fragment.id,
      label: fragment.title,
      position: { x: position.x, y: position.y },
      sourcePosition: handles.source,
      targetPosition: handles.target,
      class: [
        "topic-fragment-node",
        selectedFragmentId.value === fragment.id ? "selected" : "",
        fragmentDirty.value && selectedFragmentId.value === fragment.id ? "dirty" : "",
        selectedContextIds.value.has(fragment.id) ? "context-selected" : "",
        fragment.origin_classification === "assistant_generated" || fragment.origin_classification === "mixed"
          ? "ai"
          : "",
      ].filter(Boolean).join(" "),
      data: fragment,
    };
  });
  edges.value = graph.value.relations.map((relation) => ({
    id: relation.id,
    source: relation.source_fragment_id,
    target: relation.target_fragment_id,
    label: relation.relation_kind,
    type: "smoothstep",
    updatable: true,
    markerEnd: MarkerType.ArrowClosed,
    class: [
      selectedRelationId.value === relation.id ? "selected" : "",
      relationDirty.value && selectedRelationId.value === relation.id ? "dirty" : "",
    ].filter(Boolean).join(" "),
    data: relation,
  }));
}

function fragmentPositions() {
  const positions: Record<string, { x: number; y: number }> = {};
  if (!graph.value) return positions;
  graph.value.fragments.forEach((fragment, index) => {
    const saved = graph.value?.positions[fragment.id];
    positions[fragment.id] = saved ? { x: saved.x, y: saved.y } : defaultPosition(index);
  });
  nodes.value.forEach((node) => {
    if (node.id && node.position) {
      positions[node.id] = { x: node.position.x, y: node.position.y };
    }
  });
  return positions;
}

function handlePositionsFor(fragmentId: string, positions: Record<string, { x: number; y: number }>) {
  const origin = positions[fragmentId];
  if (!graph.value || !origin) {
    return { source: Position.Right, target: Position.Left };
  }
  const outgoingTargets = graph.value.relations
    .filter((relation) => relation.source_fragment_id === fragmentId)
    .map((relation) => positions[relation.target_fragment_id])
    .filter(Boolean);
  const incomingSources = graph.value.relations
    .filter((relation) => relation.target_fragment_id === fragmentId)
    .map((relation) => positions[relation.source_fragment_id])
    .filter(Boolean);
  return {
    source: averageDirectionPosition(origin, outgoingTargets, Position.Right),
    target: averageDirectionPosition(origin, incomingSources, Position.Left),
  };
}

function averageDirectionPosition(
  origin: { x: number; y: number },
  points: Array<{ x: number; y: number }>,
  fallback: Position
) {
  if (!points.length) return fallback;
  const delta = points.reduce(
    (sum, point) => ({
      x: sum.x + point.x - origin.x,
      y: sum.y + point.y - origin.y,
    }),
    { x: 0, y: 0 }
  );
  if (Math.abs(delta.x) >= Math.abs(delta.y)) {
    return delta.x >= 0 ? Position.Right : Position.Left;
  }
  return delta.y >= 0 ? Position.Bottom : Position.Top;
}

function defaultPosition(index: number) {
  const column = index % 3;
  const row = Math.floor(index / 3);
  return {
    x: column * 260,
    y: row * 160,
  };
}

function selectNode(event: NodeMouseEvent) {
  if (event.node.id !== selectedFragmentId.value || selectedRelationId.value) {
    if (!confirmDiscardChanges()) return;
  }
  selectedFragmentId.value = event.node.id;
  selectedRelationId.value = "";
  bodyEditing.value = false;
  syncDrafts();
  syncFlowElements();
}

function selectEdge(event: EdgeMouseEvent) {
  if (event.edge.id !== selectedRelationId.value || selectedFragmentId.value) {
    if (!confirmDiscardChanges()) return;
  }
  selectedRelationId.value = event.edge.id;
  selectedFragmentId.value = "";
  bodyEditing.value = false;
  syncDrafts();
  syncFlowElements();
}

function inspectFragment(fragmentId: string) {
  if (!confirmDiscardChanges()) return;
  activeTab.value = "graph";
  selectedFragmentId.value = fragmentId;
  selectedRelationId.value = "";
  bodyEditing.value = false;
  syncDrafts();
  syncFlowElements();
}

function closeInspector() {
  if (!confirmDiscardChanges()) return;
  selectedFragmentId.value = "";
  selectedRelationId.value = "";
  bodyEditing.value = false;
  syncFlowElements();
}

function toggleTopicFragmentSelection(fragmentId: string) {
  const next = new Set(selectedTopicFragmentIds.value);
  if (next.has(fragmentId)) next.delete(fragmentId);
  else next.add(fragmentId);
  selectedTopicFragmentIds.value = [...next];
}

function toggleAllTopicFragments() {
  if (allFilteredTopicFragmentsSelected.value) {
    const filteredIds = new Set(filteredTopicFragments.value.map((fragment) => fragment.id));
    selectedTopicFragmentIds.value = selectedTopicFragmentIds.value.filter((id) => !filteredIds.has(id));
  } else {
    selectedTopicFragmentIds.value = [...new Set([...selectedTopicFragmentIds.value, ...filteredTopicFragments.value.map((fragment) => fragment.id)])];
  }
}

function toggleAddFragmentSelection(fragmentId: string) {
  const next = new Set(selectedAddFragmentIds.value);
  if (next.has(fragmentId)) next.delete(fragmentId);
  else next.add(fragmentId);
  selectedAddFragmentIds.value = [...next];
}

function toggleAllAddCandidates() {
  if (allFilteredAddCandidatesSelected.value) {
    const filteredIds = new Set(filteredAddableFragments.value.map((fragment) => fragment.id));
    selectedAddFragmentIds.value = selectedAddFragmentIds.value.filter((id) => !filteredIds.has(id));
  } else {
    selectedAddFragmentIds.value = [...new Set([...selectedAddFragmentIds.value, ...filteredAddableFragments.value.map((fragment) => fragment.id)])];
  }
}

async function addSelectedFragmentsToTopic() {
  if (!graph.value || !selectedAddFragmentIds.value.length) return;
  bulkBusy.value = true;
  await runGraphChange(async () => {
    await api.bulkUpdateFragments({
      ids: selectedAddFragmentIds.value,
      topic_id: graph.value!.topic.id,
      change_note: `Added to topic ${graph.value!.topic.title}.`,
    });
    selectedAddFragmentIds.value = [];
    addSearch.value = "";
    addDrawerOpen.value = false;
    message.value = "Fragments added to topic.";
  });
  bulkBusy.value = false;
}

async function removeSelectedFromTopic() {
  if (!selectedTopicFragmentIds.value.length || !graph.value) return;
  bulkBusy.value = true;
  await runGraphChange(async () => {
    await api.bulkUpdateFragments({
      ids: selectedTopicFragmentIds.value,
      topic_id: null,
      change_note: `Removed from topic ${graph.value!.topic.title}.`,
    });
    selectedTopicFragmentIds.value = [];
    message.value = "Fragments removed from topic.";
  });
  bulkBusy.value = false;
}

async function applyBulkStatus() {
  if (!selectedTopicFragmentIds.value.length || !bulkStatusTarget.value) return;
  bulkBusy.value = true;
  await runGraphChange(async () => {
    await api.bulkUpdateFragments({
      ids: selectedTopicFragmentIds.value,
      status: bulkStatusTarget.value,
      change_note: `Bulk status update from topic ${graph.value?.topic.title || props.id}.`,
    });
    bulkStatusTarget.value = "";
    message.value = "Fragment statuses updated.";
  });
  bulkBusy.value = false;
}

async function deleteSelectedTopicFragments() {
  if (!selectedTopicFragmentIds.value.length) return;
  bulkBusy.value = true;
  await runGraphChange(async () => {
    await api.bulkDeleteFragments(selectedTopicFragmentIds.value);
    selectedTopicFragmentIds.value = [];
    deleteTopicFragmentsConfirmOpen.value = false;
    message.value = "Fragments deleted.";
  });
  bulkBusy.value = false;
}

function toggleContextFragment(fragmentId: string) {
  const fragment = graph.value?.fragments.find((item) => item.id === fragmentId);
  if (!fragment || fragment.status === "rejected") return;
  const index = selectedContextItems.value.findIndex((item) => item.fragment_id === fragmentId);
  if (index >= 0) {
    selectedContextItems.value.splice(index, 1);
  } else {
    selectedContextItems.value.push({
      fragment_id: fragmentId,
      order_index: selectedContextItems.value.length,
      reason: "Useful for the current AI task.",
    });
  }
  normalizeContextOrder();
  syncFlowElements();
}

function selectAllContextCandidates() {
  selectedContextItems.value = contextCandidateFragments.value.map((fragment, index) => ({
    fragment_id: fragment.id,
    order_index: index,
    reason: "Included from this topic.",
  }));
  syncFlowElements();
}

function discardContextSuggestion() {
  clearContextPollTimer();
  selectedContextItems.value = [];
  contextWarnings.value = [];
  missingContextQuestions.value = [];
  contextLogs.value = [];
  contextError.value = "";
  contextExportedMarkdown.value = "";
  currentContextJob.value = null;
  appliedContextJobId.value = "";
  contextSuggesting.value = false;
  message.value = "Discarded context suggestion.";
  syncFlowElements();
}

function moveContextItem(index: number, delta: number) {
  const target = index + delta;
  if (target < 0 || target >= selectedContextItems.value.length) return;
  const [item] = selectedContextItems.value.splice(index, 1);
  selectedContextItems.value.splice(target, 0, item);
  normalizeContextOrder();
}

function normalizeContextOrder() {
  selectedContextItems.value.forEach((item, index) => {
    item.order_index = index;
  });
}

function fragmentTitle(fragmentId: string) {
  return graph.value?.fragments.find((fragment) => fragment.id === fragmentId)?.title || fragmentId;
}

function fragmentMeta(fragmentId: string) {
  const fragment = graph.value?.fragments.find((item) => item.id === fragmentId);
  return fragment ? `${fragment.type} / ${fragment.status}` : fragmentId;
}

async function suggestContextPack() {
  if (!graph.value) return;
  contextSuggesting.value = true;
  contextError.value = "";
  contextLogs.value = [];
  contextWarnings.value = [];
  missingContextQuestions.value = [];
  try {
    currentContextJob.value = await api.startContextPackSuggestJob({
      topic_id: graph.value.topic.id,
      objective: contextObjective.value,
      task_prompt: contextTaskPrompt.value,
      timeout_seconds: settings.settings.aiTimeoutSeconds,
    });
    contextLogs.value = currentContextJob.value.logs;
    syncGlobalContextLogs(currentContextJob.value, true);
    pollContextSuggestionJob(currentContextJob.value.job_id);
  } catch (caught) {
    contextError.value = caught instanceof Error ? caught.message : String(caught);
    contextSuggesting.value = false;
  }
}

async function pollContextSuggestionJob(jobId: string) {
  clearContextPollTimer();
  try {
    const job = await api.getContextPackSuggestJob(jobId);
    currentContextJob.value = job;
    contextLogs.value = job.logs;
    syncGlobalContextLogs(job);
    if (job.status === "queued" || job.status === "running") {
      contextPollTimer = window.setTimeout(() => pollContextSuggestionJob(jobId), 1000);
      return;
    }
    contextSuggesting.value = false;
    const result = job.result;
    if (!result) {
      contextError.value = job.error || "Codex suggestion finished without a result.";
      return;
    }
    applyContextSuggestionResult(result);
    appliedContextJobId.value = job.job_id;
    message.value = "Context suggestion loaded.";
    syncFlowElements();
  } catch (caught) {
    contextError.value = caught instanceof Error ? caught.message : String(caught);
    contextSuggesting.value = false;
  } finally {
    if (currentContextJob.value?.status !== "queued" && currentContextJob.value?.status !== "running") {
      contextSuggesting.value = false;
    }
  }
}

function clearContextPollTimer() {
  if (contextPollTimer !== undefined) {
    window.clearTimeout(contextPollTimer);
    contextPollTimer = undefined;
  }
}

function syncGlobalContextLogs(job: ContextPackSuggestJob, open = false) {
  aiLogs.upsertRun({
    id: job.job_id,
    kind: "context_suggest",
    label: "AI context suggestion",
    status: job.status,
    logs: job.logs,
    error: job.error,
    result: job.result,
    context: { topic_id: props.id },
    open,
  });
}

function restoreContextSuggestionFromGlobalRun() {
  const run = aiLogs.runs.find(
    (item) =>
      item.kind === "context_suggest" &&
      item.context?.topic_id === props.id &&
      item.status === "succeeded" &&
      item.result &&
      item.id !== appliedContextJobId.value
  );
  if (!run) return;
  const result = run.result as ContextPackSuggestResult;
  if (!result.suggestion) return;
  applyContextSuggestionResult(result);
  contextLogs.value = run.logs;
  activeTab.value = "context";
  contextSuggesting.value = false;
  appliedContextJobId.value = run.id;
  message.value = "Restored completed context suggestion.";
  syncFlowElements();
}

function applyContextSuggestionResult(result: ContextPackSuggestResult) {
  if (!result.available) {
    contextError.value = result.error || "Codex CLI is unavailable. Manual selection is still usable.";
    return;
  }
  if (result.error || !result.suggestion) {
    contextError.value = result.error || "Codex did not return a suggestion.";
    return;
  }
  contextObjective.value = result.suggestion.objective;
  contextTaskPrompt.value = result.suggestion.task_prompt;
  const candidateIds = new Set(contextCandidateFragments.value.map((fragment) => fragment.id));
  selectedContextItems.value = result.suggestion.items
    .filter((item) => candidateIds.has(item.fragment_id))
    .sort((left, right) => left.order_index - right.order_index)
    .map((item, index) => ({
      fragment_id: item.fragment_id,
      order_index: index,
      reason: item.reason,
    }));
  contextWarnings.value = result.suggestion.warnings;
  missingContextQuestions.value = result.suggestion.missing_context_questions;
}

async function saveContextPack() {
  if (!graph.value || !selectedContextItems.value.length) return;
  contextSaving.value = true;
  contextError.value = "";
  try {
    const pack = await api.createContextPack({
      title: contextTitle.value,
      topic_id: graph.value.topic.id,
      objective: contextObjective.value,
      task_prompt: contextTaskPrompt.value,
      items: selectedContextItems.value,
    });
    topicContextPacks.value = [pack, ...topicContextPacks.value.filter((item) => item.id !== pack.id)];
    await exportContextPack(pack.id);
    message.value = `Saved ${pack.title}.`;
  } catch (caught) {
    contextError.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    contextSaving.value = false;
  }
}

async function exportContextPack(packId: string) {
  contextError.value = "";
  try {
    const result = await api.exportContextPack(packId);
    contextExportedMarkdown.value = result.markdown;
  } catch (caught) {
    contextError.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function startPackRename(pack: ContextPack) {
  packEditingId.value = pack.id;
  packTitleDraft.value = pack.title;
}

function cancelPackRename() {
  packEditingId.value = "";
  packTitleDraft.value = "";
}

async function savePackTitle(pack: ContextPack) {
  if (!packTitleDraft.value.trim()) return;
  error.value = "";
  try {
    const updated = await api.updateContextPack(pack.id, { title: packTitleDraft.value.trim() });
    topicContextPacks.value = topicContextPacks.value.map((item) => (item.id === updated.id ? updated : item));
    cancelPackRename();
    message.value = "Context pack renamed.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function deletePack() {
  if (!packToDelete.value) return;
  error.value = "";
  try {
    await api.deleteContextPack(packToDelete.value.id);
    topicContextPacks.value = topicContextPacks.value.filter((pack) => pack.id !== packToDelete.value?.id);
    packToDelete.value = null;
    message.value = "Context pack deleted.";
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function syncDrafts() {
  if (selectedFragment.value) {
    fragmentDraft.title = selectedFragment.value.title;
    fragmentDraft.type = selectedFragment.value.type;
    fragmentDraft.status = selectedFragment.value.status;
    fragmentDraft.body = selectedFragment.value.body;
  }
  if (selectedRelation.value) {
    relationDraft.relation_kind = selectedRelation.value.relation_kind;
    relationDraft.confidence = selectedRelation.value.confidence;
  }
}

async function openFragment(event: NodeMouseEvent) {
  if (!confirmDiscardChanges()) return;
  await router.push(fragmentDetailLocation(event.node.id));
}

function fragmentDetailLocation(fragmentId: string) {
  return {
    path: `/fragments/${fragmentId}`,
    query: { from: `/topics/${props.id}`, from_label: graph.value?.topic.title || "Topic" },
  };
}

async function saveLayout(_event?: NodeDragEvent) {
  if (!graph.value) return;
  await persistPositions();
}

async function autoArrangeGraph() {
  if (!graph.value) return;
  activeTab.value = "graph";
  const arranged = arrangedPositions();
  nodes.value = nodes.value.map((node) => ({
    ...node,
    position: arranged[node.id] || node.position,
  }));
  await persistPositions("Graph auto-arranged.");
}

function arrangedPositions() {
  if (!graph.value) return {};
  const fragments = graph.value.fragments;
  const fragmentIds = new Set(fragments.map((fragment) => fragment.id));
  const outgoing = new Map<string, string[]>();
  const incomingCount = new Map<string, number>();
  fragments.forEach((fragment) => {
    outgoing.set(fragment.id, []);
    incomingCount.set(fragment.id, 0);
  });
  graph.value.relations.forEach((relation) => {
    if (!fragmentIds.has(relation.source_fragment_id) || !fragmentIds.has(relation.target_fragment_id)) return;
    outgoing.get(relation.source_fragment_id)?.push(relation.target_fragment_id);
    incomingCount.set(
      relation.target_fragment_id,
      (incomingCount.get(relation.target_fragment_id) || 0) + 1
    );
  });
  const levels = new Map<string, number>();
  const roots = fragments
    .filter((fragment) => (incomingCount.get(fragment.id) || 0) === 0)
    .map((fragment) => fragment.id);
  const queue = roots.length ? [...roots] : fragments.slice(0, 1).map((fragment) => fragment.id);
  queue.forEach((id) => levels.set(id, 0));
  while (queue.length) {
    const current = queue.shift()!;
    const nextLevel = (levels.get(current) || 0) + 1;
    for (const target of outgoing.get(current) || []) {
      if ((levels.get(target) ?? -1) >= nextLevel) continue;
      levels.set(target, nextLevel);
      queue.push(target);
    }
  }
  fragments.forEach((fragment) => {
    if (!levels.has(fragment.id)) levels.set(fragment.id, 0);
  });
  const groups = new Map<number, Fragment[]>();
  fragments.forEach((fragment) => {
    const level = levels.get(fragment.id) || 0;
    groups.set(level, [...(groups.get(level) || []), fragment]);
  });
  const positions: Record<string, { x: number; y: number }> = {};
  [...groups.entries()].forEach(([level, group]) => {
    group
      .sort((left, right) => left.title.localeCompare(right.title))
      .forEach((fragment, index) => {
        positions[fragment.id] = {
          x: level * 300,
          y: index * 150,
        };
      });
  });
  return positions;
}

async function persistPositions(successMessage = "Layout saved.") {
  const positions: Record<string, { fragment_id: string; x: number; y: number }> = {};
  for (const node of nodes.value) {
    positions[node.id] = {
      fragment_id: node.id,
      x: node.position.x,
      y: node.position.y,
    };
  }
  try {
    graph.value = await api.updateTopicGraphLayout(props.id, positions);
    syncFlowElements();
    message.value = successMessage;
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function createGraphRelation(connection: Connection) {
  if (!connection.source || !connection.target || connection.source === connection.target) return;
  await runGraphChange(async () => {
    await api.createRelation({
      source_fragment_id: connection.source!,
      relation_kind: "depends_on",
      target_fragment_id: connection.target!,
      confidence: null,
    });
    message.value = "Relation created.";
  });
}

async function reconnectEdge(event: EdgeUpdateEvent) {
  if (!event.connection.source || !event.connection.target) return;
  await runGraphChange(async () => {
    await api.updateRelation(event.edge.id, {
      source_fragment_id: event.connection.source,
      target_fragment_id: event.connection.target,
    });
    message.value = "Relation reconnected.";
  });
}

async function saveFragment() {
  if (!selectedFragment.value) return;
  await runGraphChange(async () => {
    await api.updateFragment(selectedFragment.value!.id, {
      title: fragmentDraft.title,
      type: fragmentDraft.type,
      status: fragmentDraft.status,
      body: fragmentDraft.body,
      change_note: "Edited from topic workspace.",
    });
    bodyEditing.value = false;
    message.value = "Fragment saved.";
  });
}

async function removeFragmentFromTopic() {
  if (!selectedFragment.value) return;
  await runGraphChange(async () => {
    await api.updateFragment(selectedFragment.value!.id, {
      topic_id: null,
      change_note: `Removed from topic ${graph.value?.topic.title || props.id}.`,
    });
    selectedFragmentId.value = "";
    message.value = "Fragment removed from topic.";
  });
}

async function saveRelation() {
  if (!selectedRelation.value) return;
  await runGraphChange(async () => {
    await api.updateRelation(selectedRelation.value!.id, {
      relation_kind: relationDraft.relation_kind,
      confidence: relationDraft.confidence,
    });
    message.value = "Relation saved.";
  });
}

async function deleteSelectedRelation() {
  if (!selectedRelation.value) return;
  await runGraphChange(async () => {
    await api.deleteRelation(selectedRelation.value!.id);
    selectedRelationId.value = "";
    message.value = "Relation deleted.";
  });
}

function confirmDiscardChanges() {
  if (!hasUnsavedChanges.value) return true;
  return window.confirm("You have unsaved changes. Discard them and continue?");
}

function warnBeforeUnload(event: BeforeUnloadEvent) {
  if (!hasUnsavedChanges.value) return;
  event.preventDefault();
  event.returnValue = "";
}

async function runGraphChange(operation: () => Promise<void>) {
  error.value = "";
  message.value = "";
  try {
    await operation();
    const selectedFragmentBeforeLoad = selectedFragmentId.value;
    const selectedRelationBeforeLoad = selectedRelationId.value;
    graph.value = await api.getTopicGraph(props.id);
    allFragments.value = await api.listFragments();
    topicContextPacks.value = await api.listTopicContextPacks(props.id);
    selectedFragmentId.value = graph.value.fragments.some((fragment) => fragment.id === selectedFragmentBeforeLoad)
      ? selectedFragmentBeforeLoad
      : "";
    selectedRelationId.value = graph.value.relations.some((relation) => relation.id === selectedRelationBeforeLoad)
      ? selectedRelationBeforeLoad
      : "";
    pruneLocalSelections();
    syncFlowElements();
    syncDrafts();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function pruneLocalSelections() {
  const topicIds = new Set(topicFragments.value.map((fragment) => fragment.id));
  const allIds = new Set(allFragments.value.map((fragment) => fragment.id));
  selectedTopicFragmentIds.value = selectedTopicFragmentIds.value.filter((id) => topicIds.has(id));
  selectedAddFragmentIds.value = selectedAddFragmentIds.value.filter((id) => allIds.has(id) && !topicIds.has(id));
  selectedContextItems.value = selectedContextItems.value.filter((item) => topicIds.has(item.fragment_id));
  normalizeContextOrder();
}

function relationTitle(relation: Relation) {
  const source = graph.value?.fragments.find((fragment) => fragment.id === relation.source_fragment_id);
  const target = graph.value?.fragments.find((fragment) => fragment.id === relation.target_fragment_id);
  return `${source?.title || relation.source_fragment_id} -> ${target?.title || relation.target_fragment_id}`;
}

function candidateTopicLabel(fragment: Fragment) {
  if (!fragment.topic_id) return "Unsorted";
  return `Topic: ${fragment.topic_id}`;
}

function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

onMounted(() => {
  window.addEventListener("beforeunload", warnBeforeUnload);
  void load();
});

watch(
  () => aiLogs.runs.map((run) => `${run.id}:${run.status}:${run.updated_at}`).join("|"),
  () => {
    if (graph.value) restoreContextSuggestionFromGlobalRun();
  }
);

onBeforeUnmount(() => {
  window.removeEventListener("beforeunload", warnBeforeUnload);
  clearContextPollTimer();
});
</script>
