import { defineStore } from "pinia";

const LOG_KEY = "lemmaforge.aiLogs";
const MAX_RUNS = 12;
const MAX_LINES = 400;

export type AILogStatus = "queued" | "running" | "succeeded" | "failed";
export type AILogKind = "import_extract" | "context_suggest";

export interface AILogRun {
  id: string;
  kind: AILogKind | null;
  label: string;
  status: AILogStatus;
  logs: string[];
  error: string | null;
  result: unknown | null;
  context: Record<string, string | null> | null;
  created_at: string;
  updated_at: string;
}

export const useAILogsStore = defineStore("aiLogs", {
  state: () => ({
    runs: loadRuns(),
    activeRunId: "",
    panelOpen: false,
  }),
  getters: {
    activeRun(state): AILogRun | null {
      return state.runs.find((run) => run.id === state.activeRunId) || state.runs[0] || null;
    },
    runningCount(state): number {
      return state.runs.filter((run) => run.status === "queued" || run.status === "running").length;
    },
  },
  actions: {
    upsertRun(payload: {
      id: string;
      kind?: AILogKind | null;
      label: string;
      status: AILogStatus;
      logs?: string[];
      error?: string | null;
      result?: unknown | null;
      context?: Record<string, string | null> | null;
      open?: boolean;
    }) {
      const now = new Date().toISOString();
      const existing = this.runs.find((run) => run.id === payload.id);
      if (existing) {
        existing.label = payload.label || existing.label;
        existing.kind = payload.kind ?? existing.kind ?? null;
        existing.status = payload.status;
        existing.logs = trimLogs(payload.logs ?? existing.logs);
        existing.error = payload.error ?? null;
        existing.result = payload.result === undefined ? existing.result : payload.result;
        existing.context = payload.context === undefined ? existing.context : payload.context;
        existing.updated_at = now;
      } else {
        this.runs.unshift({
          id: payload.id,
          kind: payload.kind ?? null,
          label: payload.label,
          status: payload.status,
          logs: trimLogs(payload.logs ?? []),
          error: payload.error ?? null,
          result: payload.result ?? null,
          context: payload.context ?? null,
          created_at: now,
          updated_at: now,
        });
      }
      this.runs = this.runs
        .sort((left, right) => right.updated_at.localeCompare(left.updated_at))
        .slice(0, MAX_RUNS);
      this.activeRunId = payload.id;
      if (payload.open) this.panelOpen = true;
      persistRuns(this.runs);
    },
    appendLog(id: string, label: string, line: string) {
      const existing = this.runs.find((run) => run.id === id);
      const logs = existing ? [...existing.logs, line] : [line];
      this.upsertRun({
        id,
        kind: existing?.kind || null,
        label,
        status: existing?.status || "running",
        logs,
        error: existing?.error || null,
        result: existing?.result || null,
        context: existing?.context || null,
      });
    },
    setPanelOpen(open: boolean) {
      this.panelOpen = open;
    },
    clearRuns() {
      this.runs = [];
      this.activeRunId = "";
      persistRuns(this.runs);
    },
  },
});

function loadRuns(): AILogRun[] {
  const raw = localStorage.getItem(LOG_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as AILogRun[];
    return parsed.slice(0, MAX_RUNS).map((run) => ({
      ...run,
      kind: run.kind ?? null,
      status:
        !run.kind && (run.status === "queued" || run.status === "running")
          ? "failed"
          : run.status,
      logs: trimLogs(run.logs || []),
      error:
        !run.kind && (run.status === "queued" || run.status === "running")
          ? "This older AI run cannot be resumed because it has no job type metadata."
          : run.error ?? null,
      result: run.result ?? null,
      context: run.context ?? null,
    }));
  } catch {
    return [];
  }
}

function persistRuns(runs: AILogRun[]) {
  localStorage.setItem(LOG_KEY, JSON.stringify(runs.slice(0, MAX_RUNS)));
}

function trimLogs(logs: string[]) {
  return logs.slice(-MAX_LINES);
}
