<template>
  <section class="panel">
    <h2>徴収状況</h2>
    <p>未徴収 {{ formatYen(uncollectedAmount) }}</p>
    <p>徴収済み {{ formatYen(collectedAmount) }}</p>
    <p>金庫 {{ formatYen(vaultAmount) }}</p>
    <button
      type="button"
      class="primary"
      :disabled="busy || collectedAmount === 0"
      @click="confirmDeposit"
    >
      金庫に収める
    </button>
    <h3>金庫収納の履歴</h3>
    <ul class="records">
      <li v-for="item in deposits" :key="item.id">
        {{ formatDateTime(item.deposited_at) }} · {{ formatYen(item.amount) }}
      </li>
    </ul>
    <p v-if="deposits.length === 0" class="muted">金庫収納はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { SafeDeposit } from "../types";

const props = defineProps<{
  collectedAmount: number;
  uncollectedAmount: number;
  vaultAmount: number;
  deposits: SafeDeposit[];
  busy: boolean;
}>();

const emit = defineEmits<{
  deposit: [];
}>();

function confirmDeposit(): void {
  if (props.collectedAmount === 0) {
    return;
  }
  const ok = window.confirm(
    `徴収済み ${formatYen(props.collectedAmount)} を金庫に収めます。よろしいですか？`,
  );
  if (ok) {
    emit("deposit");
  }
}
</script>
