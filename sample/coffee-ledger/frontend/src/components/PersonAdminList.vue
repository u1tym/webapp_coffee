<template>
  <section class="panel">
    <h2>人</h2>
    <form class="row" @submit.prevent="submit">
      <label>
        名前
        <input v-model="name" type="text" maxlength="100" :disabled="busy" />
      </label>
      <button type="submit" class="primary" :disabled="busy || name.trim() === ''">登録</button>
    </form>
    <ul class="people-admin">
      <li v-for="(person, index) in people" :key="person.id">
        <button type="button" class="name-select" @click="$emit('select', person.id)">
          {{ person.name }}
          <span v-if="person.deactivated" class="badge">停止</span>
        </button>
        <DisplayOrderControls
          :index="index"
          :last-index="people.length - 1"
          :busy="busy"
          @move="(delta) => $emit('move', person.id, delta)"
        />
        <button
          v-if="!person.deactivated"
          type="button"
          class="link"
          :disabled="busy"
          @click="$emit('deactivate', person.id)"
        >
          利用停止
        </button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { Person } from "../types";
import DisplayOrderControls from "./DisplayOrderControls.vue";

defineProps<{
  people: Person[];
  busy: boolean;
}>();

const emit = defineEmits<{
  register: [name: string];
  select: [personId: number];
  deactivate: [personId: number];
  move: [personId: number, delta: number];
}>();

const name = ref("");

function submit(): void {
  const trimmed = name.value.trim();
  if (trimmed === "") {
    return;
  }
  emit("register", trimmed);
  name.value = "";
}
</script>
