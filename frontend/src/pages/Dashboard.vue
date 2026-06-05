<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Research Dashboard</h1>
        <p>Local fragment graph overview</p>
      </div>
      <RouterLink class="button primary" to="/import">
        <Inbox :size="16" aria-hidden="true" />
        Import
      </RouterLink>
    </header>

    <div class="metric-grid">
      <div class="metric">
        <span>Total fragments</span>
        <strong>{{ fragments.length }}</strong>
      </div>
      <div class="metric">
        <span>Needs review</span>
        <strong>{{ reviewCount }}</strong>
      </div>
      <div class="metric">
        <span>Stable fragments</span>
        <strong>{{ stableCount }}</strong>
      </div>
      <div class="metric">
        <span>Working notes</span>
        <strong>{{ workingCount }}</strong>
      </div>
    </div>

    <section class="plain-section">
      <header class="section-header">
        <h2>Recent Fragments</h2>
        <RouterLink class="button subtle" to="/fragments">
          <ArrowRight :size="16" aria-hidden="true" />
          Browse
        </RouterLink>
      </header>
      <div class="list-stack">
        <FragmentCard v-for="fragment in recentFragments" :key="fragment.id" :fragment="fragment" />
        <p v-if="!recentFragments.length" class="empty-state">No accepted fragments yet.</p>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { ArrowRight, Inbox } from "lucide-vue-next";
import FragmentCard from "../components/FragmentCard.vue";
import { useFragmentsStore } from "../stores/fragments";
import { acceptedFragmentStatuses, unacceptedFragmentStatuses } from "../types";

const store = useFragmentsStore();
const fragments = computed(() => store.fragments);
const reviewCount = computed(
  () => fragments.value.filter((item) => unacceptedFragmentStatuses.includes(item.status)).length
);
const stableCount = computed(() => fragments.value.filter((item) => item.status === "stable").length);
const workingCount = computed(() => fragments.value.filter((item) => item.status === "working").length);
const recentFragments = computed(() =>
  fragments.value.filter((item) => acceptedFragmentStatuses.includes(item.status)).slice(0, 6)
);

onMounted(() => store.load());
</script>
