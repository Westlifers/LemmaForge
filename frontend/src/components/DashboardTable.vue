<template>
  <table class="dashboard-table">
    <thead>
      <tr>
        <th v-for="header in headers" :key="header">{{ header }}</th>
      </tr>
    </thead>
    <tbody>
      <slot />
    </tbody>
  </table>
</template>

<script setup lang="ts">
defineProps<{ headers: string[] }>();
</script>
