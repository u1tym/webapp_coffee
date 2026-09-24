<template>
  <section class="panel">
    <h2>{{ title }}</h2>
    <ul class="records">
      <li v-for="drink in drinks" :key="drink.id" :class="{ cancelled: drink.cancelled }">
        <span>{{ formatDateTime(drink.recorded_at) }} · {{ formatYen(drink.unit_price) }}</span>
        <span v-if="drink.cancelled" class="badge">取消済み</span>
      </li>
    </ul>
    <p v-if="drinks.length === 0" class="muted">飲用記録はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { Drink } from "../types";

defineProps<{
  drinks: Drink[];
  title: string;
}>();
</script>
