<template>
  <div class="order-controls">
    <button type="button" :disabled="busy || index <= 0" @click="$emit('move', -1)">一つ上へ</button>
    <button type="button" :disabled="busy || index < 0 || index >= lastIndex" @click="$emit('move', 1)">
      一つ下へ
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  index: number;
  lastIndex: number;
  busy: boolean;
}>();

defineEmits<{
  move: [delta: number];
}>();
</script>
