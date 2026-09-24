<template>
  <ul v-if="people.length > 0" class="person-rows">
    <li v-for="person in people" :key="person.id" class="person-row">
      <span class="person-name">{{ person.name }}</span>
      <button
        type="button"
        class="unpaid-btn"
        :disabled="disabled || (person.unpaid_amount ?? 0) === 0"
        @click="$emit('pay', person.id)"
      >
        {{ formatYen(person.unpaid_amount ?? 0) }}
      </button>
      <button
        type="button"
        class="drink-btn"
        :disabled="disabled || !canDrink"
        @click="$emit('drink', person.id)"
      >
        飲む
      </button>
      <span
        class="last-drink"
        :class="{ cancelled: person.last_drink?.cancelled }"
      >
        <template v-if="person.last_drink">
          {{ formatDateTime(person.last_drink.recorded_at).replace(" ", "\n") }}
        </template>
        <template v-else>—</template>
      </span>
      <TrashButton
        :disabled="disabled || !person.last_drink || person.last_drink.cancelled"
        @click="$emit('cancel-drink', person.id, person.last_drink?.id ?? 0)"
      />
    </li>
  </ul>
  <p v-else class="muted">利用中の人はいません。</p>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { Person } from "../types";
import TrashButton from "./TrashButton.vue";

defineProps<{
  people: Person[];
  canDrink: boolean;
  disabled: boolean;
}>();

defineEmits<{
  pay: [personId: number];
  drink: [personId: number];
  "cancel-drink": [personId: number, drinkId: number];
}>();
</script>
