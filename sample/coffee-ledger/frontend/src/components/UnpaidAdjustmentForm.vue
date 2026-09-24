<template>
  <section class="panel">
    <h2>未払いの修正</h2>
    <p>現在 {{ formatYen(currentAmount) }}</p>
    <form class="vault-form" @submit.prevent="submit">
      <label>
        新しい額
        <input
          v-model.number="newAmount"
          type="number"
          min="0"
          step="1"
          :disabled="busy"
        />
      </label>
      <label>
        事由
        <input v-model="reason" type="text" maxlength="200" :disabled="busy" required />
      </label>
      <button type="submit" class="primary" :disabled="busy || !canSubmit">修正する</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { formatYen } from "../format";

const props = defineProps<{
  personName: string;
  currentAmount: number;
  busy: boolean;
}>();

const emit = defineEmits<{
  adjust: [payload: { new_amount: number; reason: string }];
}>();

const newAmount = ref(props.currentAmount);
const reason = ref("");

watch(
  () => props.currentAmount,
  (value) => {
    newAmount.value = value;
  },
);

const canSubmit = computed(() => {
  const value = Number(newAmount.value);
  return (
    Number.isInteger(value) &&
    value >= 0 &&
    value !== props.currentAmount &&
    reason.value.trim() !== ""
  );
});

function submit(): void {
  if (!canSubmit.value) {
    return;
  }
  const value = Number(newAmount.value);
  const ok = window.confirm(
    `${props.personName} の未払いを ${formatYen(props.currentAmount)} から ${formatYen(value)} に修正します。事由「${reason.value.trim()}」。よろしいですか？`,
  );
  if (!ok) {
    return;
  }
  emit("adjust", { new_amount: value, reason: reason.value.trim() });
}
</script>
