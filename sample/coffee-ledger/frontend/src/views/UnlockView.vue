<template>
  <main class="page">
    <h1>管理パスワード</h1>
    <p class="muted">管理機能を使うにはパスワードを入力してください。</p>
    <AdminPasswordForm @success="onSuccess" @cancel="onCancel" />
  </main>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import AdminPasswordForm from "../components/AdminPasswordForm.vue";
import { safeAdminNext, unlockAdmin } from "../adminGate";

const router = useRouter();
const route = useRoute();

function onSuccess(): void {
  unlockAdmin();
  void router.replace(safeAdminNext(route.query.next));
}

function onCancel(): void {
  void router.replace("/");
}
</script>
