<template>
  <section class="page dashboard-page">
    <header class="page-header dashboard-hero">
      <div>
        <span class="eyebrow">Research operating desk</span>
        <h1>Research Dashboard</h1>
        <p>Review drafts, keep topics sorted, and prepare AI context from one local console.</p>
      </div>
      <div class="toolbar">
        <RouterLink class="button subtle" to="/fragments">
          <Library :size="16" aria-hidden="true" />
          Browse
        </RouterLink>
        <RouterLink class="button primary" to="/import">
          <Inbox :size="16" aria-hidden="true" />
          Import
        </RouterLink>
      </div>
    </header>

    <div class="dashboard-grid">
      <section class="metric-grid dashboard-metrics">
        <article class="metric featured">
          <span><Library :size="15" aria-hidden="true" /> Total fragments</span>
          <strong>{{ fragments.length }}</strong>
          <small>{{ acceptedCount }} accepted / {{ reviewCount }} needs review</small>
        </article>
        <article class="metric">
          <span><ClipboardCheck :size="15" aria-hidden="true" /> Needs review</span>
          <strong>{{ reviewCount }}</strong>
          <small>draft, raw, candidate</small>
        </article>
        <article class="metric">
          <span><Network :size="15" aria-hidden="true" /> Topics</span>
          <strong>{{ topics.length }}</strong>
          <small>{{ unsortedCount }} unsorted fragments</small>
        </article>
        <article class="metric">
          <span><FileText :size="15" aria-hidden="true" /> Context packs</span>
          <strong>{{ packs.length }}</strong>
          <small>saved AI prompts</small>
        </article>
      </section>

      <section class="plain-section glass-panel dashboard-review">
        <header class="section-header">
          <div>
            <h2>Review Queue</h2>
            <p>Fragments waiting for your decision</p>
          </div>
          <RouterLink class="button subtle" to="/fragments?status=draft">
            <ArrowRight :size="16" aria-hidden="true" />
            Open
          </RouterLink>
        </header>
        <div class="review-meter" aria-hidden="true">
          <span :style="{ width: reviewWidth }"></span>
        </div>
        <div class="dashboard-status-row">
          <span v-for="status in reviewStatuses" :key="status" class="status-pill" :data-status="status">
            {{ status }}
            <strong>{{ statusCount(status) }}</strong>
          </span>
        </div>
      </section>

      <section class="plain-section glass-panel dashboard-topic-card">
        <header class="section-header">
          <div>
            <h2>Topic Coverage</h2>
            <p>Keep the graph tidy before building prompts</p>
          </div>
          <RouterLink class="button subtle" to="/topics">
            <Network :size="16" aria-hidden="true" />
            Topics
          </RouterLink>
        </header>
        <div class="topic-health">
          <strong>{{ sortedPercent }}%</strong>
          <span>sorted into topics</span>
        </div>
        <ul class="compact-list">
          <li v-for="topic in topTopics" :key="topic.id">
            <RouterLink class="text-button" :to="`/topics/${topic.id}`">{{ topic.title }}</RouterLink>
            <span>{{ countForTopic(topic.id) }} fragments</span>
          </li>
          <li v-if="!topTopics.length">
            <span class="muted">No topics yet.</span>
          </li>
        </ul>
      </section>

      <section class="plain-section glass-panel dashboard-ai-card">
        <header class="section-header">
          <div>
            <h2>AI Jobs</h2>
            <p>Recent Codex-assisted operations</p>
          </div>
          <span class="panel-icon">
            <Bot :size="18" aria-hidden="true" />
          </span>
        </header>
        <div class="ai-job-summary" :class="{ active: aiLogs.runningCount }">
          <span class="panel-icon">
            <Activity :size="18" aria-hidden="true" />
          </span>
          <div>
            <strong>{{ aiLogs.runningCount }}</strong>
            <span>running or queued</span>
          </div>
        </div>
        <div class="ai-job-list">
          <article v-for="run in visibleAiRuns" :key="run.id" class="ai-job-card" :data-status="run.status">
            <span class="ai-job-icon">
              <component :is="aiRunIcon(run)" :size="16" aria-hidden="true" />
            </span>
            <div>
              <strong>{{ run.label }}</strong>
              <small>{{ aiRunKindLabel(run) }} / {{ relativeTime(run.updated_at) }}</small>
            </div>
            <span class="status" :data-status="run.status">{{ run.status }}</span>
          </article>
          <div v-if="!recentAiRuns.length" class="ai-job-empty">
            <Bot :size="20" aria-hidden="true" />
            <span class="muted">AI logs will appear after import or context suggestions.</span>
          </div>
          <Transition name="collapse">
            <div v-if="aiJobsExpanded && hiddenAiRuns.length" class="ai-job-list ai-job-list-extra">
              <article v-for="run in hiddenAiRuns" :key="run.id" class="ai-job-card" :data-status="run.status">
                <span class="ai-job-icon">
                  <component :is="aiRunIcon(run)" :size="16" aria-hidden="true" />
                </span>
                <div>
                  <strong>{{ run.label }}</strong>
                  <small>{{ aiRunKindLabel(run) }} / {{ relativeTime(run.updated_at) }}</small>
                </div>
                <span class="status" :data-status="run.status">{{ run.status }}</span>
              </article>
            </div>
          </Transition>
          <button
            v-if="hiddenAiRuns.length"
            class="button subtle ai-job-expand"
            type="button"
            @click="aiJobsExpanded = !aiJobsExpanded"
          >
            <ChevronDown :class="{ open: aiJobsExpanded }" :size="16" aria-hidden="true" />
            {{ aiJobsExpanded ? "Show Less" : `Show ${hiddenAiRuns.length} More` }}
          </button>
        </div>
      </section>

      <section class="plain-section glass-panel dashboard-list wide">
        <header class="section-header">
          <div>
            <h2>Recent Fragments</h2>
            <p>Latest accepted or working material</p>
          </div>
          <RouterLink class="button subtle" to="/fragments">
            <ArrowRight :size="16" aria-hidden="true" />
            Browse
          </RouterLink>
        </header>
        <div class="list-stack">
          <FragmentCard v-for="fragment in recentFragments" :key="fragment.id" :fragment="fragment" />
          <p v-if="!recentFragments.length" class="empty-state">No accepted fragments yet.</p>
        </div>
      </section>

      <section class="plain-section glass-panel dashboard-list">
        <header class="section-header">
          <div>
            <h2>Recent Context Packs</h2>
            <p>Prompt packs ready for AI sessions</p>
          </div>
          <RouterLink class="button subtle" to="/context-packs">
            <FileText :size="16" aria-hidden="true" />
            Manage
          </RouterLink>
        </header>
        <ul class="compact-list context-pack-mini-list">
          <li v-for="pack in recentPacks" :key="pack.id">
            <RouterLink class="text-button" to="/context-packs">{{ pack.title }}</RouterLink>
            <span>{{ pack.items.length }} items</span>
          </li>
          <li v-if="!recentPacks.length">
            <span class="muted">No context packs saved yet.</span>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  Activity,
  ArrowRight,
  Bot,
  Brain,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  Clock3,
  FileSearch,
  FileText,
  Inbox,
  Library,
  LoaderCircle,
  Network,
  TriangleAlert,
} from "lucide-vue-next";
import FragmentCard from "../components/FragmentCard.vue";
import { api } from "../api/client";
import { useAILogsStore } from "../stores/aiLogs";
import { useFragmentsStore } from "../stores/fragments";
import type { ContextPack, FragmentStatus, Topic } from "../types";
import type { AILogRun } from "../stores/aiLogs";
import { acceptedFragmentStatuses, unacceptedFragmentStatuses } from "../types";

const store = useFragmentsStore();
const aiLogs = useAILogsStore();
const topics = ref<Topic[]>([]);
const packs = ref<ContextPack[]>([]);
const aiJobsExpanded = ref(false);
const fragments = computed(() => store.fragments);
const reviewStatuses: FragmentStatus[] = ["draft", "raw", "candidate"];
const reviewCount = computed(
  () => fragments.value.filter((item) => unacceptedFragmentStatuses.includes(item.status)).length
);
const acceptedCount = computed(
  () => fragments.value.filter((item) => acceptedFragmentStatuses.includes(item.status)).length
);
const unsortedCount = computed(() => fragments.value.filter((item) => !item.topic_id).length);
const sortedPercent = computed(() => {
  if (!fragments.value.length) return 0;
  return Math.round(((fragments.value.length - unsortedCount.value) / fragments.value.length) * 100);
});
const reviewWidth = computed(() => {
  if (!fragments.value.length) return "0%";
  return `${Math.min(100, Math.round((reviewCount.value / fragments.value.length) * 100))}%`;
});
const recentFragments = computed(() =>
  fragments.value
    .filter((item) => acceptedFragmentStatuses.includes(item.status))
    .sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at))
    .slice(0, 5)
);
const recentPacks = computed(() =>
  [...packs.value].sort((left, right) => Date.parse(right.updated_at) - Date.parse(left.updated_at)).slice(0, 5)
);
const recentAiRuns = computed(() => aiLogs.runs.slice(0, 5));
const visibleAiRuns = computed(() => recentAiRuns.value.slice(0, 3));
const hiddenAiRuns = computed(() => recentAiRuns.value.slice(3));
const topTopics = computed(() =>
  [...topics.value].sort((left, right) => countForTopic(right.id) - countForTopic(left.id)).slice(0, 5)
);

function statusCount(status: FragmentStatus) {
  return fragments.value.filter((item) => item.status === status).length;
}

function countForTopic(topicId: string) {
  return fragments.value.filter((fragment) => fragment.topic_id === topicId).length;
}

function aiRunIcon(run: AILogRun) {
  if (run.status === "failed") return TriangleAlert;
  if (run.status === "succeeded") return CheckCircle2;
  if (run.status === "queued") return Clock3;
  if (run.kind === "context_suggest") return Brain;
  if (run.kind === "import_extract") return FileSearch;
  return LoaderCircle;
}

function aiRunKindLabel(run: AILogRun) {
  if (run.kind === "context_suggest") return "Context suggestion";
  if (run.kind === "import_extract") return "Fragment extraction";
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
  const [topicResult, packResult] = await Promise.all([api.listTopics(), api.listContextPacks()]);
  topics.value = topicResult;
  packs.value = packResult;
});
</script>
