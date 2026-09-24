<template>
  <section class="panel">
    <h2>金庫操作</h2>
    <form class="vault-form" @submit.prevent="submit">
      <label>
        事由
        <input v-model="reason" type="text" maxlength="200" :disabled="busy" required />
      </label>
      <fieldset class="direction-row">
        <legend>入金または出金</legend>
        <label class="inline">
          <input v-model="direction" type="radio" value="deposit" :disabled="busy" />
          入金
        </label>
        <label class="inline">
          <input v-model="direction" type="radio" value="withdrawal" :disabled="busy" />
          出金
        </label>
      </fieldset>
      <label>
        金額
        <input v-model.number="amount" type="number" min="1" step="1" :disabled="busy" />
      </label>
      <label>
        事由の日付
        <input v-model="reasonDate" type="date" :disabled="busy" required />
      </label>
      <button type="submit" class="primary" :disabled="busy || !canSubmit">記録する</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { formatYen, todayJst } from "../format";

const props = defineProps<{
  vaultAmount: number;
  busy: boolean;
}>();

const emit = defineEmits<{
  operate: [payload: { reason: string; direction: "deposit" | "withdrawal"; amount: number; reason_date: string }];
}>();

const reason = ref("");
const direction = ref<"deposit" | "withdrawal">("deposit");
const amount = ref(1);
const reasonDate = ref(todayJst());

const canSubmit = computed(() => {
  const value = Number(amount.value);
  return (
    reason.value.trim() !== "" &&
    Number.isInteger(value) &&
    value >= 1 &&
    (direction.value === "deposit" || value <= props.vaultAmount)
  );
});

function submit(): void {
  if (!canSubmit.value) {
    return;
  }
  const value = Number(amount.value);
  const label = direction.value === "deposit" ? "入金" : "出金";
  const ok = window.confirm(
    `事由「${reason.value.trim()}」で ${label} ${formatYen(value)} を記録します。よろしいですか？`,
  );
  if (!ok) {
    return;
  }
  emit("operate", {
    reason: reason.value.trim(),
    direction: direction.value,
    amount: value,
    reason_date: reasonDate.value,
  });
}
</script>
