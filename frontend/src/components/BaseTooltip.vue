<template>
  <TooltipProvider :delay-duration="250">
    <TooltipRoot>
      <TooltipTrigger as-child>
        <slot />
      </TooltipTrigger>
      <TooltipPortal>
        <TooltipContent class="base-tooltip" :side="side" :side-offset="8">
          {{ label }}
          <TooltipArrow class="base-tooltip-arrow" />
        </TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  </TooltipProvider>
</template>

<script setup lang="ts">
import {
  TooltipArrow,
  TooltipContent,
  TooltipPortal,
  TooltipProvider,
  TooltipRoot,
  TooltipTrigger,
} from "reka-ui";

withDefaults(defineProps<{ label: string; side?: "top" | "right" | "bottom" | "left" }>(), {
  side: "bottom"
});
</script>
