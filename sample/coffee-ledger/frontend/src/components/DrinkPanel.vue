<template>
  <section class="panel">
    <h2>{{ title }}</h2>
    <button
      v-if="showAction"
      type="button"
      class="primary"
      :disabled="busy || !canDrink"
      @click="$emit('drink')"
    >
      飲む
    </button>
    <p v-if="showAction && !canDrink" class="muted">一杯単価が未登録のため記録できません。</p>
    <ul class="records">
      <li v-for="drink in drinks" :key="drink.id" :class="{ cancelled: drink.cancelled }">
        <span>{{ formatDateTime(drink.recorded_at) }} · {{ formatYen(drink.unit_price) }}</span>
        <span v-if="drink.cancelled" class="badge">取消済み</span>
        <button
          v-else-if="allowCancel"
          type="button"
          class="link"
          :disabled="busy"
          @click="$emit('cancel', drink.id)"
        >
          取り消し
        </button>
      </li>
    </ul>
    <p v-if="drinks.length === 0" class="muted">飲用記録はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { Drink } from "../types";

withDefaults(
  defineProps<{
    drinks: Drink[];
    canDrink?: boolean;
    busy: boolean;
    showAction?: boolean;
    allowCancel?: boolean;
    title?: string;
  }>(),
  {
    canDrink: false,
    showAction: false,
    allowCancel: true,
    title: "直近の飲用",
  },
);

defineEmits<{
  drink: [];
  cancel: [drinkId: number];
}>();
</script>
