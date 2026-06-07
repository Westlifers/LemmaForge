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
      <header class="section-header">
        <div>
          <h2>Agent Status</h2>
          <p>Local backend agent capability snapshot</p>
        </div>
        <span class="panel-icon">
          <Terminal :size="17" aria-hidden="true" />
        </span>
      </header>
      <pre class="metadata-json compact-json">{{ status }}</pre>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RefreshCw, Terminal } from "lucide-vue-next";
import { api } from "../api/client";

const status = ref("");

async function load() {
  status.value = JSON.stringify(await api.agentStatus(), null, 2);
}

onMounted(load);
</script>
