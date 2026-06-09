import type { FragmentType, RelationKind } from "../types";

export const relationKinds: RelationKind[] = [
  "depends_on",
  "proof_of",
  "refines",
  "replaces",
  "contradicts",
  "generalizes",
  "is_example_of",
  "is_counterexample_to",
  "uses_notation",
  "questions",
  "compares_with",
  "inspired_by",
];

export const advancedRelationKinds: RelationKind[] = ["compares_with", "inspired_by"];

export const legacyRelationKinds = new Set([
  "uses",
  "proves",
  "specializes_to",
  "cites",
  "quotes",
  "paraphrases",
  "restates",
  "adopts_notation_from",
  "depends_on_notation",
  "generalizes_external_result",
  "specializes_external_result",
  "questions_external_claim",
  "came_from",
]);

export function recommendedRelationKinds(sourceType?: FragmentType | string | null): RelationKind[] {
  if (sourceType === "Question") return ["questions", "depends_on", "refines"];
  if (sourceType === "ProofSketch" || sourceType === "Proof") return ["proof_of", "depends_on", "uses_notation"];
  if (sourceType === "Definition" || sourceType === "ExternalDefinition" || sourceType === "ExternalNotation") {
    return ["depends_on", "uses_notation", "refines", "replaces"];
  }
  if (sourceType === "Example") return ["is_example_of", "depends_on"];
  if (sourceType === "Counterexample") return ["is_counterexample_to", "depends_on"];
  if (["Theorem", "Proposition", "Lemma", "Corollary", "Conjecture", "ExternalTheorem", "LiteratureClaim"].includes(sourceType || "")) {
    return ["depends_on", "generalizes", "contradicts", "refines"];
  }
  return ["depends_on", "refines", "uses_notation"];
}

export function relationKindOptions(sourceType?: FragmentType | string | null, currentKind?: string | null) {
  const recommended = recommendedRelationKinds(sourceType);
  const recommendedSet = new Set(recommended);
  const regular = relationKinds.filter((kind) => !recommendedSet.has(kind) && !advancedRelationKinds.includes(kind));
  const currentLegacy = currentKind && legacyRelationKinds.has(currentKind) ? currentKind : null;
  return {
    recommended,
    regular,
    advanced: advancedRelationKinds,
    currentLegacy,
  };
}

export function isLegacyRelationKind(kind: string) {
  return legacyRelationKinds.has(kind);
}
