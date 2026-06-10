<template>
  <section class="page problem-graph-page">
    <header class="problem-workspace-topbar">
      <div>
        <RouterLink class="text-button" to="/problems">Problems</RouterLink>
        <span class="muted">/</span>
        <span class="muted">{{ problem?.title || "Workspace" }}</span>
        <h1>Problem Workspace</h1>
        <p>{{ problem?.objective || "Loading problem..." }}</p>
      </div>
      <div class="toolbar">
        <button class="button subtle" type="button" @click="aiPanelOpen = !aiPanelOpen">
          <Sparkles :size="16" aria-hidden="true" />
          AI Assistant
        </button>
        <button class="button primary" type="button" @click="attemptModalOpen = true">
          <Plus :size="16" aria-hidden="true" />
          New Attempt{{ selectedProblemLinkIds.length ? ` (${selectedProblemLinkIds.length})` : "" }}
        </button>
        <button class="button subtle" type="button" @click="load">
          <RefreshCw :size="16" aria-hidden="true" />
          Refresh
        </button>
      </div>
    </header>

    <p v-if="message" class="topic-floating-message success-text">{{ message }}</p>
    <p v-if="error" class="topic-floating-message error-text">{{ error }}</p>

    <section v-if="workspace && problem" class="problem-graph-shell" :class="{ 'without-right-panel': !detailsPanelOpen }">
      <aside class="problem-overview-panel">
        <header>
          <div>
            <h2>Problem Overview</h2>
            <p>{{ problem.id }}</p>
          </div>
          <button class="button subtle" type="button" @click="editDrawerOpen = true">Edit</button>
        </header>
        <dl>
          <dt>Title</dt>
          <dd>{{ problem.title }}</dd>
          <dt>Status</dt>
          <dd><span class="status" :data-status="problem.status">{{ problem.status }}</span></dd>
          <dt>Objective</dt>
          <dd>{{ problem.objective }}</dd>
          <dt>Current Formulation</dt>
          <dd>{{ problem.current_formulation || "No current formulation recorded." }}</dd>
        </dl>
        <section class="problem-key-items">
          <h3>Key Items</h3>
          <p><strong>{{ countRole("active_definition") }}</strong> active definitions</p>
          <p><strong>{{ countRole("claim") }}</strong> key claims</p>
          <p><strong>{{ countRole("gap") + countRole("main_question") }}</strong> open questions</p>
          <p><strong>{{ workspace.topic_links.length }}</strong> topics</p>
        </section>
      </aside>

      <main class="problem-main-workspace">
        <div class="problem-view-tabs">
          <button class="button subtle" :class="{ active: viewMode === 'graph' }" type="button" @click="viewMode = 'graph'">
            <Network :size="16" aria-hidden="true" />
            Graph View
          </button>
          <button class="button subtle" :class="{ active: viewMode === 'timeline' }" type="button" @click="viewMode = 'timeline'">
            <ListChecks :size="16" aria-hidden="true" />
            Timeline View
          </button>
          <button class="button subtle" :class="{ active: viewMode === 'table' }" type="button" @click="viewMode = 'table'">
            <Table2 :size="16" aria-hidden="true" />
            Table View
          </button>
          <span class="spacer"></span>
          <button v-if="viewMode === 'graph'" class="button subtle" type="button" @click="graphControlsOpen = !graphControlsOpen">
            <SlidersHorizontal :size="16" aria-hidden="true" />
            Graph Controls
          </button>
          <button class="button subtle" :class="{ active: detailsPanelOpen }" type="button" @click="detailsPanelOpen = !detailsPanelOpen">
            <PanelRight :size="16" aria-hidden="true" />
            Details
          </button>
          <button class="button subtle" type="button" @click="addDrawerOpen = true">
            <Library :size="16" aria-hidden="true" />
            Add Fragments
          </button>
          <button class="button subtle" type="button" @click="topicDrawerOpen = true">
            <Tags :size="16" aria-hidden="true" />
            Topics
          </button>
        </div>

        <section v-if="viewMode === 'graph'" class="problem-graph-stage">
          <Transition name="popover">
            <div v-if="graphControlsOpen" class="problem-graph-controls-panel">
              <header>
                <div>
                  <span class="eyebrow">Graph Controls</span>
                  <strong>Visibility & layout</strong>
                </div>
                <button class="icon-button" type="button" aria-label="Close graph controls" @click="graphControlsOpen = false">
                  <X :size="15" aria-hidden="true" />
                </button>
              </header>
              <div class="problem-edge-filter-group" aria-label="Graph edge visibility">
                <button
                  class="button subtle compact"
                  :class="{ active: showProblemRoleEdges }"
                  type="button"
                  @click="toggleProblemRoleEdges"
                >
                  <Eye v-if="showProblemRoleEdges" :size="15" aria-hidden="true" />
                  <EyeOff v-else :size="15" aria-hidden="true" />
                  Role links
                </button>
                <button
                  class="button subtle compact"
                  :class="{ active: showMathRelationEdges }"
                  type="button"
                  @click="toggleMathRelationEdges"
                >
                  <Eye v-if="showMathRelationEdges" :size="15" aria-hidden="true" />
                  <EyeOff v-else :size="15" aria-hidden="true" />
                  Math relations
                </button>
              </div>
              <button class="button primary" type="button" @click="autoArrange">
                <GitBranch :size="16" aria-hidden="true" />
                Auto Arrange
              </button>
            </div>
          </Transition>
          <VueFlow
            v-model:nodes="nodes"
            v-model:edges="edges"
            class="topic-flow problem-flow"
            :fit-view-on-init="true"
            :default-edge-options="{ type: 'bezier' }"
            @node-click="selectGraphNode"
            @node-drag="refreshDynamicHandles"
            @node-drag-stop="saveLayout"
            @pane-click="selectedLinkId = ''"
          >
            <template #node-default="{ data }">
              <div class="problem-node-content" :data-role="data.role || 'problem'">
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
                <span class="chip" :data-chip="data.kind === 'problem' ? 'ai' : 'topic'">
                  {{ data.role || data.type || "Problem" }}
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
                <span class="eyebrow">Fragment in Problem</span>
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
                <option v-for="role in problemFragmentRoles" :key="role" :value="role">{{ role }}</option>
              </select>
            </label>
            <label>
              Note
              <textarea v-model="selectedLinkDraft.note" rows="3" />
            </label>
            <footer class="action-row">
              <button class="button primary" type="button" @click="saveSelectedLink">Save</button>
              <button class="button subtle" type="button" :class="{ active: selectedProblemLinkSet.has(selectedLink.id) }" @click="toggleProblemLinkSelection(selectedLink.id)">
                <CheckSquare v-if="selectedProblemLinkSet.has(selectedLink.id)" :size="16" aria-hidden="true" />
                <Square v-else :size="16" aria-hidden="true" />
                Input
              </button>
              <RouterLink class="button subtle" :to="`/fragments/${selectedLink.fragment_id}?from=/problems/${problem.id}`">Open</RouterLink>
              <button class="button danger" type="button" @click="removeFragmentLink(selectedLink.id)">Remove</button>
            </footer>
          </aside>
        </section>

        <section v-else-if="viewMode === 'timeline'" class="plain-section problem-timeline-view">
          <article v-for="attempt in workspace.attempts" :key="attempt.id" class="problem-timeline-item">
            <span class="status" :data-status="attempt.status">{{ attempt.status }}</span>
            <RouterLink :to="`/attempts/${attempt.id}`">{{ attempt.title }}</RouterLink>
            <p>{{ attempt.strategy }}</p>
          </article>
          <p v-if="!workspace.attempts.length" class="empty-state">No attempts yet.</p>
        </section>

        <section v-else class="plain-section">
          <DashboardTable :headers="['Use', 'Fragment', 'Role', 'Status', 'Note']">
            <tr v-for="link in workspace.fragment_links" :key="link.id">
              <td>
                <button class="icon-button" type="button" :aria-label="`Use ${link.fragment?.title || link.fragment_id} in new attempt`" @click="toggleProblemLinkSelection(link.id)">
                  <CheckSquare v-if="selectedProblemLinkSet.has(link.id)" :size="15" aria-hidden="true" />
                  <Square v-else :size="15" aria-hidden="true" />
                </button>
              </td>
              <td>{{ link.fragment?.title || link.fragment_id }}</td>
              <td>{{ link.role }}</td>
              <td>{{ link.fragment?.status }}</td>
              <td>{{ link.note || "" }}</td>
            </tr>
          </DashboardTable>
        </section>
      </main>

      <aside v-if="detailsPanelOpen" class="problem-right-panel">
        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Open Gaps & Next Steps</h2>
              <p>Derived from problem roles and active attempts.</p>
            </div>
          </header>
          <div class="problem-gap-list">
            <p v-for="link in gapLinks" :key="link.id">
              <span class="badge">{{ link.role }}</span>
              {{ link.fragment?.title || link.note || link.fragment_id }}
            </p>
            <p v-for="attempt in blockedAttempts" :key="attempt.id">
              <span class="badge warning">{{ attempt.status }}</span>
              {{ attempt.next_step || attempt.failure_reason || attempt.title }}
            </p>
            <p v-if="!gapLinks.length && !blockedAttempts.length" class="muted">No explicit gaps recorded.</p>
          </div>
        </section>

        <section class="plain-section">
          <header class="section-header">
            <div>
              <h2>Active Attempts</h2>
              <p>{{ workspace.attempts.length }} attempts for this problem</p>
            </div>
          </header>
          <article v-for="attempt in workspace.attempts" :key="attempt.id" class="problem-attempt-card">
            <RouterLink class="problem-title-link" :to="`/attempts/${attempt.id}`">{{ attempt.title }}</RouterLink>
            <span class="status" :data-status="attempt.status">{{ attempt.status }}</span>
            <p>{{ attempt.next_step || attempt.strategy }}</p>
          </article>
          <p v-if="!workspace.attempts.length" class="empty-state">No attempts yet.</p>
        </section>

        <section v-if="aiPanelOpen" class="plain-section">
          <header class="section-header">
            <div>
              <h2>AI Proposal</h2>
              <p>Codex proposes formulation and fragment roles.</p>
            </div>
          </header>
          <label>
            Title hint
            <input v-model="aiRequest.title_hint" />
          </label>
          <label>
            Objective hint
            <textarea v-model="aiRequest.objective_hint" rows="3" />
          </label>
          <button class="button primary" type="button" :disabled="aiBusy" @click="suggestProblem">
            <Sparkles :size="16" aria-hidden="true" />
            Suggest Summary
          </button>
          <p v-if="aiError" class="error-text">{{ aiError }}</p>
          <article v-if="proposal" class="problem-proposal-card">
            <header>
              <h3>{{ proposal.title }}</h3>
              <button class="button danger" type="button" @click="discardProposal">Discard</button>
            </header>
            <p>{{ proposal.objective }}</p>
            <div class="action-row">
              <button class="button subtle" type="button" @click="applyProposalFields">Apply Fields</button>
              <button class="button primary" type="button" @click="applySuggestedRoles">Apply Roles</button>
            </div>
          </article>
        </section>
      </aside>
    </section>

    <Transition name="drawer-fade">
      <div v-if="editDrawerOpen" class="context-drawer-scrim drawer-click-scrim" @click.self="editDrawerOpen = false">
        <section class="context-drawer topic-add-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">Problem</span>
              <h2>Edit Problem</h2>
            </div>
            <button class="icon-button" type="button" aria-label="Close edit drawer" @click="editDrawerOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="problem-drawer-body">
            <label>Title <input v-model="draft.title" /></label>
            <label>Status
              <select v-model="draft.status">
                <option v-for="status in problemStatuses" :key="status" :value="status">{{ status }}</option>
              </select>
            </label>
            <label>Objective <textarea v-model="draft.objective" rows="4" /></label>
            <label>Current formulation <textarea v-model="draft.current_formulation" rows="5" /></label>
            <label>Motivation <textarea v-model="draft.motivation" rows="3" /></label>
            <label>Why it matters <textarea v-model="draft.why_it_matters" rows="3" /></label>
            <button class="button primary" type="button" :disabled="saving" @click="saveProblem">Save Problem</button>
          </div>
        </section>
      </div>
    </Transition>

    <Transition name="drawer-fade">
      <div v-if="addDrawerOpen" class="context-drawer-scrim drawer-click-scrim" @click.self="addDrawerOpen = false">
        <section class="context-drawer topic-add-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">Problem fragments</span>
              <h2>Add Fragments</h2>
              <p>{{ availableFragments.length }} available</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close add fragments drawer" @click="addDrawerOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="problem-drawer-body">
            <label>Search <input v-model="fragmentSearch" placeholder="Title or body..." /></label>
            <label>Role
              <select v-model="fragmentDraft.role">
                <option v-for="role in problemFragmentRoles" :key="role" :value="role">{{ role }}</option>
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

    <Transition name="drawer-fade">
      <div v-if="topicDrawerOpen" class="context-drawer-scrim drawer-click-scrim" @click.self="topicDrawerOpen = false">
        <section class="context-drawer topic-add-drawer">
          <header class="section-header context-drawer-header">
            <div>
              <span class="eyebrow">Problem topics</span>
              <h2>Linked Topics</h2>
            </div>
            <button class="icon-button" type="button" aria-label="Close topic drawer" @click="topicDrawerOpen = false">
              <X :size="16" aria-hidden="true" />
            </button>
          </header>
          <div class="problem-drawer-body">
            <div class="problem-link-controls compact">
              <select v-model="topicDraft.topic_id">
                <option value="">Select topic...</option>
                <option v-for="topic in availableTopics" :key="topic.id" :value="topic.id">{{ topic.title }}</option>
              </select>
              <button class="button subtle" type="button" @click="addTopicLink">Link</button>
            </div>
            <span v-for="link in workspace?.topic_links || []" :key="link.id" class="topic-pill">
              <RouterLink :to="`/topics/${link.topic_id}`">{{ link.topic?.title || link.topic_id }}</RouterLink>
              <button type="button" aria-label="Remove topic link" @click="removeTopicLink(link.topic_id)">
                <X :size="13" aria-hidden="true" />
              </button>
            </span>
          </div>
        </section>
      </div>
    </Transition>

    <Transition name="modal-fade">
      <section v-if="attemptModalOpen" class="modal-backdrop" @click.self="attemptModalOpen = false">
        <div class="modal-panel problem-attempt-modal">
          <header>
            <span class="modal-icon">
              <Plus :size="20" aria-hidden="true" />
            </span>
            <div>
              <h2>New Attempt</h2>
              <p>Record a concrete strategy under this problem.</p>
            </div>
            <button class="icon-button" type="button" aria-label="Close attempt modal" @click="attemptModalOpen = false">
              <X :size="18" aria-hidden="true" />
            </button>
          </header>
          <section class="problem-attempt-modal-body">
            <div v-if="selectedProblemLinks.length" class="attempt-seed-panel">
              <strong>{{ selectedProblemLinks.length }} input fragments selected</strong>
              <p>These problem fragments will be linked to the new attempt as inputs.</p>
              <span v-for="link in selectedProblemLinks" :key="link.id" class="chip" data-chip="topic">
                {{ link.fragment?.title || link.fragment_id }}
              </span>
            </div>
            <label>
              Title
              <input v-model="attemptDraft.title" placeholder="e.g. Test the one-object quantale case" />
            </label>
            <label>
              Strategy
              <textarea v-model="attemptDraft.strategy" rows="4" placeholder="What will you try, and what assumptions are you restricting to?" />
            </label>
            <label>
              Expected outcome
              <textarea v-model="attemptDraft.expected_outcome" rows="3" placeholder="What would count as progress, failure, or a useful counterexample?" />
            </label>
          </section>
          <footer class="action-row">
            <button class="button subtle" type="button" @click="attemptModalOpen = false">Cancel</button>
            <button class="button primary" type="button" :disabled="!attemptDraft.title || !attemptDraft.strategy" @click="createAttempt">
              <Plus :size="16" aria-hidden="true" />
              Create Attempt
            </button>
          </footer>
        </div>
      </section>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { Handle, Position, VueFlow, type Edge, type Node, type NodeDragEvent, type NodeMouseEvent } from "@vue-flow/core";
import "@vue-flow/core/dist/style.css";
import "@vue-flow/core/dist/theme-default.css";
import {
  BookOpen,
  Box,
  CheckSquare,
  Eye,
  EyeOff,
  FileQuestion,
  GitBranch,
  Library,
  Lightbulb,
  ListChecks,
  Network,
  PanelRight,
  Plus,
  RefreshCw,
  Save,
  Sigma,
  SlidersHorizontal,
  Square,
  Sparkles,
  Table2,
  Tags,
  Target,
  X,
} from "lucide-vue-next";
import DashboardTable from "../components/DashboardTable.vue";
import MarkdownLatexRenderer from "../components/MarkdownLatexRenderer.vue";
import { api } from "../api/client";
import { useAILogsStore } from "../stores/aiLogs";
import type {
  Attempt,
  Fragment,
  ProblemFragmentLink,
  ProblemFragmentRole,
  ProblemStatus,
  ProblemSummaryProposal,
  ProblemWorkspace,
  ResearchProblem,
  Topic,
} from "../types";
import { problemFragmentRoles, problemStatuses } from "../types";

const props = defineProps<{ id: string }>();
const router = useRouter();
const aiLogs = useAILogsStore();

const workspace = ref<ProblemWorkspace | null>(null);
const allFragments = ref<Fragment[]>([]);
const topics = ref<Topic[]>([]);
const nodes = ref<Node[]>([]);
const edges = ref<Edge[]>([]);
const viewMode = ref<"graph" | "timeline" | "table">("graph");
const selectedLinkId = ref("");
const editDrawerOpen = ref(false);
const addDrawerOpen = ref(false);
const topicDrawerOpen = ref(false);
const aiPanelOpen = ref(false);
const attemptModalOpen = ref(false);
const saving = ref(false);
const aiBusy = ref(false);
const message = ref("");
const error = ref("");
const aiError = ref("");
const proposal = ref<ProblemSummaryProposal | null>(null);
const currentProblemJobId = ref("");
const fragmentSearch = ref("");
const selectedProblemLinkIds = ref<string[]>([]);
const showProblemRoleEdges = ref(true);
const showMathRelationEdges = ref(true);
const graphControlsOpen = ref(false);
const detailsPanelOpen = ref(true);
let problemJobPollTimer: number | undefined;

const draft = reactive({
  title: "",
  status: "open" as ProblemStatus,
  objective: "",
  current_formulation: "",
  motivation: "",
  why_it_matters: "",
});
const fragmentDraft = reactive({ role: "other" as ProblemFragmentRole, note: "" });
const topicDraft = reactive({ topic_id: "" });
const aiRequest = reactive({ title_hint: "", objective_hint: "" });
const attemptDraft = reactive({ title: "", strategy: "", expected_outcome: "" });
const selectedLinkDraft = reactive({ role: "other" as ProblemFragmentRole, note: "" });
const graphNodeSize = { width: 238, height: 92 };
const graphHandlePositions = [Position.Left, Position.Right, Position.Top, Position.Bottom];

const problem = computed(() => workspace.value?.problem || null);
const selectedLink = computed(() => workspace.value?.fragment_links.find((link) => link.id === selectedLinkId.value) || null);
const selectedProblemLinkSet = computed(() => new Set(selectedProblemLinkIds.value));
const selectedProblemLinks = computed(
  () => workspace.value?.fragment_links.filter((link) => selectedProblemLinkSet.value.has(link.id)) || []
);
const linkedFragmentIds = computed(() => new Set(workspace.value?.fragment_links.map((link) => link.fragment_id) || []));
const linkedTopicIds = computed(() => new Set(workspace.value?.topic_links.map((link) => link.topic_id) || []));
const availableFragments = computed(() => allFragments.value.filter((fragment) => !linkedFragmentIds.value.has(fragment.id)));
const availableTopics = computed(() => topics.value.filter((topic) => !linkedTopicIds.value.has(topic.id)));
const filteredAvailableFragments = computed(() => {
  const needle = fragmentSearch.value.trim().toLowerCase();
  if (!needle) return availableFragments.value;
  return availableFragments.value.filter(
    (fragment) => fragment.title.toLowerCase().includes(needle) || fragment.body.toLowerCase().includes(needle)
  );
});
const gapLinks = computed(() =>
  workspace.value?.fragment_links.filter((link) => ["gap", "main_question"].includes(String(link.role))) || []
);
const blockedAttempts = computed(() =>
  workspace.value?.attempts.filter((attempt) => attempt.status === "blocked" || attempt.status === "planned") || []
);

async function load() {
  error.value = "";
  const [workspaceResult, fragmentsResult, topicsResult] = await Promise.all([
    api.getProblemWorkspace(props.id),
    api.listFragments(),
    api.listTopics(),
  ]);
  workspace.value = workspaceResult;
  allFragments.value = fragmentsResult;
  topics.value = topicsResult;
  pruneProblemLinkSelection();
  syncDraft(workspaceResult.problem);
  syncFlowElements();
}

function syncDraft(value: ResearchProblem) {
  draft.title = value.title;
  draft.status = value.status;
  draft.objective = value.objective;
  draft.current_formulation = value.current_formulation || "";
  draft.motivation = value.motivation || "";
  draft.why_it_matters = value.why_it_matters || "";
  aiRequest.title_hint = value.title;
  aiRequest.objective_hint = value.objective;
}

function syncFlowElements() {
  if (!workspace.value) return;
  const problemNodeKey = `problem:${workspace.value.problem.id}`;
  const roleGroups = groupedLinks();
  const generatedNodes: Node[] = [
    {
      id: problemNodeKey,
      type: "default",
      position: savedOrDefault(problemNodeKey, { x: 460, y: 180 }),
      data: {
        kind: "problem",
        title: workspace.value.problem.title,
        subtitle: workspace.value.problem.status,
      },
      class: "problem-workspace-node problem-root-node",
    },
  ];
  for (const [role, links] of roleGroups.entries()) {
    const column = roleColumn(role);
    links.forEach((link, index) => {
      const key = fragmentNodeKey(link);
      generatedNodes.push({
        id: key,
        type: "default",
        position: savedOrDefault(key, { x: column.x, y: column.y + index * 132 }),
        data: {
          kind: "fragment",
          title: link.fragment?.title || link.fragment_id,
          subtitle: link.fragment?.type || "Fragment",
          type: link.fragment?.type,
          role: link.role,
        },
        class: `problem-workspace-node problem-fragment-node role-${link.role}`,
      });
    });
  }
  const positionsById = positionsFromNodes(generatedNodes);
  const roleEdges: Edge[] = showProblemRoleEdges.value
    ? workspace.value.fragment_links.map((link) => dynamicEdge({
        id: `role-${link.id}`,
        source: problemNodeKey,
        target: fragmentNodeKey(link),
        label: link.role,
        animated: ["gap", "main_question"].includes(String(link.role)),
        class: "problem-role-edge",
        style: { stroke: roleColor(String(link.role)), strokeWidth: 2.1 },
        labelStyle: { fill: roleColor(String(link.role)), fontWeight: 800 },
        labelBgStyle: { fill: "var(--surface)", stroke: roleColor(String(link.role)) },
      }, positionsById))
    : [];
  const linkByFragment = new Map(workspace.value.fragment_links.map((link) => [link.fragment_id, link]));
  const relationEdges: Edge[] = showMathRelationEdges.value
    ? workspace.value.relations.flatMap((relation) => {
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
      })
    : [];
  nodes.value = generatedNodes;
  edges.value = [...roleEdges, ...relationEdges];
  void nextTick(() => syncSelectedDraft());
}

function groupedLinks() {
  const groups = new Map<string, ProblemFragmentLink[]>();
  for (const link of workspace.value?.fragment_links || []) {
    groups.set(String(link.role), [...(groups.get(String(link.role)) || []), link]);
  }
  return groups;
}

function roleColumn(role: string) {
  const columns: Record<string, { x: number; y: number }> = {
    active_definition: { x: 90, y: 70 },
    candidate_definition: { x: 90, y: 230 },
    main_question: { x: 430, y: 390 },
    gap: { x: 430, y: 520 },
    claim: { x: 820, y: 80 },
    proof: { x: 820, y: 260 },
    example: { x: 1090, y: 80 },
    counterexample: { x: 1090, y: 240 },
    source_note: { x: 170, y: 520 },
    background: { x: 170, y: 650 },
    notation: { x: 90, y: 390 },
    result: { x: 820, y: 430 },
  };
  return columns[role] || { x: 600, y: 650 };
}

function savedOrDefault(nodeKey: string, fallback: { x: number; y: number }) {
  const saved = workspace.value?.positions[nodeKey];
  return saved ? { x: saved.x, y: saved.y } : fallback;
}

function fragmentNodeKey(link: ProblemFragmentLink) {
  return `fragment_link:${link.id}`;
}

function selectGraphNode(event: NodeMouseEvent) {
  const nodeId = event.node.id;
  if (!nodeId.startsWith("fragment_link:")) {
    selectedLinkId.value = "";
    return;
  }
  selectedLinkId.value = nodeId.replace("fragment_link:", "");
  syncSelectedDraft();
}

function syncSelectedDraft() {
  if (!selectedLink.value) return;
  selectedLinkDraft.role = selectedLink.value.role as ProblemFragmentRole;
  selectedLinkDraft.note = selectedLink.value.note || "";
}

function toggleProblemRoleEdges() {
  showProblemRoleEdges.value = !showProblemRoleEdges.value;
  syncFlowElements();
}

function toggleMathRelationEdges() {
  showMathRelationEdges.value = !showMathRelationEdges.value;
  syncFlowElements();
}

function toggleProblemLinkSelection(linkId: string) {
  if (selectedProblemLinkSet.value.has(linkId)) {
    selectedProblemLinkIds.value = selectedProblemLinkIds.value.filter((id) => id !== linkId);
  } else {
    selectedProblemLinkIds.value = [...selectedProblemLinkIds.value, linkId];
  }
}

function pruneProblemLinkSelection() {
  const valid = new Set(workspace.value?.fragment_links.map((link) => link.id) || []);
  selectedProblemLinkIds.value = selectedProblemLinkIds.value.filter((id) => valid.has(id));
}

async function saveSelectedLink() {
  if (!problem.value || !selectedLink.value) return;
  await api.updateProblemFragment(problem.value.id, selectedLink.value.id, {
    role: selectedLinkDraft.role,
    note: selectedLinkDraft.note || null,
  });
  message.value = "Problem fragment role saved.";
  await load();
}

async function saveLayout(_event?: NodeDragEvent) {
  if (!workspace.value) return;
  refreshDynamicHandles(_event);
  const positions: Record<string, { node_key: string; x: number; y: number }> = {};
  nodes.value.forEach((node) => {
    positions[node.id] = { node_key: node.id, x: node.position.x, y: node.position.y };
  });
  try {
    workspace.value = await api.updateProblemGraphLayout(workspace.value.problem.id, positions);
    message.value = "Layout saved.";
    syncFlowElements();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
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

async function autoArrange() {
  if (!workspace.value) return;
  const arranged = arrangedGraphPositions();
  const nextNodes: Node[] = [];
  nodes.value.forEach((node) => {
    nextNodes.push({
      ...node,
      position: arranged[node.id] || node.position,
    } as Node);
  });
  nodes.value = nextNodes;
  await saveLayout();
  message.value = "Graph auto-arranged.";
}

function arrangedGraphPositions() {
  const positions: Record<string, { x: number; y: number }> = {};
  if (!workspace.value) return positions;
  const problemNodeKey = `problem:${workspace.value.problem.id}`;
  positions[problemNodeKey] = { x: 460, y: 210 };
  const groups = groupedLinks();
  for (const [role, links] of groups.entries()) {
    const column = roleColumn(role);
    links
      .slice()
      .sort((left, right) => (left.fragment?.title || left.fragment_id).localeCompare(right.fragment?.title || right.fragment_id))
      .forEach((link, index) => {
        positions[fragmentNodeKey(link)] = {
          x: column.x,
          y: column.y + index * 142,
        };
      });
  }
  return positions;
}

async function saveProblem() {
  if (!problem.value) return;
  saving.value = true;
  try {
    await api.updateProblem(problem.value.id, {
      title: draft.title,
      status: draft.status,
      objective: draft.objective,
      current_formulation: draft.current_formulation || null,
      motivation: draft.motivation || null,
      why_it_matters: draft.why_it_matters || null,
    });
    editDrawerOpen.value = false;
    message.value = "Problem saved.";
    await load();
  } finally {
    saving.value = false;
  }
}

async function addFragmentLink(fragmentId: string) {
  if (!problem.value) return;
  try {
    await api.addProblemFragment(problem.value.id, {
      fragment_id: fragmentId,
      role: fragmentDraft.role,
      note: fragmentDraft.note || null,
    });
    message.value = "Fragment linked to problem.";
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function removeFragmentLink(linkId: string) {
  if (!problem.value) return;
  await api.removeProblemFragment(problem.value.id, linkId);
  selectedLinkId.value = "";
  message.value = "Fragment removed from problem.";
  await load();
}

async function addTopicLink() {
  if (!problem.value || !topicDraft.topic_id) return;
  try {
    await api.addProblemTopic(problem.value.id, topicDraft.topic_id);
    topicDraft.topic_id = "";
    await load();
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : String(caught);
  }
}

async function removeTopicLink(topicId: string) {
  if (!problem.value) return;
  await api.removeProblemTopic(problem.value.id, topicId);
  await load();
}

async function createAttempt() {
  if (!problem.value || !attemptDraft.title || !attemptDraft.strategy) return;
  const attempt = await api.createAttempt(problem.value.id, {
    title: attemptDraft.title,
    strategy: attemptDraft.strategy,
    expected_outcome: attemptDraft.expected_outcome || null,
    status: "planned",
  });
  for (const link of selectedProblemLinks.value) {
    await api.addAttemptFragment(attempt.id, {
      fragment_id: link.fragment_id,
      role: "input",
      note: link.note || null,
    });
  }
  attemptModalOpen.value = false;
  attemptDraft.title = "";
  attemptDraft.strategy = "";
  attemptDraft.expected_outcome = "";
  selectedProblemLinkIds.value = [];
  await load();
  await router.push(`/attempts/${attempt.id}`);
}

async function suggestProblem() {
  if (!problem.value || !workspace.value) return;
  aiBusy.value = true;
  aiError.value = "";
  proposal.value = null;
  try {
    const job = await api.startProblemSummaryJob({
      topic_ids: workspace.value.topic_links.map((link) => link.topic_id),
      fragment_ids: workspace.value.fragment_links.map((link) => link.fragment_id),
      title_hint: aiRequest.title_hint || null,
      objective_hint: aiRequest.objective_hint || null,
    });
    currentProblemJobId.value = job.job_id;
    syncProblemJobToLogs(job, true);
    startProblemJobPolling();
  } catch (caught) {
    aiBusy.value = false;
    aiError.value = caught instanceof Error ? caught.message : String(caught);
  }
}

function startProblemJobPolling() {
  stopProblemJobPolling();
  problemJobPollTimer = window.setInterval(() => void pollProblemJob(), 1000);
  void pollProblemJob();
}

function stopProblemJobPolling() {
  if (problemJobPollTimer !== undefined) {
    window.clearInterval(problemJobPollTimer);
    problemJobPollTimer = undefined;
  }
}

async function pollProblemJob() {
  if (!currentProblemJobId.value) return;
  const job = await api.getProblemSummaryJob(currentProblemJobId.value);
  syncProblemJobToLogs(job);
  if (job.status === "queued" || job.status === "running") return;
  stopProblemJobPolling();
  aiBusy.value = false;
  if (job.result?.proposal) proposal.value = job.result.proposal;
  if (job.error || job.result?.error) aiError.value = job.error || job.result?.error || "";
}

function syncProblemJobToLogs(job: Awaited<ReturnType<typeof api.getProblemSummaryJob>>, open = false) {
  aiLogs.upsertRun({
    id: job.job_id,
    kind: "problem_summary",
    label: `Problem proposal: ${draft.title || "Untitled problem"}`,
    status: job.status,
    logs: job.logs,
    error: job.error,
    result: job.result,
    context: { problem_id: problem.value?.id || null },
    open,
  });
}

function restoreCompletedProblemProposal() {
  const run = aiLogs.runs.find(
    (item) => item.kind === "problem_summary" && item.context?.problem_id === props.id && item.status === "succeeded"
  );
  const result = run?.result as { proposal?: ProblemSummaryProposal | null } | null;
  if (result?.proposal) proposal.value = result.proposal;
}

function discardProposal() {
  proposal.value = null;
  aiError.value = "";
  aiLogs.runs
    .filter((item) => item.kind === "problem_summary" && item.context?.problem_id === props.id)
    .forEach((run) => aiLogs.removeRun(run.id));
  message.value = "AI proposal discarded.";
}

function applyProposalFields() {
  if (!proposal.value) return;
  draft.title = proposal.value.title;
  draft.objective = proposal.value.objective;
  draft.current_formulation = proposal.value.current_formulation || "";
  draft.motivation = proposal.value.motivation || "";
  draft.why_it_matters = proposal.value.why_it_matters || "";
  editDrawerOpen.value = true;
}

async function applySuggestedRoles() {
  if (!problem.value || !proposal.value || !workspace.value) return;
  const existingByFragment = new Map(workspace.value.fragment_links.map((link) => [link.fragment_id, link]));
  for (const suggested of proposal.value.suggested_fragment_roles) {
    const existing = existingByFragment.get(suggested.fragment_id);
    if (existing) {
      await api.updateProblemFragment(problem.value.id, existing.id, {
        role: suggested.role,
        note: suggested.note,
      });
    } else {
      await api.addProblemFragment(problem.value.id, {
        fragment_id: suggested.fragment_id,
        role: suggested.role,
        note: suggested.note,
      });
    }
  }
  message.value = "Suggested roles applied.";
  await load();
}

function countRole(role: string) {
  return workspace.value?.fragment_links.filter((link) => link.role === role).length || 0;
}

function roleColor(role: string) {
  if (role.includes("definition") || role === "notation") return "#0f9f8f";
  if (role === "claim" || role === "result" || role === "proof") return "#3178d4";
  if (role === "gap" || role === "main_question") return "#d88916";
  if (role === "source_note" || role === "background") return "#7a8998";
  return "#7b61d1";
}

function nodeIcon(data: Record<string, string>) {
  if (data.kind === "problem") return Target;
  if (data.role === "gap" || data.role === "main_question" || data.type === "Question") return FileQuestion;
  if (data.role?.includes("definition") || data.type === "Definition") return BookOpen;
  if (data.role === "claim" || data.type === "Theorem" || data.type === "Proposition") return Sigma;
  if (data.role === "source_note" || data.role === "background") return Box;
  return Lightbulb;
}

onMounted(async () => {
  await load();
  restoreCompletedProblemProposal();
});
onBeforeUnmount(stopProblemJobPolling);
</script>
