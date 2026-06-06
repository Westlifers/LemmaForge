<template>
  <section class="page import-workspace">
    <header class="page-header">
      <div>
        <h1>Import</h1>
        <p>Extract draft fragments with Codex or write one manually</p>
      </div>
      <RouterLink class="button subtle" :to="{ path: '/fragments', query: { status: 'draft' } }">
        <ListChecks :size="16" aria-hidden="true" />
        View Drafts
      </RouterLink>
    </header>

    <div class="tabs">
      <button :class="{ active: activeTab === 'ai' }" type="button" @click="activeTab = 'ai'">
        <Sparkles :size="16" aria-hidden="true" />
        AI Extract
      </button>
      <button :class="{ active: activeTab === 'manual' }" type="button" @click="activeTab = 'manual'">
        <Pencil :size="16" aria-hidden="true" />
        Manual Draft
      </button>
    </div>

    <div v-if="activeTab === 'ai'" class="ai-import-grid">
      <section class="plain-section editor">
        <h2>Source Text</h2>
        <label>
          Excerpt or conversation
          <textarea v-model="aiForm.raw_excerpt" :disabled="isCompletedImport" required rows="18" />
        </label>
        <div class="form-grid two">
          <label>
            Topic hint
            <input v-model="aiForm.topic_hint" :disabled="isCompletedImport" placeholder="Optional" />
          </label>
          <label>
            Source kind
            <select v-model="aiForm.source_kind" :disabled="isCompletedImport">
              <option value="conversation">conversation</option>
              <option value="chatgpt_excerpt">chatgpt_excerpt</option>
              <option value="paper_excerpt">paper_excerpt</option>
              <option value="personal_note">personal_note</option>
              <option value="manual_excerpt">manual_excerpt</option>
            </select>
          </label>
          <label>
            Citekey
            <input v-model="aiForm.citekey" :disabled="isCompletedImport" placeholder="Optional" />
          </label>
          <label>
            Locator
            <input v-model="aiForm.locator" :disabled="isCompletedImport" placeholder="Optional page, theorem, section" />
          </label>
          <label>
            Timeout
            <select v-model.number="aiForm.timeout_seconds" :disabled="isCompletedImport">
              <option :value="300">5 minutes</option>
              <option :value="480">8 minutes</option>
              <option :value="720">12 minutes</option>
              <option :value="1200">20 minutes</option>
            </select>
          </label>
        </div>
        <div class="toolbar">
          <button class="button primary" type="button" :disabled="extracting || isCompletedImport || !aiForm.raw_excerpt.trim()" @click="extract">
            <Sparkles :size="16" aria-hidden="true" />
            {{ extracting ? "Extracting..." : "Extract With Codex" }}
          </button>
          <button class="button primary" type="button" :disabled="extracting && !isCompletedImport" @click="startNewImport">
            <Sparkles :size="16" aria-hidden="true" />
            Start New Import
          </button>
          <button class="button subtle" type="button" :disabled="!aiPreview" @click="resetAiReview">
            Clear Preview
          </button>
        </div>
        <p v-if="aiMessage" class="success-text">{{ aiMessage }}</p>
        <p v-if="aiError" class="error-text">{{ aiError }}</p>
        <section class="plain-section codex-log-panel">
          <header class="section-header">
            <div>
              <h2>Codex Feedback</h2>
              <p>{{ currentJob ? `${currentJob.status} / ${currentJob.job_id}` : "No extraction running" }}</p>
            </div>
          </header>
          <pre v-if="codexLogs.length" class="metadata-json codex-log">{{ codexLogs.join("\n") }}</pre>
          <p v-else class="muted">Codex stdout/stderr appears here while extraction runs.</p>
        </section>
      </section>

      <section class="plain-section ai-review-panel">
        <header class="section-header">
          <div>
            <h2>Extraction Review</h2>
            <p v-if="currentBatch">
              Batch {{ currentBatch.id }} / {{ selectedLocalIds.length }} selected
              <span v-if="isCompletedImport"> / completed</span>
            </p>
          </div>
          <button
            class="button primary"
            type="button"
            :disabled="!currentBatch || creatingDrafts || isCompletedImport || !selectedLocalIds.length"
            @click="createDrafts"
          >
            <Save :size="16" aria-hidden="true" />
            {{ creatingDrafts ? "Creating..." : "Create Drafts" }}
          </button>
        </header>

        <div v-if="aiPreview" class="patch-preview compact-preview">
          <div class="toolbar">
            <button class="button subtle" type="button" :disabled="isCompletedImport" @click="selectAllFragments">
              Select All
            </button>
            <button class="button subtle" type="button" :disabled="isCompletedImport" @click="clearFragmentSelection">
              Clear
            </button>
          </div>
          <div v-if="isCompletedImport" class="success-panel">
            <strong>Drafts created.</strong>
            <span>Start a new import when you are done checking links and applied relations.</span>
          </div>
          <div v-if="aiPreview.warnings.length" class="warning-list">
            <p v-for="warning in aiPreview.warnings" :key="warning">{{ warning }}</p>
          </div>

          <article
            v-for="fragment in aiPreview.patch.fragments"
            :key="fragment.local_id"
            class="fragment-card selectable-fragment-card"
            :class="{
              unselected: !selectedLocalIds.includes(fragment.local_id),
              saved: isFragmentSaved(fragment.local_id)
            }"
          >
            <div class="fragment-card__header">
              <label class="inline-check">
                <input
                  v-model="selectedLocalIds"
                  type="checkbox"
                  :value="fragment.local_id"
                  :disabled="isCompletedImport"
                />
                {{ isFragmentSaved(fragment.local_id) ? "Saved" : "Keep" }}
              </label>
              <span class="badge">{{ fragment.type }}</span>
              <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
              <span class="chip" data-chip="ai">AI extracted</span>
            </div>
            <h3>{{ fragment.title }}</h3>
            <p>{{ fragment.body }}</p>
            <footer>
              <span class="chip" data-chip="origin">Origin: {{ fragment.origin_classification }}</span>
              <span class="chip" data-chip="exactness">Exactness: {{ fragment.exactness }}</span>
              <RouterLink
                v-if="draftResult?.local_to_fragment_id[fragment.local_id]"
                class="chip"
                data-chip="topic"
                :to="`/fragments/${draftResult.local_to_fragment_id[fragment.local_id]}`"
              >
                Draft
              </RouterLink>
              <span v-if="fragment.confidence !== null" class="chip">Confidence: {{ fragment.confidence }}</span>
            </footer>
          </article>

          <section v-if="aiPreview.patch.source_pointers.length" class="plain-section">
            <h3>Source Pointers</h3>
            <ul class="compact-list">
              <li v-for="pointer in aiPreview.patch.source_pointers" :key="`${pointer.fragment_local_id}-${pointer.citekey}-${pointer.locator}`">
                <code>{{ pointer.fragment_local_id }}</code>
                <span>{{ pointer.citekey || pointer.source?.title || "inline source" }}</span>
                <span v-if="pointer.locator">{{ pointer.locator }}</span>
              </li>
            </ul>
          </section>
        </div>
        <div v-else class="muted-panel plain-section">
          <p>Paste source text and run extraction to review structured candidates.</p>
        </div>
      </section>

      <aside class="plain-section ai-side-panel">
        <section class="plain-section">
          <h2>Duplicate Suggestions</h2>
          <ul v-if="suggestions.length" class="compact-list">
            <li v-for="suggestion in suggestions" :key="`${suggestion.local_id}-${suggestion.fragment_id}`">
              <code>{{ suggestion.local_id }}</code>
              <RouterLink :to="`/fragments/${suggestion.fragment_id}`">{{ suggestion.title }}</RouterLink>
              <span>{{ Math.round(suggestion.score * 100) }}%</span>
            </li>
          </ul>
          <p v-else class="muted">Suggestions appear after extraction.</p>
        </section>

        <section class="plain-section">
          <h2>Created Drafts</h2>
          <ul v-if="draftResult?.fragment_ids.length" class="compact-list">
            <li v-for="fragmentId in draftResult.fragment_ids" :key="fragmentId">
              <RouterLink :to="`/fragments/${fragmentId}`">{{ fragmentId }}</RouterLink>
            </li>
          </ul>
          <p v-else class="muted">Draft links appear after creation.</p>
        </section>

        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Relation Proposals</h2>
              <p>{{ relationProposals.length }} proposed</p>
            </div>
            <button
              class="button subtle"
              type="button"
              :disabled="!selectedProposalIds.length || applyingRelations || !currentBatch"
              @click="applySelectedRelations"
            >
              <GitBranch :size="16" aria-hidden="true" />
              Apply
            </button>
          </header>
          <div v-if="relationProposals.length" class="list-stack">
            <label
              v-for="proposal in relationProposals"
              :key="proposal.proposal_id"
              class="proposal-row"
              :class="{ applied: !!proposal.applied_relation_id }"
            >
              <input
                v-model="selectedProposalIds"
                type="checkbox"
                :value="proposal.proposal_id"
                :disabled="!!proposal.applied_relation_id"
              />
              <span>
                <code>{{ proposal.source }}</code>
                {{ proposal.kind }}
                <code>{{ proposal.target }}</code>
              </span>
              <small v-if="proposal.applied_relation_id">applied</small>
            </label>
          </div>
          <p v-else class="muted">Codex relation proposals stay here until you apply them.</p>
        </section>
      </aside>
    </div>

    <div v-else class="split">
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
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { GitBranch, ListChecks, Pencil, Save, Sparkles } from "lucide-vue-next";
import { api } from "../api/client";
import FragmentCard from "../components/FragmentCard.vue";
import { useFragmentsStore } from "../stores/fragments";
import type {
  AIDraftCreationResult,
  AIRelationProposal,
  DuplicateSuggestion,
  AIExtractJob,
  Fragment,
  ImportBatch,
  ImportPreview,
  Topic
} from "../types";
import { fragmentTypes } from "../types";

const AI_REVIEW_CACHE_KEY = "lemmaforge.aiImportReview";
const fragments = useFragmentsStore();
const activeTab = ref<"ai" | "manual">("ai");
const topics = ref<Topic[]>([]);
const message = ref("");
const error = ref("");
const aiMessage = ref("");
const aiError = ref("");
const extracting = ref(false);
const creatingDrafts = ref(false);
const applyingRelations = ref(false);
const aiPreview = ref<ImportPreview | null>(null);
const currentJob = ref<AIExtractJob | null>(null);
const codexLogs = ref<string[]>([]);
const currentBatch = ref<ImportBatch | null>(null);
const draftResult = ref<AIDraftCreationResult | null>(null);
const suggestions = ref<DuplicateSuggestion[]>([]);
const selectedProposalIds = ref<string[]>([]);
const selectedLocalIds = ref<string[]>([]);
const aiForm = reactive({
  raw_excerpt: "",
  topic_hint: "",
  citekey: "",
  locator: "",
  source_kind: "conversation",
  timeout_seconds: 480
});
let pollTimer: number | undefined;
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
const relationProposals = computed<AIRelationProposal[]>(() =>
  draftResult.value?.relation_proposals || currentBatch.value?.relation_proposals || []
);
const isCompletedImport = computed(() => !!draftResult.value?.fragment_ids.length);

async function load() {
  topics.value = await api.listTopics();
  await fragments.load({ status: "draft" });
  await restoreAiReview();
}

async function extract() {
  aiError.value = "";
  aiMessage.value = "";
  extracting.value = true;
  resetAiReview();
  try {
    currentJob.value = await api.startAiExtractJob({
      raw_excerpt: aiForm.raw_excerpt,
      topic_hint: emptyToNull(aiForm.topic_hint),
      citekey: emptyToNull(aiForm.citekey),
      locator: emptyToNull(aiForm.locator),
      source_kind: aiForm.source_kind,
      timeout_seconds: aiForm.timeout_seconds
    });
    codexLogs.value = currentJob.value.logs;
    aiMessage.value = "Codex extraction started.";
    persistAiReview();
    pollExtractionJob(currentJob.value.job_id);
  } catch (caught) {
    aiError.value = caught instanceof Error ? caught.message : String(caught);
    extracting.value = false;
  }
}

async function pollExtractionJob(jobId: string) {
  clearPollTimer();
  try {
    const job = await api.getAiExtractJob(jobId);
    currentJob.value = job;
    codexLogs.value = job.logs;
    persistAiReview();
    if (job.status === "queued" || job.status === "running") {
      pollTimer = window.setTimeout(() => pollExtractionJob(jobId), 1000);
      return;
    }
    extracting.value = false;
    const result = job.result;
    if (!result) {
      aiError.value = job.error || "Codex extraction finished without a result.";
      return;
    }
    if (!result.available) {
      aiError.value = result.error || "Codex CLI is unavailable.";
      return;
    }
    if (result.error) {
      aiError.value = result.error;
      return;
    }
    aiPreview.value = result.preview;
    selectedLocalIds.value = result.preview?.patch.fragments.map((fragment) => fragment.local_id) || [];
    currentBatch.value = result.batch;
    draftResult.value = result.batch?.ai_draft_result || null;
    aiMessage.value = `Validated ${result.preview?.fragment_count || 0} extracted fragments.`;
    persistAiReview();
    await loadSuggestions();
  } catch (caught) {
    aiError.value = caught instanceof Error ? caught.message : String(caught);
    extracting.value = false;
  }
}

async function createDrafts() {
  if (!currentBatch.value) return;
  aiError.value = "";
  creatingDrafts.value = true;
  try {
    draftResult.value = await api.aiCreateDrafts({
      batch_id: currentBatch.value.id,
      selected_local_ids: selectedLocalIds.value
    });
    currentBatch.value = await api.getImportBatch(currentBatch.value.id);
    aiMessage.value = `Created ${draftResult.value.fragment_ids.length} draft fragments.`;
    persistAiReview();
    await fragments.load({ status: "draft" });
  } catch (caught) {
    aiError.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    creatingDrafts.value = false;
  }
}

async function applySelectedRelations() {
  if (!currentBatch.value || !selectedProposalIds.value.length) return;
  aiError.value = "";
  applyingRelations.value = true;
  try {
    const result = await api.aiApplyRelations(currentBatch.value.id, selectedProposalIds.value);
    selectedProposalIds.value = [];
    currentBatch.value = await api.getImportBatch(currentBatch.value.id);
    if (draftResult.value) {
      draftResult.value.relation_proposals = result.relation_proposals;
    }
    aiMessage.value = `Applied ${result.relation_ids.length} relations.`;
    persistAiReview();
  } catch (caught) {
    aiError.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    applyingRelations.value = false;
  }
}

async function loadSuggestions() {
  if (!currentBatch.value) return;
  try {
    suggestions.value = (await api.importBatchSuggestions(currentBatch.value.id)).suggestions;
  } catch {
    suggestions.value = [];
  }
}

function resetAiReview() {
  clearPollTimer();
  aiPreview.value = null;
  currentBatch.value = null;
  currentJob.value = null;
  codexLogs.value = [];
  draftResult.value = null;
  suggestions.value = [];
  selectedProposalIds.value = [];
  selectedLocalIds.value = [];
  aiMessage.value = "";
  aiError.value = "";
  sessionStorage.removeItem(AI_REVIEW_CACHE_KEY);
}

function startNewImport() {
  resetAiReview();
  aiForm.raw_excerpt = "";
  aiForm.topic_hint = "";
  aiForm.citekey = "";
  aiForm.locator = "";
  aiForm.source_kind = "conversation";
  aiForm.timeout_seconds = 480;
}

function isFragmentSaved(localId: string) {
  return !!draftResult.value?.local_to_fragment_id[localId];
}

function selectAllFragments() {
  selectedLocalIds.value = aiPreview.value?.patch.fragments.map((fragment) => fragment.local_id) || [];
  persistAiReview();
}

function clearFragmentSelection() {
  selectedLocalIds.value = [];
  persistAiReview();
}

function clearPollTimer() {
  if (pollTimer !== undefined) {
    window.clearTimeout(pollTimer);
    pollTimer = undefined;
  }
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

function emptyToNull(value: string) {
  return value.trim() || null;
}

function previewFromBatch(batch: ImportBatch): ImportPreview | null {
  if (!batch.patch) return null;
  return {
    valid: true,
    fragment_count: batch.patch.fragments.length,
    relation_count: batch.patch.relations.length,
    source_pointer_count: batch.patch.source_pointers.length,
    warnings: batch.warnings,
    patch: batch.patch
  };
}

async function restoreAiReview() {
  const cached = readCachedReview();
  if (cached?.job_id) {
    try {
      const job = await api.getAiExtractJob(cached.job_id);
      currentJob.value = job;
      codexLogs.value = job.logs;
      if (job.status === "queued" || job.status === "running") {
        extracting.value = true;
        pollExtractionJob(job.job_id);
        return;
      }
      if (job.result?.batch) {
        restoreBatchState(job.result.batch, cached.selected_local_ids);
        currentJob.value = job;
        codexLogs.value = job.logs;
        aiMessage.value = "Restored previous extraction.";
        return;
      }
    } catch {
      currentJob.value = null;
    }
  }

  if (cached?.batch_id) {
    try {
      const batch = await api.getImportBatch(cached.batch_id);
      restoreBatchState(batch, cached.selected_local_ids);
      aiMessage.value = "Restored previous extraction.";
      return;
    } catch {
      sessionStorage.removeItem(AI_REVIEW_CACHE_KEY);
    }
  }

  await restoreLatestBatch();
}

async function restoreLatestBatch() {
  try {
    const batches = await api.listImportBatches();
    const batch = batches.find(
      (item) =>
        item.patch &&
        item.patch.metadata.created_by === "codex_import_agent" &&
        (item.status === "validated" || (item.status === "committed" && !!item.ai_draft_result))
    );
    if (!batch) return;
    restoreBatchState(batch, null);
    aiMessage.value = "Restored latest AI extraction.";
  } catch {
    // Best-effort cache restore; leave a clean empty page if it fails.
  }
}

function restoreBatchState(batch: ImportBatch, selectedLocalIdsFromCache: string[] | null | undefined) {
  currentBatch.value = batch;
  aiPreview.value = previewFromBatch(batch);
  draftResult.value = batch.ai_draft_result;
  selectedProposalIds.value = [];
  selectedLocalIds.value =
    selectedLocalIdsFromCache && selectedLocalIdsFromCache.length
      ? selectedLocalIdsFromCache
      : batch.patch?.fragments.map((fragment) => fragment.local_id) || [];
  aiForm.raw_excerpt = batch.raw_excerpt || aiForm.raw_excerpt;
  aiForm.topic_hint = batch.topic_hint || "";
  aiForm.citekey = batch.citekey || "";
  aiForm.locator = batch.locator || "";
  loadSuggestions();
  persistAiReview();
}

function persistAiReview() {
  if (!currentBatch.value && !currentJob.value) return;
  sessionStorage.setItem(
    AI_REVIEW_CACHE_KEY,
    JSON.stringify({
      batch_id: currentBatch.value?.id || currentJob.value?.result?.batch?.id || null,
      job_id: currentJob.value?.job_id || null,
      selected_local_ids: selectedLocalIds.value,
      updated_at: new Date().toISOString()
    })
  );
}

function readCachedReview(): {
  batch_id?: string | null;
  job_id?: string | null;
  selected_local_ids?: string[] | null;
} | null {
  const raw = sessionStorage.getItem(AI_REVIEW_CACHE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    sessionStorage.removeItem(AI_REVIEW_CACHE_KEY);
    return null;
  }
}

onMounted(load);
onBeforeUnmount(clearPollTimer);
watch(selectedLocalIds, persistAiReview);
</script>
