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

    <div class="onscreen-keyboard">
      <div v-for="row in KEYBOARD_ROWS" :key="row.join('')" class="onscreen-keyboard-row">
        <button v-for="key in row" :key="key" type="button" @click="appendChar(key)">
          {{ key }}
        </button>
      </div>
    </div>

    <div class="numpad">
      <div v-for="row in NUMPAD_ROWS" :key="row.join('')" class="numpad-row">
        <button v-for="key in row" :key="key" type="button" @click="appendChar(key)">
          {{ key }}
        </button>
      </div>
    </div>

    <button type="button" class="password-clear" @click="clearPassword">消去</button>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { matchesAdminPassword } from "../adminGate";

const KEYBOARD_ROWS = [
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
  ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
  ["z", "x", "c", "v", "b", "n", "m"],
];

const NUMPAD_ROWS = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["0"],
];

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

function appendChar(char: string): void {
  password.value += char;
}

function clearPassword(): void {
  password.value = "";
}
</script>
