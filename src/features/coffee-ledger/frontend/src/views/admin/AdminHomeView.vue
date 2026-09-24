<template>
  <main class="page">
    <h1>管理</h1>
    <p class="admin-links">
      <RouterLink to="/admin/people">人の管理</RouterLink>
      <RouterLink to="/admin/summary">集計</RouterLink>
      <RouterLink to="/admin/operations">操作記録</RouterLink>
      <RouterLink to="/">一般へ</RouterLink>
    </p>
    <p v-if="error" class="error">{{ error }}</p>
    <PriceForm :current="cupPrice" :busy="busy" @save="onSavePrice" />
    <CollectionPanel
      :collected-amount="collected"
      :uncollected-amount="uncollected"
      :vault-amount="vault"
      :deposits="deposits"
      :busy="busy"
      @deposit="onDeposit"
    />
    <VaultOperationForm :vault-amount="vault" :busy="busy" @operate="onVaultOperate" />
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  createSafeDeposit,
  createVaultOperation,
  getCollection,
  getCupPrice,
  listSafeDeposits,
  setCupPrice,
} from "../../api";
import type { ApiError, SafeDeposit } from "../../types";
import CollectionPanel from "../../components/CollectionPanel.vue";
import PriceForm from "../../components/PriceForm.vue";
import VaultOperationForm from "../../components/VaultOperationForm.vue";

const cupPrice = ref<number | null>(null);
const collected = ref(0);
const uncollected = ref(0);
const vault = ref(0);
const deposits = ref<SafeDeposit[]>([]);
const error = ref("");
const busy = ref(false);

async function load(): Promise<void> {
  error.value = "";
  try {
    const [priceRes, collectionRes, depositRes] = await Promise.all([
      getCupPrice(),
      getCollection(),
      listSafeDeposits(),
    ]);
    cupPrice.value = priceRes.amount;
    collected.value = collectionRes.collected_amount;
    uncollected.value = collectionRes.uncollected_amount;
    vault.value = collectionRes.vault_amount;
    deposits.value = depositRes.safe_deposits;
  } catch (err) {
    error.value = (err as ApiError).message;
  }
}

onMounted(() => {
  void load();
});

async function run(action: () => Promise<void>): Promise<void> {
  if (busy.value) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await action();
    await load();
  } catch (err) {
    error.value = (err as ApiError).message;
  } finally {
    busy.value = false;
  }
}

function onSavePrice(amount: number): void {
  void run(async () => {
    await setCupPrice(amount);
  });
}

function onDeposit(): void {
  void run(async () => {
    await createSafeDeposit();
  });
}

function onVaultOperate(payload: {
  reason: string;
  direction: "deposit" | "withdrawal";
  amount: number;
  reason_date: string;
}): void {
  void run(async () => {
    await createVaultOperation(payload);
  });
}
</script>
