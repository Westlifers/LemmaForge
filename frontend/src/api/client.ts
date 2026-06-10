import type {
  AIApplyRelationsResult,
  AICreateDraftsRequest,
  AIDraftCreationResult,
  AIExtractRequest,
  AIExtractResult,
  AIExtractJob,
  AppHealth,
  Attempt,
  AttemptFragmentLink,
  AttemptFragmentRole,
  AttemptStatus,
  AttemptWorkspace,
  ContextPack,
  ContextPackItemInput,
  ContextPackSuggestJob,
  ContextPackSuggestRequest,
  ContextPackSuggestResult,
  DuplicateSuggestion,
  Fragment,
  FragmentVersion,
  ImportBatch,
  ImportCommitResult,
  ImportPreview,
  ProblemFragmentLink,
  ProblemFragmentRole,
  ProblemStatus,
  ProblemSummaryRequest,
  ProblemSummaryResult,
  ProblemSummaryJob,
  ProblemTopicLink,
  ProblemWorkspace,
  Relation,
  ResearchPatch,
  ResearchProblem,
  Source,
  SourcePointer,
  TopicGraph,
  ZoteroItemResult,
  ZoteroSearchResult,
  ZoteroStatus,
  ZoteroSyncResult
} from "../types";

const jsonHeaders = { "Content-Type": "application/json" };

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export interface FragmentFilters {
  search?: string;
  type?: string;
  status?: string;
  topic_id?: string;
  origin_classification?: string;
  exactness?: string;
  source_citekey?: string;
}

export interface ProblemFilters {
  search?: string;
  status?: string;
}

function queryString(filters: FragmentFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const api = {
  health() {
    return request<AppHealth>("/api/health");
  },
  listFragments(filters: FragmentFilters = {}) {
    return request<Fragment[]>(`/api/fragments${queryString(filters)}`);
  },
  listProblems(filters: ProblemFilters = {}) {
    return request<ResearchProblem[]>(`/api/problems${queryString(filters)}`);
  },
  createProblem(payload: {
    title: string;
    status?: ProblemStatus;
    objective: string;
    current_formulation?: string | null;
    motivation?: string | null;
    why_it_matters?: string | null;
  }) {
    return request<ResearchProblem>("/api/problems", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getProblem(id: string) {
    return request<ResearchProblem>(`/api/problems/${id}`);
  },
  getProblemWorkspace(id: string) {
    return request<ProblemWorkspace>(`/api/problems/${id}/workspace`);
  },
  updateProblemGraphLayout(id: string, positions: Record<string, { node_key: string; x: number; y: number }>) {
    return request<ProblemWorkspace>(`/api/problems/${id}/graph-layout`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify({ positions })
    });
  },
  updateProblem(id: string, payload: Partial<ResearchProblem>) {
    return request<ResearchProblem>(`/api/problems/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  deleteProblem(id: string) {
    return request<void>(`/api/problems/${id}`, { method: "DELETE" });
  },
  listProblemTopics(problemId: string) {
    return request<ProblemTopicLink[]>(`/api/problems/${problemId}/topics`);
  },
  addProblemTopic(problemId: string, topic_id: string) {
    return request<ProblemTopicLink>(`/api/problems/${problemId}/topics`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ topic_id })
    });
  },
  removeProblemTopic(problemId: string, topicId: string) {
    return request<void>(`/api/problems/${problemId}/topics/${topicId}`, { method: "DELETE" });
  },
  listProblemFragments(problemId: string) {
    return request<ProblemFragmentLink[]>(`/api/problems/${problemId}/fragments`);
  },
  addProblemFragment(problemId: string, payload: { fragment_id: string; role: ProblemFragmentRole; note?: string | null }) {
    return request<ProblemFragmentLink>(`/api/problems/${problemId}/fragments`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  updateProblemFragment(problemId: string, linkId: string, payload: { role?: ProblemFragmentRole; note?: string | null }) {
    return request<ProblemFragmentLink>(`/api/problems/${problemId}/fragments/${linkId}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  removeProblemFragment(problemId: string, linkId: string) {
    return request<void>(`/api/problems/${problemId}/fragments/${linkId}`, { method: "DELETE" });
  },
  suggestProblemSummary(payload: ProblemSummaryRequest) {
    return request<ProblemSummaryResult>("/api/problems/ai/summarize", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  startProblemSummaryJob(payload: ProblemSummaryRequest) {
    return request<ProblemSummaryJob>("/api/problems/ai/summary-jobs", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getProblemSummaryJob(jobId: string) {
    return request<ProblemSummaryJob>(`/api/problems/ai/summary-jobs/${jobId}`);
  },
  listProblemAttempts(problemId: string) {
    return request<Attempt[]>(`/api/problems/${problemId}/attempts`);
  },
  createAttempt(problemId: string, payload: {
    title: string;
    status?: AttemptStatus;
    strategy: string;
    expected_outcome?: string | null;
    result_summary?: string | null;
    failure_reason?: string | null;
    next_step?: string | null;
  }) {
    return request<Attempt>(`/api/problems/${problemId}/attempts`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getAttempt(id: string) {
    return request<Attempt>(`/api/attempts/${id}`);
  },
  getAttemptWorkspace(id: string) {
    return request<AttemptWorkspace>(`/api/attempts/${id}/workspace`);
  },
  updateAttempt(id: string, payload: Partial<Attempt>) {
    return request<Attempt>(`/api/attempts/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  deleteAttempt(id: string) {
    return request<void>(`/api/attempts/${id}`, { method: "DELETE" });
  },
  listAttemptFragments(attemptId: string) {
    return request<AttemptFragmentLink[]>(`/api/attempts/${attemptId}/fragments`);
  },
  addAttemptFragment(attemptId: string, payload: { fragment_id: string; role: AttemptFragmentRole; note?: string | null }) {
    return request<AttemptFragmentLink>(`/api/attempts/${attemptId}/fragments`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  updateAttemptFragment(attemptId: string, linkId: string, payload: { role?: AttemptFragmentRole; note?: string | null }) {
    return request<AttemptFragmentLink>(`/api/attempts/${attemptId}/fragments/${linkId}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  removeAttemptFragment(attemptId: string, linkId: string) {
    return request<void>(`/api/attempts/${attemptId}/fragments/${linkId}`, { method: "DELETE" });
  },
  createFragment(payload: Partial<Fragment> & { source_citekey?: string | null; source_locator?: string | null }) {
    return request<Fragment>("/api/fragments", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getFragment(id: string) {
    return request<Fragment>(`/api/fragments/${id}`);
  },
  updateFragment(id: string, payload: Partial<Fragment> & { change_note?: string }) {
    return request<Fragment>(`/api/fragments/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  bulkUpdateFragments(payload: { ids: string[]; topic_id?: string | null; status?: string | null; change_note?: string | null }) {
    return request<Fragment[]>("/api/fragments/bulk", {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  deleteFragment(id: string) {
    return request<void>(`/api/fragments/${id}`, { method: "DELETE" });
  },
  bulkDeleteFragments(ids: string[]) {
    return request<{ deleted_ids: string[] }>("/api/fragments/bulk", {
      method: "DELETE",
      headers: jsonHeaders,
      body: JSON.stringify(ids)
    });
  },
  listVersions(id: string) {
    return request<FragmentVersion[]>(`/api/fragments/${id}/versions`);
  },
  listRelations(id: string) {
    return request<Relation[]>(`/api/fragments/${id}/relations`);
  },
  listSourcePointers(id: string) {
    return request<SourcePointer[]>(`/api/fragments/${id}/source-pointers`);
  },
  listOutgoingRelations(id: string) {
    return request<Relation[]>(`/api/fragments/${id}/relations/outgoing`);
  },
  listIncomingRelations(id: string) {
    return request<Relation[]>(`/api/fragments/${id}/relations/incoming`);
  },
  createRelation(payload: {
    source_fragment_id: string;
    relation_kind: string;
    target_fragment_id: string;
    confidence?: number | null;
  }) {
    return request<Relation>("/api/relations", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  updateRelation(id: string, payload: Partial<Relation>) {
    return request<Relation>(`/api/relations/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  deleteRelation(id: string) {
    return request<void>(`/api/relations/${id}`, { method: "DELETE" });
  },
  validatePatch(patch: ResearchPatch) {
    return request<ImportPreview>("/api/import/validate", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(patch)
    });
  },
  previewPatch(patch: ResearchPatch) {
    return request<ImportPreview>("/api/import/preview", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(patch)
    });
  },
  commitPatch(patch: ResearchPatch) {
    return request<ImportCommitResult>("/api/import/commit", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(patch)
    });
  },
  aiExtract(payload: AIExtractRequest) {
    return request<AIExtractResult>("/api/import/ai/extract", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  startAiExtractJob(payload: AIExtractRequest) {
    return request<AIExtractJob>("/api/import/ai/extraction-jobs", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getAiExtractJob(jobId: string) {
    return request<AIExtractJob>(`/api/import/ai/extraction-jobs/${jobId}`);
  },
  aiCreateDrafts(payload: AICreateDraftsRequest) {
    return request<AIDraftCreationResult>("/api/import/ai/create-drafts", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  aiApplyRelations(batchId: string, proposal_ids: string[]) {
    return request<AIApplyRelationsResult>(`/api/import/ai/${batchId}/apply-relations`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ proposal_ids })
    });
  },
  listImportBatches() {
    return request<ImportBatch[]>("/api/import/batches");
  },
  createImportBatch(payload: {
    raw_excerpt?: string;
    topic_hint?: string | null;
    citekey?: string | null;
    locator?: string | null;
    patch?: ResearchPatch | null;
    review_note?: string | null;
  }) {
    return request<ImportBatch>("/api/import/batches", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getImportBatch(id: string) {
    return request<ImportBatch>(`/api/import/batches/${id}`);
  },
  updateImportBatch(id: string, payload: Partial<ImportBatch> & { patch?: ResearchPatch | null }) {
    return request<ImportBatch>(`/api/import/batches/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  validateImportBatch(id: string) {
    return request<ImportBatch>(`/api/import/batches/${id}/validate`, { method: "POST" });
  },
  commitImportBatch(id: string, gitCommit = false) {
    return request<ImportBatch>(`/api/import/batches/${id}/commit?git_commit=${gitCommit}`, {
      method: "POST"
    });
  },
  rejectImportBatch(id: string, review_note?: string | null) {
    return request<ImportBatch>(`/api/import/batches/${id}/reject`, {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify({ review_note })
    });
  },
  importBatchSuggestions(id: string) {
    return request<{ batch_id: string; suggestions: DuplicateSuggestion[] }>(
      `/api/import/batches/${id}/suggestions`
    );
  },
  listContextPacks() {
    return request<ContextPack[]>("/api/context-packs");
  },
  createContextPack(payload: {
    title: string;
    topic_id?: string | null;
    objective: string;
    task_prompt?: string | null;
    body?: string;
    items: ContextPackItemInput[];
  }) {
    return request<ContextPack>("/api/context-packs", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  exportContextPack(id: string) {
    return request<{ context_pack_id: string; markdown: string; path: string | null }>(
      `/api/context-packs/${id}/export`,
      { method: "POST" }
    );
  },
  deleteContextPack(id: string) {
    return request<void>(`/api/context-packs/${id}`, { method: "DELETE" });
  },
  updateContextPack(id: string, payload: { title?: string; objective?: string; task_prompt?: string | null; body?: string }) {
    return request<ContextPack>(`/api/context-packs/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  suggestContextPack(payload: ContextPackSuggestRequest) {
    return request<ContextPackSuggestResult>("/api/context-packs/ai/suggest", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  startContextPackSuggestJob(payload: ContextPackSuggestRequest) {
    return request<ContextPackSuggestJob>("/api/context-packs/ai/suggestion-jobs", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  getContextPackSuggestJob(jobId: string) {
    return request<ContextPackSuggestJob>(`/api/context-packs/ai/suggestion-jobs/${jobId}`);
  },
  listTopicContextPacks(topicId: string) {
    return request<ContextPack[]>(`/api/topics/${topicId}/context-packs`);
  },
  zoteroStatus() {
    return request<ZoteroStatus>("/api/zotero/status");
  },
  saveZoteroSettings(payload: { zotero_local_api_url?: string | null; references_bib?: string | null; zotero_data_dir?: string | null }) {
    return request<{ saved: boolean; path: string }>("/api/zotero/settings", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  zoteroSearch(query: string, limit = 20) {
    return request<ZoteroSearchResult>(
      `/api/zotero/search?query=${encodeURIComponent(query)}&limit=${limit}`
    );
  },
  getZoteroItem(itemKey: string) {
    return request<ZoteroItemResult>(`/api/zotero/items/${encodeURIComponent(itemKey)}`);
  },
  zoteroSync(itemKeys?: string[]) {
    return request<ZoteroSyncResult>("/api/zotero/sync", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(itemKeys?.length ? { item_keys: itemKeys } : {})
    });
  },
  zoteroSyncBibtex() {
    return request<Source[]>("/api/zotero/sync-bibtex", { method: "POST" });
  },
  listSources(search = "") {
    return request<Source[]>(`/api/sources${search ? `?search=${encodeURIComponent(search)}` : ""}`);
  },
  getSource(id: string) {
    return request<Source>(`/api/sources/${id}`);
  },
  listSourceFragments(id: string) {
    return request<Fragment[]>(`/api/sources/${id}/fragments`);
  },
  listTopics() {
    return request<import("../types").Topic[]>("/api/topics");
  },
  createTopic(payload: { title: string; description?: string | null }) {
    return request<import("../types").Topic>("/api/topics", {
      method: "POST",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  updateTopic(id: string, payload: { title?: string; description?: string | null }) {
    return request<import("../types").Topic>(`/api/topics/${id}`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify(payload)
    });
  },
  deleteTopic(id: string) {
    return request<void>(`/api/topics/${id}`, { method: "DELETE" });
  },
  getTopicGraph(id: string) {
    return request<TopicGraph>(`/api/topics/${id}/graph`);
  },
  updateTopicGraphLayout(id: string, positions: Record<string, { fragment_id: string; x: number; y: number }>) {
    return request<TopicGraph>(`/api/topics/${id}/graph-layout`, {
      method: "PATCH",
      headers: jsonHeaders,
      body: JSON.stringify({ positions })
    });
  },
  agentStatus() {
    return request<Record<string, unknown>>("/api/agent/status");
  }
};
