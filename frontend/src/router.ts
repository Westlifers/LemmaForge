import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "./pages/Dashboard.vue";
import InboxImport from "./pages/InboxImport.vue";
import FragmentList from "./pages/FragmentList.vue";
import FragmentDetail from "./pages/FragmentDetail.vue";
import ContextPackBuilder from "./pages/ContextPackBuilder.vue";
import TopicWorkspace from "./pages/TopicWorkspace.vue";
import TopicDetail from "./pages/TopicDetail.vue";
import ZoteroSettings from "./pages/ZoteroSettings.vue";
import AgentConsole from "./pages/AgentConsole.vue";
import SourceDetail from "./pages/SourceDetail.vue";
import ReviewQueue from "./pages/ReviewQueue.vue";
import RejectedFragments from "./pages/RejectedFragments.vue";
import SettingsPage from "./pages/SettingsPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: Dashboard },
    { path: "/import", name: "import", component: InboxImport },
    { path: "/review", name: "review", component: ReviewQueue },
    { path: "/rejected", name: "rejected", component: RejectedFragments },
    { path: "/fragments", name: "fragments", component: FragmentList },
    { path: "/fragments/:id", name: "fragment-detail", component: FragmentDetail, props: true },
    { path: "/topics", name: "topics", component: TopicWorkspace },
    { path: "/topics/:id", name: "topic-detail", component: TopicDetail, props: true },
    { path: "/context-packs", name: "context-packs", component: ContextPackBuilder },
    { path: "/zotero", name: "zotero", component: ZoteroSettings },
    { path: "/sources/:id", name: "source-detail", component: SourceDetail, props: true },
    { path: "/agent", name: "agent", component: AgentConsole },
    { path: "/settings", name: "settings", component: SettingsPage }
  ]
});

export default router;
