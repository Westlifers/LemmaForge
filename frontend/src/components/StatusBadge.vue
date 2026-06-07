<template>
  <span class="status" :data-status="status">
    <CircleDot :size="13" aria-hidden="true" />
    {{ status }}
  </span>
</template>

<script setup lang="ts">
import { CircleDot } from "lucide-vue-next";

defineProps<{ status: string }>();
</script>
