<template>
  <section class="page">
    <header class="page-header">
      <div>
        <h1>Agent Console</h1>
        <p>Manual patch import is the active first-version mode</p>
      </div>
      <button class="button subtle" type="button" @click="load">
        <RefreshCw :size="16" aria-hidden="true" />
        Refresh
      </button>
    </header>
    <section class="plain-section">
      <pre class="metadata-json">{{ status }}</pre>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RefreshCw } from "lucide-vue-next";
import { api } from "../api/client";

const status = ref("");

async function load() {
  status.value = JSON.stringify(await api.agentStatus(), null, 2);
}

onMounted(load);
</script>

