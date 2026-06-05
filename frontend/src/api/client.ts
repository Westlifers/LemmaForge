import type {
  ContextPack,
  ContextPackItemInput,
  DuplicateSuggestion,
  Fragment,
  FragmentVersion,
  ImportBatch,
  ImportCommitResult,
  ImportPreview,
  Relation,
  ResearchPatch,
  Source,
  SourcePointer
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

function queryString(filters: FragmentFilters): string {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `?${query}` : "";
}

export const api = {
  listFragments(filters: FragmentFilters = {}) {
    return request<Fragment[]>(`/api/fragments${queryString(filters)}`);
  },
  createFragment(payload: Partial<Fragment>) {
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
  deleteFragment(id: string) {
    return request<void>(`/api/fragments/${id}`, { method: "DELETE" });
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
    objective: string;
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
  zoteroStatus() {
    return request<Record<string, unknown>>("/api/zotero/status");
  },
  zoteroSearch(query: string) {
    return request<{ query: string; results: Array<Record<string, string | null>> }>(
      `/api/zotero/search?query=${encodeURIComponent(query)}`
    );
  },
  zoteroSync() {
    return request<Source[]>("/api/zotero/sync", { method: "POST" });
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
  agentStatus() {
    return request<Record<string, unknown>>("/api/agent/status");
  }
};
