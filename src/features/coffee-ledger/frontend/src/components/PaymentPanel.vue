<template>
  <section class="panel">
    <h2>{{ title }}</h2>
    <ul class="records">
      <li v-for="payment in payments" :key="payment.id" :class="{ cancelled: payment.cancelled }">
        <span>{{ formatDateTime(payment.recorded_at) }} · {{ formatYen(payment.amount) }}</span>
        <span v-if="payment.cancelled" class="badge">取消済み</span>
      </li>
    </ul>
    <p v-if="payments.length === 0" class="muted">支払記録はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { Payment } from "../types";

defineProps<{
  payments: Payment[];
  title: string;
}>();
</script>
