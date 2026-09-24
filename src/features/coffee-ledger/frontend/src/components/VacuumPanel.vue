<template>
  <section class="panel">
    <h2>DB の整理</h2>
    <p class="muted">不要な領域を回収し、統計情報を更新します。台帳のデータは変わりません。</p>
    <button type="button" class="primary" :disabled="busy" @click="confirmVacuum">
      {{ running ? "整理中…" : "整理する" }}
    </button>
    <p v-if="elapsedSeconds !== null">DB の整理が完了しました（所要 {{ elapsedSeconds.toFixed(1) }} 秒）。</p>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  busy: boolean;
  running: boolean;
  elapsedSeconds: number | null;
}>();

const emit = defineEmits<{
  vacuum: [];
}>();

function confirmVacuum(): void {
  if (window.confirm("DB を整理します。よろしいですか？")) {
    emit("vacuum");
  }
}
</script>
