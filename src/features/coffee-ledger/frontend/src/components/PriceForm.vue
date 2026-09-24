<template>
  <section class="panel">
    <h2>一杯単価</h2>
    <form class="row" @submit.prevent="submit">
      <label>
        金額
        <input v-model.number="amount" type="number" min="1" step="1" :disabled="busy" />
      </label>
      <button type="submit" class="primary" :disabled="busy || !valid">保存</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

const props = defineProps<{
  current: number | null;
  busy: boolean;
}>();

const emit = defineEmits<{
  save: [amount: number];
}>();

const amount = ref<number>(props.current ?? 100);

watch(
  () => props.current,
  (value) => {
    if (value !== null) {
      amount.value = value;
    }
  },
);

const valid = computed(() => {
  const value = Number(amount.value);
  return Number.isInteger(value) && value >= 1;
});

function submit(): void {
  if (!valid.value) {
    return;
  }
  emit("save", Number(amount.value));
}
</script>
