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
  relation_kind: string;
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

export interface Topic {
  id: string;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
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
  title: string;
  objective: string;
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
