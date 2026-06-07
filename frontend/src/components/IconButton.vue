<template>
  <BaseTooltip v-if="tooltip" :label="tooltip" :side="tooltipSide">
    <component :is="tag" class="icon-button" :aria-label="label" v-bind="$attrs">
      <slot />
    </component>
  </BaseTooltip>
  <component :is="tag" v-else class="icon-button" :aria-label="label" v-bind="$attrs">
    <slot />
  </component>
</template>

<script setup lang="ts">
import BaseTooltip from "./BaseTooltip.vue";

withDefaults(
  defineProps<{
    label: string;
    tag?: "button" | "a" | "RouterLink";
    tooltip?: string;
    tooltipSide?: "top" | "right" | "bottom" | "left";
  }>(),
  {
    tag: "button",
    tooltip: "",
    tooltipSide: "bottom"
  }
);
</script>
