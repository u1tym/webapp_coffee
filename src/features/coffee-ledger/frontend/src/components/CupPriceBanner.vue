<template>
  <p v-if="amount === null" class="price missing">単価未登録</p>
  <p v-else class="price">一杯 {{ formatYen(amount) }}</p>
</template>

<script setup lang="ts">
import { formatYen } from "../format";

defineProps<{
  amount: number | null;
}>();
</script>
