import { defineStore } from "pinia";
import { api, type FragmentFilters } from "../api/client";
import type { Fragment } from "../types";

export const useFragmentsStore = defineStore("fragments", {
  state: () => ({
    fragments: [] as Fragment[],
    loading: false,
    error: ""
  }),
  actions: {
    async load(filters: FragmentFilters = {}) {
      this.loading = true;
      this.error = "";
      try {
        this.fragments = await api.listFragments(filters);
      } catch (error) {
        this.error = error instanceof Error ? error.message : String(error);
      } finally {
        this.loading = false;
      }
    }
  }
});

