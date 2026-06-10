<template>
  <section class="page problem-graph-page attempt-graph-page">
    <header class="problem-workspace-topbar">
      <div>
        <RouterLink class="text-button" to="/problems">Problems</RouterLink>
        <span class="muted">/</span>
        <RouterLink v-if="workspace" class="text-button" :to="`/problems/${workspace.problem.id}`">
          {{ workspace.problem.title }}
        </RouterLink>
        <span class="muted">/</span>
        <span class="muted">{{ workspace?.attempt.title || "Attempt" }}</span>
        <h1>Attempt Workspace</h1>
        <p>{{ workspace?.attempt.strategy || "Loading attempt..." }}</p>
      </div>
      <div class="toolbar">
        <RouterLink v-if="workspace" class="button subtle" :to="`/problems/${workspace.problem.id}`">
          <Target :size="16" aria-hidden="true" />
          Problem
        </RouterLink>
        <button class="button subtle" type="button" @click="load">
          <RefreshCw :size="16" aria-hidden="true" />
          Refresh
        </button>
        <button class="button danger" type="button" @click="deleteAttemptConfirmOpen = true">
          <Trash2 :size="16" aria-hidden="true" />
          Delete
        </button>
      </div>
    </header>

    <p v-if="message" class="topic-floating-message success-text">{{ message }}</p>
    <p v-if="error" class="topic-floating-message error-text">{{ error }}</p>

    <section v-if="workspace" class="problem-graph-shell attempt-graph-shell">
      <aside class="problem-overview-panel attempt-summary-panel">
        <header>
          <div>
            <h2>Attempt Summary</h2>
            <p>{{ workspace.attempt.id }}</p>
          </div>
          <span class="status" :data-status="workspace.attempt.status">{{ workspace.attempt.status }}</span>
        </header>

        <label>
          Title
          <input v-model="draft.title" />
        </label>
        <label>
          Status
          <select v-model="draft.status">
            <option v-for="status in attemptStatuses" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
        <label>
          Strategy
          <textarea v-model="draft.strategy" rows="4" />
        </label>
        <label>
          Expected Outcome
          <textarea v-model="draft.expected_outcome" rows="3" />
        </label>
        <label>
          Result Summary
          <textarea v-model="draft.result_summary" rows="3" />
        </label>
        <label>
          Failure / Blocking Reason
          <textarea v-model="draft.failure_reason" rows="3" />
        </label>
        <label>
          Next Step
          <textarea v-model="draft.next_step" rows="3" />
        </label>
        <button class="button primary" type="button" :disabled="saving" @click="saveAttempt">
          <Save :size="16" aria-hidden="true" />
          Save Attempt
        </button>
      </aside>

      <main class="problem-main-workspace">
        <div class="problem-view-tabs">
          <button class="button subtle" :class="{ active: viewMode === 'graph' }" type="button" @click="viewMode = 'graph'">
            <Network :size="16" aria-hidden="true" />
            Graph View
          </button>
          <button class="button subtle" :class="{ active: viewMode === 'table' }" type="button" @click="viewMode = 'table'">
            <Table2 :size="16" aria-hidden="true" />
            Table View
          </button>
          <span class="spacer"></span>
          <button class="button subtle" type="button" @click="addDrawerOpen = true">
            <Library :size="16" aria-hidden="true" />
            Add Fragments
          </button>
          <button class="button subtle" type="button" @click="syncFlowElements">
            <GitBranch :size="16" aria-hidden="true" />
            Auto Arrange
          </button>
        </div>

        <section v-if="viewMode === 'graph'" class="problem-graph-stage attempt-graph-stage">
          <VueFlow
            v-model:nodes="nodes"
            v-model:edges="edges"
            class="topic-flow problem-flow attempt-flow"
            :fit-view-on-init="true"
            :default-edge-options="{ type: 'bezier' }"
            @node-click="selectGraphNode"
            @node-drag="refreshDynamicHandles"
            @pane-click="selectedLinkId = ''"
          >
            <template #node-default="{ data }">
              <div class="problem-node-content attempt-node-content" :data-role="data.role || 'attempt'">
                <Handle
                  v-for="position in graphHandlePositions"
                  :id="graphHandleId('target', position)"
                  :key="`target-${position}`"
                  type="target"
                  :position="position"
                />
                <span class="problem-node-icon">
                  <component :is="nodeIcon(data)" :size="18" aria-hidden="true" />
                </span>
                <strong>{{ data.title }}</strong>
                <small>{{ data.subtitle }}</small>
                <span class="chip" :data-chip="data.kind === 'attempt' ? 'ai' : 'topic'">
                  {{ data.role || data.type || "Attempt" }}
                </span>
                <Handle
                  v-for="position in graphHandlePositions"
                  :id="graphHandleId('source', position)"
                  :key="`source-${position}`"
                  type="source"
                  :position="position"
                />
              </div>
            </template>
          </VueFlow>

          <aside v-if="selectedLink" class="problem-floating-inspector">
            <header>
              <div>
                <span class="eyebrow">Attempt Fragment</span>
                <h2>{{ selectedLink.fragment?.title || selectedLink.fragment_id }}</h2>
              </div>
              <button class="icon-button" type="button" aria-label="Close inspector" @click="selectedLinkId = ''">
                <X :size="16" aria-hidden="true" />
              </button>
            </header>
            <MarkdownLatexRenderer v-if="selectedLink.fragment" class="card-tex-preview" :body="selectedLink.fragment.body" />
            <label>
              Role
              <select v-model="selectedLinkDraft.role">
                <option v-for="role in attemptFragmentRoles" :key="role" :value="role">{{ role }}</option>
              </select>
            </label>
            <label>
              Note
              <textarea v-model="selectedLinkDraft.note" rows="3" />
            </label>
            <footer class="action-row">
              <button class="button primary" type="button" @click="saveSelectedLink">Save</button>
              <RouterLink class="button subtle" :to="fragmentDetailLocation(selectedLink.fragment_id)">Open</RouterLink>
              <button class="button danger" type="button" @click="removeFragmentLink(selectedLink.id)">Remove</button>
            </footer>
          </aside>
        </section>

        <section v-else class="plain-section">
          <DashboardTable :headers="['Fragment', 'Attempt Role', 'Fragment Status', 'Note']">
            <tr v-for="link in workspace.fragment_links" :key="link.id">
              <td>{{ link.fragment?.title || link.fragment_id }}</td>
              <td>{{ link.role }}</td>
              <td>{{ link.fragment?.status }}</td>
              <td>{{ link.note || "" }}</td>
            </tr>
          </DashboardTable>
        </section>
      </main>

      <aside class="problem-right-panel attempt-details-panel">
        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Attempt Details</h2>
              <p>Concrete evidence and consequences of this attempt.</p>
            </div>
          </header>
          <div class="attempt-detail-tabs">
            <button class="button subtle active" type="button">Overview</button>
            <button class="button subtle" type="button">Results</button>
            <button class="button subtle" type="button">Links</button>
          </div>
          <dl class="attempt-detail-list">
            <dt>Result Summary</dt>
            <dd>{{ workspace.attempt.result_summary || "No result yet." }}</dd>
            <dt>Blocking Issues</dt>
            <dd>{{ workspace.attempt.failure_reason || "No blocking issue recorded." }}</dd>
            <dt>Next Step</dt>
            <dd>{{ workspace.attempt.next_step || "No next step recorded." }}</dd>
          </dl>
        </section>

        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Produced Fragments</h2>
              <p>{{ producedLinks.length }} generated or revised outputs</p>
            </div>
          </header>
          <article v-for="link in producedLinks" :key="link.id" class="problem-attempt-card">
            <RouterLink class="problem-title-link" :to="fragmentDetailLocation(link.fragment_id)">
              {{ link.fragment?.title || link.fragment_id }}
            </RouterLink>
            <span class="chip" data-chip="topic">{{ link.fragment?.type || "Fragment" }}</span>
          </article>
          <p v-if="!producedLinks.length" class="empty-state">No produced fragments linked yet.</p>
        </section>

        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Affected Items</h2>
              <p>Inputs that need revision or remain blocked.</p>
            </div>
          </header>
          <article v-for="link in affectedLinks" :key="link.id" class="problem-attempt-card">
            <RouterLink class="problem-title-link" :to="fragmentDetailLocation(link.fragment_id)">
              {{ link.fragment?.title || link.fragment_id }}
            </RouterLink>
            <span class="badge warning">{{ link.role }}</span>
          </article>
          <p v-if="!affectedLinks.length" class="empty-state">No affected items marked.</p>
        </section>
      </aside>
    </section>

    <Transition name="drawer-fade">
      <div v-if="addDrawerOpen" class="context-drawer-scrim drawer-click-scrim" @click.self="addDrawerOpen = false">
        <section class="context-drawer topic-add-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">Attempt fragments</span>
              <h2>Add Fragments</h2>
              <p>{{ filteredAvailableFragments.length }} available</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close add fragments drawer" @click="addDrawerOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="problem-drawer-body">
            <label>Search <input v-model="fragmentSearch" placeholder="Title or body..." /></label>
            <label>Role
              <select v-model="fragmentDraft.role">
                <option v-for="role in attemptFragmentRoles" :key="role" :value="role">{{ role }}</option>
              </select>
            </label>
            <article v-for="fragment in filteredAvailableFragments" :key="fragment.id" class="topic-add-candidate">
              <div>
                <strong>{{ fragment.title }}</strong>
                <small>{{ fragment.type }} / {{ fragment.status }}</small>
              </div>
              <button class="button subtle" type="button" @click="addFragmentLink(fragment.id)">Add</button>
            </article>
          </div>
        </section>
      </div>
    </Transition>

    <Transition name="modal-fade">
      <section v-if="deleteAttemptConfirmOpen" class="modal-backdrop" @click.self="deleteAttemptConfirmOpen = false">
        <div class="modal-panel problem-attempt-modal attempt-delete-modal">
          <header>
            <span class="modal-icon danger">
              <Trash2 :size="20" aria-hidden="true" />
            </span>
            <div>
              <h2>Delete attempt?</h2>
              <p>This removes the attempt and its attempt-fragment links. It will not delete fragments.</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close delete confirmation" @click="deleteAttemptConfirmOpen = false">
              <X :size="18" aria-hidden="true" />
            </button>
          </header>
          <section class="attempt-delete-modal-body">
            <strong>{{ workspace?.attempt.title }}</strong>
            <p>
              Deleting is permanent for this attempt record. Linked fragments, problem links,
              topics, and mathematical relations stay untouched.
            </p>
          </section>
          <footer class="action-row">
            <button class="button subtle" type="button" @click="deleteAttemptConfirmOpen = false">Cancel</button>
            <button class="button danger" type="button" @click="deleteAttempt">
              <Trash2 :size="16" aria-hidden="true" />
              Delete Attempt
            </button>
          </footer>
        </div>
      </section>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { Handle, Position, VueFlow, type Edge, type Node, type NodeDragEvent, type NodeMouseEvent } from "@vue-flow/core";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import {
  BookOpen,
  Box,
  FileQuestion,
  GitBranch,
  Library,
  Lightbulb,
  Network,
  Pencil,
  RefreshCw,
  Save,
  Sigma,
  Table2,
  Target,
  Trash2,
  X,
} from "lucide-vue-next";
import DashboardTable from "../components/DashboardTable.vue";
import MarkdownLatexRenderer from "../components/MarkdownLatexRenderer.vue";
import { api } from "../api/client";
import type { AttemptFragmentLink, AttemptFragmentRole, AttemptStatus, AttemptWorkspace, Fragment } from "../types";
import { attemptFragmentRoles, attemptStatuses } from "../types";

const props = defineProps<{ id: string }>();
const router = useRouter();

const workspace = ref<AttemptWorkspace | null>(null);
const allFragments = ref<Fragment[]>([]);
const nodes = ref<Node[]>([]);
const edges = ref<Edge[]>([]);
const viewMode = ref<"graph" | "table">("graph");
const selectedLinkId = ref("");
const addDrawerOpen = ref(false);
const deleteAttemptConfirmOpen = ref(false);
const saving = ref(false);
const message = ref("");
const error = ref("");
const fragmentSearch = ref("");

const draft = reactive({
  title: "",
  status: "planned" as AttemptStatus,
  strategy: "",
  expected_outcome: "",
  result_summary: "",
  failure_reason: "",
  next_step: "",
});
const fragmentDraft = reactive({ role: "input" as AttemptFragmentRole, note: "" });
const selectedLinkDraft = reactive({ role: "input" as AttemptFragmentRole, note: "" });
const graphNodeSize = { width: 238, height: 92 };
const graphHandlePositions = [Position.Left, Position.Right, Position.Top, Position.Bottom];

const selectedLink = computed(() => workspace.value?.fragment_links.find((link) => link.id === selectedLinkId.value) || null);
const linkedFragmentIds = computed(() => new Set(workspace.value?.fragment_links.map((link) => link.fragment_id) || []));
const availableFragments = computed(() => allFragments.value.filter((fragment) => !linkedFragmentIds.value.has(fragment.id)));
const filteredAvailableFragments = computed(() => {
  const needle = fragmentSearch.value.trim().toLowerCase();
  if (!needle) return availableFragments.value;
  return availableFragments.value.filter(
    (fragment) => fragment.title.toLowerCase().includes(needle) || fragment.body.toLowerCase().includes(needle)
  );
});
const producedLinks = computed(() => workspace.value?.fragment_links.filter((link) => link.role === "produced") || []);
const affectedLinks = computed(
  () => workspace.value?.fragment_links.filter((link) => ["blocked_by", "refuted_by", "needs_revision"].includes(String(link.role))) || []
);

async function load() {
  error.value = "";
  const [workspaceResult, fragmentsResult] = await Promise.all([api.getAttemptWorkspace(props.id), api.listFragments()]);
  workspace.value = workspaceResult;
  allFragments.value = fragmentsResult;
  syncDraft(workspaceResult);
  syncFlowElements();
}

function syncDraft(value: AttemptWorkspace) {
  draft.title = value.attempt.title;
  draft.status = value.attempt.status;
  draft.strategy = value.attempt.strategy;
  draft.expected_outcome = value.attempt.expected_outcome || "";
  draft.result_summary = value.attempt.result_summary || "";
  draft.failure_reason = value.attempt.failure_reason || "";
  draft.next_step = value.attempt.next_step || "";
}

function syncFlowElements() {
  if (!workspace.value) return;
  const attemptNodeKey = `attempt:${workspace.value.attempt.id}`;
  const generatedNodes: Node[] = [
    {
      id: attemptNodeKey,
      type: "default",
      position: { x: 460, y: 170 },
      data: {
        kind: "attempt",
        title: workspace.value.attempt.title,
        subtitle: workspace.value.attempt.status,
      },
      class: "problem-workspace-node problem-root-node attempt-root-node",
    },
  ];

  const grouped = groupedLinks();
  for (const [role, links] of grouped.entries()) {
    const column = roleColumn(role);
    links.forEach((link, index) => {
      generatedNodes.push({
        id: fragmentNodeKey(link),
        type: "default",
        position: { x: column.x, y: column.y + index * 132 },
        data: {
          kind: "fragment",
          title: link.fragment?.title || link.fragment_id,
          subtitle: link.fragment?.type || "Fragment",
          type: link.fragment?.type,
          role: link.role,
        },
        class: `problem-workspace-node problem-fragment-node attempt-fragment-node role-${link.role}`,
      });
    });
  }

  const positionsById = positionsFromNodes(generatedNodes);
  const roleEdges: Edge[] = workspace.value.fragment_links.map((link) => dynamicEdge({
    id: `attempt-role-${link.id}`,
    source: attemptNodeKey,
    target: fragmentNodeKey(link),
    label: link.role,
    animated: ["blocked_by", "refuted_by", "needs_revision"].includes(String(link.role)),
    class: "problem-role-edge",
    style: { stroke: roleColor(String(link.role)), strokeWidth: 2.1 },
    labelStyle: { fill: roleColor(String(link.role)), fontWeight: 800 },
    labelBgStyle: { fill: "var(--surface)", stroke: roleColor(String(link.role)) },
  }, positionsById));

  const linkByFragment = new Map(workspace.value.fragment_links.map((link) => [link.fragment_id, link]));
  const relationEdges: Edge[] = workspace.value.relations
    .flatMap((relation) => {
      const sourceLink = linkByFragment.get(relation.source_fragment_id);
      const targetLink = linkByFragment.get(relation.target_fragment_id);
      if (!sourceLink || !targetLink) return [];
      return [dynamicEdge({
        id: relation.id,
        source: fragmentNodeKey(sourceLink),
        target: fragmentNodeKey(targetLink),
        label: relation.relation_kind,
        class: "problem-math-edge",
        style: { stroke: "#5d7fa8", strokeWidth: 1.8, strokeDasharray: "5 4" },
        labelBgStyle: { fill: "var(--surface)", stroke: "#5d7fa8" },
      } as Edge, positionsById)];
    });

  nodes.value = generatedNodes;
  edges.value = [...roleEdges, ...relationEdges];
  syncSelectedDraft();
}

function groupedLinks() {
  const groups = new Map<string, AttemptFragmentLink[]>();
  for (const link of workspace.value?.fragment_links || []) {
    groups.set(String(link.role), [...(groups.get(String(link.role)) || []), link]);
  }
  return groups;
}

function roleColumn(role: string) {
  const columns: Record<string, { x: number; y: number }> = {
    input: { x: 80, y: 70 },
    assumption: { x: 80, y: 230 },
    motivated: { x: 80, y: 390 },
    other: { x: 420, y: 440 },
    produced: { x: 820, y: 90 },
    blocked_by: { x: 1090, y: 90 },
    refuted_by: { x: 1090, y: 250 },
    needs_revision: { x: 1090, y: 410 },
  };
  return columns[role] || { x: 460, y: 520 };
}

function fragmentNodeKey(link: AttemptFragmentLink) {
  return `attempt_link:${link.id}`;
}

function selectGraphNode(event: NodeMouseEvent) {
  const nodeId = event.node.id;
  if (!nodeId.startsWith("attempt_link:")) {
    selectedLinkId.value = "";
    return;
  }
  selectedLinkId.value = nodeId.replace("attempt_link:", "");
  syncSelectedDraft();
}

function refreshDynamicHandles(event?: NodeDragEvent) {
  const draggedNode = event?.node;
  const positionsById = positionsFromCurrentNodes(
    draggedNode?.id && draggedNode.position
      ? { [draggedNode.id]: { x: draggedNode.position.x, y: draggedNode.position.y } }
      : {}
  );
  const nextNodes: Node[] = [];
  nodes.value.forEach((node) => {
    nextNodes.push({
      ...node,
      position: positionsById[node.id] || node.position,
    } as Node);
  });
  const nextEdges: Edge[] = [];
  edges.value.forEach((edge) => {
    nextEdges.push(dynamicEdge(edge as Edge, positionsById));
  });
  nodes.value = nextNodes;
  edges.value = nextEdges;
}

function dynamicEdge(edge: Edge, positions: Record<string, { x: number; y: number }>): Edge {
  const handles = relationHandlesForNodes(edge.source, edge.target, positions);
  return {
    ...edge,
    type: "bezier",
    sourceHandle: handles.sourceHandle,
    targetHandle: handles.targetHandle,
  };
}

function positionsFromNodes(items: Node[]) {
  const positions: Record<string, { x: number; y: number }> = {};
  items.forEach((node) => {
    positions[node.id] = { x: node.position.x, y: node.position.y };
  });
  return positions;
}

function positionsFromCurrentNodes(overrides: Record<string, { x: number; y: number }> = {}) {
  const positions: Record<string, { x: number; y: number }> = {};
  nodes.value.forEach((node) => {
    positions[node.id] = { x: node.position.x, y: node.position.y };
  });
  Object.assign(positions, overrides);
  return positions;
}

function relationHandlesForNodes(sourceId: string, targetId: string, positions: Record<string, { x: number; y: number }>) {
  const sourcePosition = positions[sourceId];
  const targetPosition = positions[targetId];
  if (!sourcePosition || !targetPosition) {
    return {
      sourceHandle: graphHandleId("source", Position.Right),
      targetHandle: graphHandleId("target", Position.Left),
    };
  }
  const sourceSide = sideFacing(sourcePosition, targetPosition);
  const targetSide = oppositePosition(sourceSide);
  return {
    sourceHandle: graphHandleId("source", sourceSide),
    targetHandle: graphHandleId("target", targetSide),
  };
}

function sideFacing(source: { x: number; y: number }, target: { x: number; y: number }) {
  const sourceCenter = nodeCenter(source);
  const targetCenter = nodeCenter(target);
  const dx = targetCenter.x - sourceCenter.x;
  const dy = targetCenter.y - sourceCenter.y;
  if (Math.abs(dx) >= Math.abs(dy)) {
    return dx >= 0 ? Position.Right : Position.Left;
  }
  return dy >= 0 ? Position.Bottom : Position.Top;
}

function oppositePosition(position: Position) {
  if (position === Position.Left) return Position.Right;
  if (position === Position.Right) return Position.Left;
  if (position === Position.Top) return Position.Bottom;
  return Position.Top;
}

function nodeCenter(position: { x: number; y: number }) {
  return {
    x: position.x + graphNodeSize.width / 2,
    y: position.y + graphNodeSize.height / 2,
  };
}

function graphHandleId(type: "source" | "target", position: Position) {
  return `${type}-${position}`;
}

function syncSelectedDraft() {
  if (!selectedLink.value) return;
  selectedLinkDraft.role = selectedLink.value.role as AttemptFragmentRole;
  selectedLinkDraft.note = selectedLink.value.note || "";
}

async function saveAttempt() {
  if (!workspace.value) return;
  saving.value = true;
  try {
    await api.updateAttempt(workspace.value.attempt.id, {
      title: draft.title,
      status: draft.status,
      strategy: draft.strategy,
      expected_outcome: draft.expected_outcome || null,
      result_summary: draft.result_summary || null,
      failure_reason: draft.failure_reason || null,
      next_step: draft.next_step || null,
    });
    message.value = "Attempt saved.";
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  } finally {
    saving.value = false;
  }
}

async function addFragmentLink(fragmentId: string) {
  if (!workspace.value) return;
  try {
    await api.addAttemptFragment(workspace.value.attempt.id, {
      fragment_id: fragmentId,
      role: fragmentDraft.role,
      note: fragmentDraft.note || null,
    });
    message.value = "Fragment linked to attempt.";
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function saveSelectedLink() {
  if (!workspace.value || !selectedLink.value) return;
  await api.updateAttemptFragment(workspace.value.attempt.id, selectedLink.value.id, {
    role: selectedLinkDraft.role,
    note: selectedLinkDraft.note || null,
  });
  message.value = "Attempt fragment role saved.";
  await load();
}

async function removeFragmentLink(linkId: string) {
  if (!workspace.value) return;
  await api.removeAttemptFragment(workspace.value.attempt.id, linkId);
  selectedLinkId.value = "";
  message.value = "Fragment removed from attempt.";
  await load();
}

async function deleteAttempt() {
  if (!workspace.value) return;
  const problemId = workspace.value.problem.id;
  await api.deleteAttempt(workspace.value.attempt.id);
  await router.push(`/problems/${problemId}`);
}

function fragmentDetailLocation(fragmentId: string) {
  return {
    path: `/fragments/${fragmentId}`,
    query: { from: `/attempts/${props.id}`, from_label: workspace.value?.attempt.title || "Attempt" },
  };
}

function roleColor(role: string) {
  if (role === "input" || role === "assumption" || role === "motivated") return "#0f9f8f";
  if (role === "produced") return "#3178d4";
  if (role === "blocked_by" || role === "refuted_by" || role === "needs_revision") return "#d88916";
  return "#7b61d1";
}

function nodeIcon(data: Record<string, string>) {
  if (data.kind === "attempt") return Target;
  if (data.role === "blocked_by" || data.role === "refuted_by" || data.type === "Question") return FileQuestion;
  if (data.role === "input" || data.role === "assumption" || data.type === "Definition") return BookOpen;
  if (data.role === "produced" || data.type === "Theorem" || data.type === "Proposition") return Sigma;
  if (data.type === "ProofSketch" || data.type === "Proof") return Pencil;
  if (data.type === "Construction") return Box;
  return Lightbulb;
}

onMounted(() => {
  void load();
});
</script>
