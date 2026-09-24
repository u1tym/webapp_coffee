<template>
  <main class="page">
    <p><RouterLink to="/admin">← 管理トップ</RouterLink></p>
    <h1>集計</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <BalanceLedger
      :uncollected-amount="summary.uncollected_amount"
      :collected-amount="summary.collected_amount"
      :vault-amount="summary.vault_amount"
      :entries="summary.entries"
    />
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getSummary } from "../../api";
import type { ApiError, Summary } from "../../types";
import BalanceLedger from "../../components/BalanceLedger.vue";

const summary = ref<Summary>({
  uncollected_amount: 0,
  collected_amount: 0,
  vault_amount: 0,
  entries: [],
});
const error = ref("");

onMounted(async () => {
  try {
    summary.value = await getSummary();
  } catch (err) {
    error.value = (err as ApiError).message;
  }
});
</script>
