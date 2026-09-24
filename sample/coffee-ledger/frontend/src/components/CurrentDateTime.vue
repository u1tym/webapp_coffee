<template>
  <p class="current-datetime" aria-live="polite">{{ text }}</p>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { formatNowJst } from "../format";

const text = ref(formatNowJst());
let timer = 0;

onMounted(() => {
  text.value = formatNowJst();
  timer = window.setInterval(() => {
    text.value = formatNowJst();
  }, 1000);
});

onUnmounted(() => {
  window.clearInterval(timer);
});
</script>
