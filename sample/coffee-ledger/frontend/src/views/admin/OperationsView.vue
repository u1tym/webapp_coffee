<template>
  <main class="page">
    <p><RouterLink to="/admin">← 管理トップ</RouterLink></p>
    <h1>操作記録</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <OperationLogList :logs="logs" />
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listOperationLogs } from "../../api";
import type { ApiError, OperationLog } from "../../types";
import OperationLogList from "../../components/OperationLogList.vue";

const logs = ref<OperationLog[]>([]);
const error = ref("");

onMounted(async () => {
  try {
    const res = await listOperationLogs();
    logs.value = res.operation_logs;
  } catch (err) {
    error.value = (err as ApiError).message;
  }
});
</script>
