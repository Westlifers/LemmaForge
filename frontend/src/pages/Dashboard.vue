<template>
  <section class="page dashboard-page dashboard-v2">
    <header class="page-header dashboard-command-header">
      <div>
        <span class="eyebrow">Research operating desk</span>
        <h1>Research Dashboard</h1>
        <p>Overview of your local mathematical research environment.</p>
      </div>
      <div class="toolbar">
        <RouterLink class="button subtle" to="/review">
          <ClipboardCheck :size="16" aria-hidden="true" />
          Review
        </RouterLink>
        <RouterLink class="button primary" to="/import">
          <Inbox :size="16" aria-hidden="true" />
          Import
        </RouterLink>
      </div>
    </header>

    <section class="dashboard-metric-strip">
      <MetricCard
        label="Fragments"
        :value="fragments.length"
        :detail="`${acceptedCount} accepted / ${unsortedCount} unsorted`"
        :sparkline="fragmentTrend"
        :icon="Library"
      />
      <MetricCard
        label="Problems"
        :value="problems.length"
        :detail="`${activeProblemCount} active / ${blockedProblemCount} blocked`"
        :sparkline="problemTrend"
        :icon="Target"
        tone="blue"
        spark-color="#2478d4"
      />
      <MetricCard
        label="Definitions"
        :value="definitionCount"
        :detail="`${notationCount} notation/context notes`"
        :sparkline="typeTrend('Definition')"
        :icon="BookMarked"
        tone="success"
        spark-color="var(--success)"
      />
      <MetricCard
        label="Claims"
        :value="claimCount"
        :detail="`${theoremCount} theorems / ${propositionCount} propositions`"
        :sparkline="claimTrend"
        :icon="Sigma"
        tone="violet"
        spark-color="var(--violet)"
      />
      <MetricCard
        label="Proof Sketches"
        :value="proofSketchCount"
        :detail="`${constructionCount} constructions recorded`"
        :sparkline="typeTrend('ProofSketch')"
        :icon="PencilRuler"
        tone="blue"
        spark-color="#2478d4"
      />
      <MetricCard
        label="Needs Review"
        :value="reviewCount"
        :detail="`${rawCount} raw / ${candidateCount} candidate / ${draftCount} draft`"
        :sparkline="reviewTrend"
        :icon="TriangleAlert"
        tone="warning"
        spark-color="var(--warning)"
      />
      <MetricCard
        label="Context Packs"
        :value="packs.length"
        :detail="`${recentPacks.length} recently visible`"
        :sparkline="packTrend"
        :icon="Box"
      />
    </section>

    <div class="dashboard-v2-grid">
      <WorkspacePanel class="dashboard-review-panel" title="Needs Review" :subtitle="`${reviewCount} fragments waiting`">
        <template #action>
          <RouterLink class="text-button" to="/review">View all</RouterLink>
        </template>
        <div class="dashboard-row-list">
          <EntityRow
            v-for="fragment in reviewFragments"
            :key="fragment.id"
            :icon="reviewIcon(fragment.status)"
            :title="fragment.title"
            :meta="`${fragment.type} / ${fragment.id}`"
          >
            <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
          </EntityRow>
          <p v-if="!reviewFragments.length" class="empty-state">No fragments waiting for review.</p>
        </div>
      </WorkspacePanel>

      <WorkspacePanel class="dashboard-coverage-panel" title="Topic Coverage" subtitle="Sorted fragment coverage">
        <template #action>
          <RouterLink class="text-button" to="/topics">Manage</RouterLink>
        </template>
        <div class="coverage-layout">
          <DonutChart :value="sortedPercent" caption="Overall" label="Topic coverage" />
          <div class="coverage-topic-list">
            <article v-for="topic in topTopics" :key="topic.id" class="coverage-topic-row">
              <div>
                <RouterLink class="text-button" :to="`/topics/${topic.id}`">{{ topic.title }}</RouterLink>
                <span>{{ countForTopic(topic.id) }} fragments</span>
              </div>
              <ProgressBar :value="topicPercent(topic.id)" :label="`${topic.title} coverage`" />
              <strong>{{ topicPercent(topic.id) }}%</strong>
            </article>
            <article v-if="unsortedCount" class="coverage-topic-row warning">
              <div>
                <RouterLink class="text-button" to="/fragments?topic_id=__unsorted__">Unsorted</RouterLink>
                <span>{{ unsortedCount }} fragments</span>
              </div>
              <ProgressBar :value="unsortedPercent" label="Unsorted fragments" />
              <strong>{{ unsortedPercent }}%</strong>
            </article>
          </div>
        </div>
      </WorkspacePanel>

      <WorkspacePanel class="dashboard-recent-panel" title="Recent Fragments" subtitle="Latest updated material">
        <template #action>
          <RouterLink class="text-button" to="/fragments">Open</RouterLink>
        </template>
        <div class="dashboard-row-list">
          <EntityRow
            v-for="fragment in recentFragments"
            :key="fragment.id"
            :icon="typeIcon(fragment.type)"
            :title="fragment.title"
            :meta="`${fragment.type} / ${relativeTime(fragment.updated_at)}`"
          >
            <span class="status" :data-status="fragment.status">{{ fragment.status }}</span>
          </EntityRow>
          <p v-if="!recentFragments.length" class="empty-state">No fragments yet.</p>
        </div>
      </WorkspacePanel>

      <WorkspacePanel class="dashboard-table-panel" title="AI Task Activity" :subtitle="`${recentAiRuns.length} recent runs`">
        <template #action>
          <RouterLink class="text-button" to="/agent">Open AI Jobs</RouterLink>
        </template>
        <DashboardTable :headers="['Task', 'Status', 'Kind', 'Updated']">
          <tr v-for="run in recentAiRuns" :key="run.id">
            <td>{{ run.label }}</td>
            <td><StatusIndicator :tone="aiRunTone(run.status)">{{ run.status }}</StatusIndicator></td>
            <td>{{ aiRunKindLabel(run) }}</td>
            <td>{{ relativeTime(run.updated_at) }}</td>
          </tr>
          <tr v-if="!recentAiRuns.length">
            <td colspan="4">No AI operations recorded yet.</td>
          </tr>
        </DashboardTable>
      </WorkspacePanel>

      <WorkspacePanel class="dashboard-table-panel" title="Context Packs" :subtitle="`${packs.length} saved prompts`">
        <template #action>
          <RouterLink class="text-button" to="/context-packs">Manage</RouterLink>
        </template>
        <DashboardTable :headers="['Pack', 'Fragments', 'Topic', 'Updated']">
          <tr v-for="pack in recentPacks" :key="pack.id">
            <td>{{ pack.title }}</td>
            <td>{{ pack.items.length }}</td>
            <td>{{ topicTitle(pack.topic_id) }}</td>
            <td>{{ relativeTime(pack.updated_at) }}</td>
          </tr>
          <tr v-if="!recentPacks.length">
            <td colspan="4">No context packs saved yet.</td>
          </tr>
        </DashboardTable>
      </WorkspacePanel>

      <WorkspacePanel class="dashboard-ops-panel" title="Inbox And Sources" subtitle="Import and provenance status">
        <div class="ops-summary-grid">
          <article>
            <Inbox :size="18" aria-hidden="true" />
            <strong>{{ importBatches.length }}</strong>
            <span>import batches</span>
          </article>
          <article>
            <ClipboardCheck :size="18" aria-hidden="true" />
            <strong>{{ openImportCount }}</strong>
            <span>open imports</span>
          </article>
          <article>
            <BookOpen :size="18" aria-hidden="true" />
            <strong>{{ sources.length }}</strong>
            <span>source records</span>
          </article>
          <article>
            <Bot :size="18" aria-hidden="true" />
            <strong>{{ aiLogs.runningCount }}</strong>
            <span>AI running</span>
          </article>
        </div>
        <div class="action-row">
          <RouterLink class="button subtle" to="/import">Open Import</RouterLink>
          <RouterLink class="button subtle" to="/zotero">Sources</RouterLink>
        </div>
      </WorkspacePanel>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  ArchiveX,
  BookMarked,
  BookOpen,
  Bot,
  Box,
  ClipboardCheck,
  FileQuestion,
  Inbox,
  Library,
  PencilRuler,
  Sigma,
  Target,
  TriangleAlert,
} from "lucide-vue-next";
import DashboardTable from "../components/DashboardTable.vue";
import DonutChart from "../components/DonutChart.vue";
import EntityRow from "../components/EntityRow.vue";
import MetricCard from "../components/MetricCard.vue";
import ProgressBar from "../components/ProgressBar.vue";
import StatusIndicator from "../components/StatusIndicator.vue";
import WorkspacePanel from "../components/WorkspacePanel.vue";
import { api } from "../api/client";
import { useAILogsStore, type AILogRun, type AILogStatus } from "../stores/aiLogs";
import { useFragmentsStore } from "../stores/fragments";
import type { ContextPack, Fragment, FragmentStatus, FragmentType, ImportBatch, ResearchProblem, Source, Topic } from "../types";
import { acceptedFragmentStatuses, unacceptedFragmentStatuses } from "../types";

const store = useFragmentsStore();
const aiLogs = useAILogsStore();
const topics = ref<Topic[]>([]);
const problems = ref<ResearchProblem[]>([]);
const packs = ref<ContextPack[]>([]);
const importBatches = ref<ImportBatch[]>([]);
const sources = ref<Source[]>([]);
const fragments = computed(() => store.fragments);
const reviewStatuses: FragmentStatus[] = ["draft", "raw", "candidate"];
const reviewCount = computed(
  () => fragments.value.filter((item) => unacceptedFragmentStatuses.includes(item.status)).length
);
const acceptedCount = computed(
  () => fragments.value.filter((item) => acceptedFragmentStatuses.includes(item.status)).length
);
const draftCount = computed(() => statusCount("draft"));
const rawCount = computed(() => statusCount("raw"));
const candidateCount = computed(() => statusCount("candidate"));
const definitionCount = computed(() => typeCount("Definition"));
const notationCount = computed(() => typeCount("ContextNote") + typeCount("ExternalNotation"));
const theoremCount = computed(() => typeCount("Theorem"));
const propositionCount = computed(() => typeCount("Proposition"));
const claimCount = computed(() => theoremCount.value + propositionCount.value + typeCount("Conjecture"));
const proofSketchCount = computed(() => typeCount("ProofSketch"));
const constructionCount = computed(() => typeCount("Construction"));
const activeProblemCount = computed(() => problems.value.filter((item) => item.status === "active").length);
const blockedProblemCount = computed(() => problems.value.filter((item) => item.status === "blocked").length);
const unsortedCount = computed(() => fragments.value.filter((item) => !item.topic_id).length);
const sortedPercent = computed(() => {
  if (!fragments.value.length) return 0;
  return Math.round(((fragments.value.length - unsortedCount.value) / fragments.value.length) * 100);
});
const unsortedPercent = computed(() => {
  if (!fragments.value.length) return 0;
  return Math.round((unsortedCount.value / fragments.value.length) * 100);
});
const reviewFragments = computed(() =>
  fragments.value
    .filter((item) => unacceptedFragmentStatuses.includes(item.status))
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
    .slice(0, 6)
);
const recentFragments = computed(() =>
  [...fragments.value].sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at)).slice(0, 6)
);
const recentPacks = computed(() =>
  [...packs.value].sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at)).slice(0, 6)
);
const recentAiRuns = computed(() => aiLogs.runs.slice(0, 6));
const topTopics = computed(() =>
  [...topics.value].sort((left, right) => countForTopic(right.id) - countForTopic(left.id)).slice(0, 6)
);
const openImportCount = computed(() =>
  importBatches.value.filter((batch) => batch.status === "draft" || batch.status === "validated").length
);
const fragmentTrend = computed(() => dateBuckets(fragments.value, "updated_at"));
const reviewTrend = computed(() => dateBuckets(fragments.value.filter((item) => reviewStatuses.includes(item.status)), "updated_at"));
const claimTrend = computed(() =>
  dateBuckets(fragments.value.filter((item) => ["Theorem", "Proposition", "Conjecture"].includes(item.type)), "updated_at")
);
const packTrend = computed(() => dateBuckets(packs.value, "updated_at"));
const problemTrend = computed(() => dateBuckets(problems.value, "updated_at"));

function statusCount(status: FragmentStatus) {
  return fragments.value.filter((item) => item.status === status).length;
}

function typeCount(type: string) {
  return fragments.value.filter((item) => item.type === type).length;
}

function typeTrend(type: FragmentType) {
  return dateBuckets(fragments.value.filter((item) => item.type === type), "updated_at");
}

function countForTopic(topicId: string) {
  return fragments.value.filter((fragment) => fragment.topic_id === topicId).length;
}

function topicPercent(topicId: string) {
  if (!fragments.value.length) return 0;
  return Math.round((countForTopic(topicId) / fragments.value.length) * 100);
}

function topicTitle(topicId: string | null) {
  if (!topicId) return "No topic";
  return topics.value.find((topic) => topic.id === topicId)?.title || topicId;
}

function dateBuckets<T extends Record<string, unknown>>(items: T[], key: keyof T) {
  const bucketCount = 12;
  const buckets = Array.from({ length: bucketCount }, () => 0);
  const day = 24 * 60 * 60 * 1000;
  const start = Date.now() - (bucketCount - 1) * day;
  items.forEach((item) => {
    const value = item[key];
    if (typeof value !== "string") return;
    const timestamp = Date.parse(value);
    if (Number.isNaN(timestamp)) return;
    const index = Math.max(0, Math.min(bucketCount - 1, Math.floor((timestamp - start) / day)));
    buckets[index] += 1;
  });
  return buckets.some(Boolean) ? buckets : [0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1].map((value) => value * 0);
}

function reviewIcon(status: FragmentStatus) {
  if (status === "raw") return FileQuestion;
  if (status === "candidate") return ClipboardCheck;
  if (status === "draft") return TriangleAlert;
  return ArchiveX;
}

function typeIcon(type: string) {
  if (type === "Definition" || type === "ExternalNotation") return BookMarked;
  if (type === "ProofSketch") return PencilRuler;
  if (type === "Theorem" || type === "Proposition") return Sigma;
  return Library;
}

function aiRunTone(status: AILogStatus) {
  if (status === "failed") return "danger";
  if (status === "succeeded") return "success";
  if (status === "running" || status === "queued") return "warning";
  return "muted";
}

function aiRunKindLabel(run: AILogRun) {
  if (run.kind === "context_suggest") return "Context suggestion";
  if (run.kind === "import_extract") return "Fragment extraction";
  if (run.kind === "problem_summary") return "Problem proposal";
  return "AI operation";
}

function relativeTime(value: string) {
  const timestamp = Date.parse(value);
  if (Number.isNaN(timestamp)) return "recently";
  const seconds = Math.max(0, Math.round((Date.now() - timestamp) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

onMounted(async () => {
  await store.load();
  const [topicResult, problemResult, packResult, batchResult, sourceResult] = await Promise.all([
    api.listTopics(),
    api.listProblems(),
    api.listContextPacks(),
    api.listImportBatches(),
    api.listSources(),
  ]);
  topics.value = topicResult;
  problems.value = problemResult;
  packs.value = packResult;
  importBatches.value = batchResult;
  sources.value = sourceResult;
});
</script>
