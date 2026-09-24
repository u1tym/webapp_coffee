<template>
  <section class="panel">
    <form class="row" @submit.prevent="submit">
      <label>
        パスワード
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          autofocus
        />
      </label>
      <button type="submit" class="primary" :disabled="!canSubmit">進む</button>
      <button type="button" @click="emit('cancel')">キャンセル</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { matchesAdminPassword } from "../adminGate";

const emit = defineEmits<{
  success: [];
  cancel: [];
}>();

const password = ref("");
const error = ref("");

const canSubmit = computed(() => password.value.length > 0);

function submit(): void {
  if (!canSubmit.value) {
    return;
  }
  if (!matchesAdminPassword(password.value)) {
    error.value = "パスワードが正しくありません。";
    return;
  }
  error.value = "";
  emit("success");
}
</script>
