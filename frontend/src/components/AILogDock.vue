<template>
  <div class="ai-log-dock">
    <transition name="toast">
      <section v-if="toastMessage" class="ai-toast">
        <strong>{{ toastMessage }}</strong>
      </section>
    </transition>
    <button class="ai-log-fab" type="button" @click="logs.setPanelOpen(!logs.panelOpen)">
      <Bot :size="18" aria-hidden="true" />
      <span v-if="logs.runningCount">{{ logs.runningCount }}</span>
    </button>
    <Transition name="popover">
      <section v-if="logs.panelOpen" class="ai-log-popover">
        <header class="section-header">
          <div>
            <h3>AI Logs</h3>
            <p>{{ logs.runs.length ? `${logs.runs.length} recent runs` : "No AI runs yet" }}</p>
          </div>
          <button class="icon-button" type="button" aria-label="Close AI logs" @click="logs.setPanelOpen(false)">
            <X :size="16" aria-hidden="true" />
          </button>
        </header>
        <div class="ai-log-layout">
          <ul class="ai-log-run-list">
            <li v-for="run in logs.runs" :key="run.id">
              <button
                type="button"
                :class="{ active: run.id === logs.activeRun?.id }"
                @click="logs.activeRunId = run.id"
              >
                <strong>{{ run.label }}</strong>
                <span :data-status="run.status">{{ run.status }}</span>
              </button>
            </li>
          </ul>
          <div class="ai-log-detail">
            <template v-if="logs.activeRun">
              <header>
                <strong>{{ logs.activeRun.label }}</strong>
                <span :data-status="logs.activeRun.status">{{ logs.activeRun.status }}</span>
              </header>
              <p v-if="logs.activeRun.error" class="error-text">{{ logs.activeRun.error }}</p>
              <pre v-if="logs.activeRun.logs.length" class="metadata-json codex-log">{{ logs.activeRun.logs.join("\n") }}</pre>
              <p v-else class="muted">No log lines yet.</p>
            </template>
            <p v-else class="muted">AI operation logs will appear here.</p>
          </div>
        </div>
        <footer class="action-row">
          <button class="button subtle" type="button" :disabled="!logs.runs.length" @click="logs.clearRuns">
            Clear
          </button>
        </footer>
      </section>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted } from "vue";
import { Bot, X } from "lucide-vue-next";
import { api } from "../api/client";
import { useAILogsStore } from "../stores/aiLogs";

const logs = useAILogsStore();
const toastMessage = ref("");
let pollTimer: number | undefined;
let toastTimer: number | undefined;

function startPolling() {
  clearPolling();
  pollTimer = window.setInterval(() => {
    void pollRunningJobs();
  }, 1000);
  void pollRunningJobs();
}

function clearPolling() {
  if (pollTimer !== undefined) {
    window.clearInterval(pollTimer);
    pollTimer = undefined;
  }
}

async function pollRunningJobs() {
  const running = logs.runs.filter((run) => run.status === "queued" || run.status === "running");
  for (const run of running) {
    try {
      if (run.kind === "import_extract") {
        const job = await api.getAiExtractJob(run.id);
        maybeShowSuccess(run.status, job.status, run.label);
        logs.upsertRun({
          id: job.job_id,
          kind: "import_extract",
          label: run.label,
          status: job.status,
          logs: job.logs,
          error: job.error,
          result: job.result,
          context: run.context,
        });
      } else if (run.kind === "context_suggest") {
        const job = await api.getContextPackSuggestJob(run.id);
        maybeShowSuccess(run.status, job.status, run.label);
        logs.upsertRun({
          id: job.job_id,
          kind: "context_suggest",
          label: run.label,
          status: job.status,
          logs: job.logs,
          error: job.error,
          result: job.result,
          context: run.context,
        });
      }
    } catch (caught) {
      logs.upsertRun({
        id: run.id,
        kind: run.kind,
        label: run.label,
        status: "failed",
        logs: run.logs,
        error: caught instanceof Error ? caught.message : String(caught),
        result: run.result,
        context: run.context,
      });
    }
  }
}

function maybeShowSuccess(previousStatus: string, nextStatus: string, label: string) {
  if ((previousStatus === "queued" || previousStatus === "running") && nextStatus === "succeeded") {
    showToast(`${label} completed.`);
  }
}

function showToast(message: string) {
  toastMessage.value = message;
  if (toastTimer !== undefined) window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    toastMessage.value = "";
  }, 4200);
}

onMounted(startPolling);
onBeforeUnmount(() => {
  clearPolling();
  if (toastTimer !== undefined) window.clearTimeout(toastTimer);
});
</script>
