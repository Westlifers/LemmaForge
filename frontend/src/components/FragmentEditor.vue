<template>
  <form class="editor" @submit.prevent="submit">
    <label>
      Title
      <input v-model="draft.title" required />
    </label>
    <div class="form-grid">
      <label>
        Type
        <select v-model="draft.type">
          <option v-for="type in fragmentTypes" :key="type" :value="type">{{ type }}</option>
        </select>
      </label>
      <label>
        Status
        <select v-model="draft.status">
          <option v-for="status in fragmentStatuses" :key="status" :value="status">{{ status }}</option>
        </select>
      </label>
      <label>
        Origin
        <select v-model="draft.origin_classification">
          <option value="user_original">user_original</option>
          <option value="assistant_generated">assistant_generated</option>
          <option value="external_source">external_source</option>
          <option value="mixed">mixed</option>
          <option value="unknown">unknown</option>
        </select>
      </label>
      <label>
        Exactness
        <select v-model="draft.exactness">
          <option value="quote">quote</option>
          <option value="close_paraphrase">close_paraphrase</option>
          <option value="paraphrase">paraphrase</option>
          <option value="interpretation">interpretation</option>
          <option value="reconstruction">reconstruction</option>
          <option value="original">original</option>
        </select>
      </label>
      <label>
        Topic id
        <select v-model="draft.topic_id">
          <option :value="null">No topic</option>
          <option v-for="topic in topics" :key="topic.id" :value="topic.id">{{ topic.title }}</option>
        </select>
      </label>
    </div>
    <label>
      Body
      <textarea v-model="draft.body" rows="12" required />
    </label>
    <label>
      Change note
      <input v-model="changeNote" />
    </label>
    <button class="button primary" type="submit">
      <Save :size="16" aria-hidden="true" />
      Save
    </button>
  </form>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { Save } from "lucide-vue-next";
import type { Fragment, Topic } from "../types";
import { fragmentStatuses, fragmentTypes } from "../types";

const props = defineProps<{ fragment: Fragment; topics?: Topic[] }>();
const emit = defineEmits<{ save: [payload: Partial<Fragment> & { change_note?: string }] }>();

const draft = reactive({ ...props.fragment });
const changeNote = ref("");
const topics = computed(() => props.topics ?? []);

watch(
  () => props.fragment,
  (fragment) => {
    Object.assign(draft, fragment);
    changeNote.value = "";
  }
);

function submit() {
  emit("save", { ...draft, change_note: changeNote.value || undefined });
}
</script>
