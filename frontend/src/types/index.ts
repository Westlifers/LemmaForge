export type FragmentType =
  | "Definition"
  | "Proposition"
  | "Lemma"
  | "Theorem"
  | "Corollary"
  | "Proof"
  | "ProofSketch"
  | "Example"
  | "Counterexample"
  | "Construction"
  | "Question"
  | "Conjecture"
  | "Remark"
  | "TODO"
  | "PaperNote"
  | "ReadingNote"
  | "ExternalDefinition"
  | "ExternalTheorem"
  | "ExternalNotation"
  | "LiteratureClaim"
  | "ContextNote";

export type FragmentStatus =
  | "draft"
  | "raw"
  | "candidate"
  | "working"
  | "stable"
  | "superseded"
  | "rejected";

export type OriginClassification =
  | "user_original"
  | "assistant_generated"
  | "external_source"
  | "mixed"
  | "unknown";

export type Exactness =
  | "quote"
  | "close_paraphrase"
  | "paraphrase"
  | "interpretation"
  | "reconstruction"
  | "original";

export type RelationKind =
  | "depends_on"
  | "proof_of"
  | "refines"
  | "replaces"
  | "contradicts"
  | "generalizes"
  | "is_example_of"
  | "is_counterexample_to"
  | "uses_notation"
  | "questions"
  | "compares_with"
  | "inspired_by";

export interface Fragment {
  id: string;
  type: FragmentType;
  title: string;
  status: FragmentStatus;
  body: string;
  topic_id: string | null;
  origin_classification: OriginClassification;
  exactness: Exactness;
  current_version_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppHealth {
  ok: boolean;
  storage?: {
    database_bytes: number;
    vault_bytes: number;
    app_bytes: number;
    disk_total_bytes: number;
    disk_free_bytes: number;
  };
}

export interface FragmentVersion {
  id: string;
  fragment_id: string;
  version_number: number;
  body: string;
  change_note: string | null;
  created_at: string;
}

export interface Relation {
  id: string;
  source_fragment_id: string;
  relation_kind: RelationKind | string;
  target_fragment_id: string;
  confidence: number | null;
  created_at: string;
}

export interface SourcePointer {
  id: string;
  fragment_id: string;
  source_id: string;
  locator: string | null;
  exactness: Exactness;
  quote_text: string | null;
  note: string | null;
}

export interface Source {
  id: string;
  source_type: string;
  title: string;
  authors: string | null;
  year: number | null;
  citekey: string | null;
  zotero_item_key: string | null;
  url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ZoteroStatus {
  configured: boolean;
  running: boolean;
  local_api_available: boolean;
  base_url: string;
  library_id: number | null;
  library_name: string | null;
  error: string | null;
  references_bib: string;
  references_exists: boolean;
}

export interface ZoteroCreator {
  firstName?: string;
  lastName?: string;
  name?: string;
  creatorType?: string;
}

export interface ZoteroAttachment {
  key: string | null;
  title: string | null;
  content_type: string | null;
  filename: string | null;
  url: string | null;
}

export interface ZoteroItem {
  key: string;
  version: number | null;
  item_type: string | null;
  title: string;
  creators: ZoteroCreator[];
  creator_summary: string | null;
  date: string | null;
  year: number | null;
  url: string | null;
  doi: string | null;
  abstract_note: string | null;
  citation_key: string | null;
  collections: string[];
  tags: Array<{ tag?: string; type?: number }>;
  attachment_count: number;
  attachments: ZoteroAttachment[];
  zotero_url: string | null;
}

export interface ZoteroSearchResult {
  query: string;
  available: boolean;
  error: string | null;
  results: ZoteroItem[];
}

export interface ZoteroItemResult {
  available: boolean;
  error: string | null;
  item: ZoteroItem | null;
}

export interface ZoteroSyncResult {
  available: boolean;
  synced_count: number;
  sources: Source[];
  error: string | null;
}

export interface Topic {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export type ProblemStatus = "open" | "active" | "blocked" | "partially_solved" | "solved" | "abandoned";
export type AttemptStatus = "planned" | "in_progress" | "succeeded" | "failed" | "blocked" | "superseded";

export type ProblemFragmentRole =
  | "main_question"
  | "active_definition"
  | "candidate_definition"
  | "claim"
  | "proof"
  | "example"
  | "counterexample"
  | "background"
  | "source_note"
  | "gap"
  | "result"
  | "notation"
  | "other";

export type AttemptFragmentRole =
  | "input"
  | "assumption"
  | "produced"
  | "blocked_by"
  | "motivated"
  | "refuted_by"
  | "needs_revision"
  | "other";

export interface ProblemTopicLink {
  id: string;
  problem_id: string;
  topic_id: string;
  created_at: string;
  topic: Topic | null;
}

export interface ProblemFragmentLink {
  id: string;
  problem_id: string;
  fragment_id: string;
  role: ProblemFragmentRole | string;
  note: string | null;
  created_at: string;
  fragment: Fragment | null;
}

export interface ProblemGraphNodePosition {
  node_key: string;
  x: number;
  y: number;
}

export interface AttemptFragmentLink {
  id: string;
  attempt_id: string;
  fragment_id: string;
  role: AttemptFragmentRole | string;
  note: string | null;
  created_at: string;
  fragment: Fragment | null;
}

export interface Attempt {
  id: string;
  problem_id: string;
  title: string;
  status: AttemptStatus;
  strategy: string;
  expected_outcome: string | null;
  result_summary: string | null;
  failure_reason: string | null;
  next_step: string | null;
  created_at: string;
  updated_at: string;
  fragment_links: AttemptFragmentLink[];
}

export interface ResearchProblem {
  id: string;
  title: string;
  status: ProblemStatus;
  objective: string;
  current_formulation: string | null;
  motivation: string | null;
  why_it_matters: string | null;
  created_at: string;
  updated_at: string;
  topic_links: ProblemTopicLink[];
  fragment_links: ProblemFragmentLink[];
  attempts: Attempt[];
}

export interface ProblemWorkspace {
  problem: ResearchProblem;
  topic_links: ProblemTopicLink[];
  fragment_links: ProblemFragmentLink[];
  relations: Relation[];
  attempts: Attempt[];
  positions: Record<string, ProblemGraphNodePosition>;
}

export interface AttemptWorkspace {
  attempt: Attempt;
  problem: ResearchProblem;
  fragment_links: AttemptFragmentLink[];
  relations: Relation[];
}

export interface ProblemSuggestedFragmentRole {
  fragment_id: string;
  role: ProblemFragmentRole;
  note: string | null;
}

export interface ProblemSummaryProposal {
  title: string;
  objective: string;
  current_formulation: string | null;
  motivation: string | null;
  why_it_matters: string | null;
  suggested_fragment_roles: ProblemSuggestedFragmentRole[];
  open_gaps: string[];
  warnings: string[];
}

export interface ProblemSummaryRequest {
  topic_ids: string[];
  fragment_ids: string[];
  title_hint?: string | null;
  objective_hint?: string | null;
  timeout_seconds?: number;
}

export interface ProblemSummaryResult {
  available: boolean;
  proposal: ProblemSummaryProposal | null;
  error: string | null;
  logs: string[];
}

export interface ProblemSummaryJob {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  logs: string[];
  result: ProblemSummaryResult | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface TopicGraphNodePosition {
  fragment_id: string;
  x: number;
  y: number;
}

export interface TopicGraph {
  topic: Topic;
  fragments: Fragment[];
  relations: Relation[];
  positions: Record<string, TopicGraphNodePosition>;
}

export interface ResearchPatch {
  patch_type: "ResearchPatch";
  metadata: {
    source_kind: string;
    topic_hint?: string | null;
    created_by: string;
    requires_user_review: true;
  };
  fragments: Array<{
    local_id: string;
    type: FragmentType;
    title: string;
    status: "raw" | "candidate";
    origin_classification: OriginClassification;
    exactness: Exactness;
    body: string;
    assumptions: string[];
    conclusion: string | null;
    confidence: number | null;
    source_excerpt: string | null;
  }>;
  relations: Array<{
    source: string;
    kind: string;
    target: string;
    confidence?: number | null;
  }>;
  source_pointers: Array<{
    fragment_local_id: string;
    citekey?: string | null;
    source?: {
      source_type: string;
      title?: string | null;
      authors?: string | null;
      year?: number | null;
      citekey?: string | null;
      zotero_item_key?: string | null;
      url?: string | null;
    } | null;
    locator?: string | null;
    exactness: Exactness;
    quote_text?: string | null;
    note?: string | null;
  }>;
  warnings: string[];
}

export interface ImportPreview {
  valid: boolean;
  fragment_count: number;
  relation_count: number;
  source_pointer_count: number;
  warnings: string[];
  patch: ResearchPatch;
}

export interface ImportCommitResult {
  fragment_ids: string[];
  relation_ids: string[];
  source_pointer_ids: string[];
  warnings: string[];
}

export type ImportBatchStatus = "draft" | "validated" | "committed" | "rejected";

export interface ImportBatch {
  id: string;
  status: ImportBatchStatus;
  raw_excerpt: string;
  topic_hint: string | null;
  citekey: string | null;
  locator: string | null;
  patch: ResearchPatch | null;
  warnings: string[];
  commit_result: ImportCommitResult | null;
  ai_draft_result: AIDraftCreationResult | null;
  relation_proposals: AIRelationProposal[];
  review_note: string | null;
  created_at: string;
  updated_at: string;
  reviewed_at: string | null;
}

export interface AIExtractRequest {
  raw_excerpt: string;
  topic_hint?: string | null;
  citekey?: string | null;
  locator?: string | null;
  source_kind?: string;
  timeout_seconds?: number;
}

export interface AIExtractResult {
  available: boolean;
  preview: ImportPreview | null;
  batch: ImportBatch | null;
  error: string | null;
  logs: string[];
}

export interface AIExtractJob {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  logs: string[];
  result: AIExtractResult | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface AICreateDraftsRequest {
  batch_id?: string | null;
  patch?: ResearchPatch | null;
  raw_excerpt?: string;
  topic_hint?: string | null;
  citekey?: string | null;
  locator?: string | null;
  selected_local_ids?: string[] | null;
}

export interface AIDraftCreationResult {
  batch_id: string;
  fragment_ids: string[];
  local_to_fragment_id: Record<string, string>;
  source_pointer_ids: string[];
  relation_proposals: AIRelationProposal[];
  warnings: string[];
}

export interface AIRelationProposal {
  proposal_id: string;
  source: string;
  kind: string;
  target: string;
  confidence: number | null;
  source_fragment_id: string | null;
  target_fragment_id: string | null;
  applied_relation_id: string | null;
}

export interface AIApplyRelationsResult {
  batch_id: string;
  relation_ids: string[];
  relation_proposals: AIRelationProposal[];
  warnings: string[];
}

export interface DuplicateSuggestion {
  local_id: string;
  fragment_id: string;
  title: string;
  type: string;
  status: string;
  origin_classification: string;
  exactness: string;
  score: number;
  reason: string;
}

export interface ContextPackItemInput {
  fragment_id: string;
  order_index: number;
  reason?: string | null;
}

export interface ContextPack {
  id: string;
  topic_id: string | null;
  title: string;
  objective: string;
  task_prompt: string | null;
  body: string;
  created_at: string;
  updated_at: string;
  items: Array<{
    context_pack_id: string;
    fragment_id: string;
    order_index: number;
    reason: string | null;
  }>;
}

export interface ContextPackSuggestionItem {
  fragment_id: string;
  order_index: number;
  reason: string;
}

export interface ContextPackSuggestion {
  topic_id: string;
  objective: string;
  task_prompt: string;
  items: ContextPackSuggestionItem[];
  warnings: string[];
  missing_context_questions: string[];
}

export interface ContextPackSuggestRequest {
  topic_id: string;
  objective: string;
  task_prompt: string;
  timeout_seconds?: number;
}

export interface ContextPackSuggestResult {
  available: boolean;
  suggestion: ContextPackSuggestion | null;
  error: string | null;
  logs: string[];
}

export interface ContextPackSuggestJob {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed";
  logs: string[];
  result: ContextPackSuggestResult | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export const fragmentTypes: FragmentType[] = [
  "Definition",
  "Proposition",
  "Lemma",
  "Theorem",
  "Corollary",
  "Proof",
  "ProofSketch",
  "Example",
  "Counterexample",
  "Construction",
  "Question",
  "Conjecture",
  "Remark",
  "TODO",
  "PaperNote",
  "ReadingNote",
  "ExternalDefinition",
  "ExternalTheorem",
  "ExternalNotation",
  "LiteratureClaim",
  "ContextNote"
];

export const fragmentStatuses: FragmentStatus[] = [
  "draft",
  "raw",
  "candidate",
  "working",
  "stable",
  "superseded",
  "rejected"
];

export const unacceptedFragmentStatuses: FragmentStatus[] = ["draft", "raw", "candidate"];
export const acceptedFragmentStatuses: FragmentStatus[] = ["working", "stable", "superseded"];

export const problemStatuses: ProblemStatus[] = [
  "open",
  "active",
  "blocked",
  "partially_solved",
  "solved",
  "abandoned"
];

export const problemFragmentRoles: ProblemFragmentRole[] = [
  "main_question",
  "active_definition",
  "candidate_definition",
  "claim",
  "proof",
  "example",
  "counterexample",
  "background",
  "source_note",
  "gap",
  "result",
  "notation",
  "other"
];

export const attemptStatuses: AttemptStatus[] = [
  "planned",
  "in_progress",
  "succeeded",
  "failed",
  "blocked",
  "superseded"
];

export const attemptFragmentRoles: AttemptFragmentRole[] = [
  "input",
  "assumption",
  "produced",
  "blocked_by",
  "motivated",
  "refuted_by",
  "needs_revision",
  "other"
];
