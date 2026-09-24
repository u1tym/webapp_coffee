<template>
  <section class="panel">
    <h2>{{ title }}</h2>
    <p v-if="showUnpaid" class="unpaid">未払い {{ formatYen(unpaidAmount) }}</p>
    <form v-if="showForm" class="row" @submit.prevent="submit">
      <label>
        支払額
        <input v-model.number="amount" type="number" min="1" step="1" :disabled="busy || unpaidAmount === 0" />
      </label>
      <button type="submit" class="primary" :disabled="busy || !canPay">支払った</button>
    </form>
    <p v-if="showForm && unpaidAmount === 0" class="muted">未払いが 0 のため支払できません。</p>
    <ul class="records">
      <li v-for="payment in payments" :key="payment.id" :class="{ cancelled: payment.cancelled }">
        <span>{{ formatDateTime(payment.recorded_at) }} · {{ formatYen(payment.amount) }}</span>
        <span v-if="payment.cancelled" class="badge">取消済み</span>
        <button
          v-else-if="allowCancel"
          type="button"
          class="link"
          :disabled="busy"
          @click="$emit('cancel', payment.id)"
        >
          取り消し
        </button>
      </li>
    </ul>
    <p v-if="payments.length === 0" class="muted">支払記録はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { formatDateTime, formatYen } from "../format";
import type { Payment } from "../types";

const props = withDefaults(
  defineProps<{
    payments: Payment[];
    unpaidAmount: number;
    busy: boolean;
    showForm?: boolean;
    showUnpaid?: boolean;
    allowCancel?: boolean;
    title?: string;
  }>(),
  {
    showForm: true,
    showUnpaid: true,
    allowCancel: true,
    title: "支払",
  },
);

const emit = defineEmits<{
  pay: [amount: number];
  cancel: [paymentId: number];
}>();

const amount = ref<number>(props.unpaidAmount);

watch(
  () => props.unpaidAmount,
  (value) => {
    amount.value = value;
  },
);

const canPay = computed(() => {
  const value = Number(amount.value);
  return (
    !props.busy &&
    props.unpaidAmount > 0 &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= props.unpaidAmount
  );
});

function submit(): void {
  if (!canPay.value) {
    return;
  }
  emit("pay", Number(amount.value));
}
</script>
