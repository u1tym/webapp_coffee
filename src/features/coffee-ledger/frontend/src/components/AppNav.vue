<template>
  <header class="nav">
    <RouterLink class="brand" to="/">珈琲台帳</RouterLink>
    <nav class="links">
      <RouterLink to="/">飲む</RouterLink>
      <RouterLink to="/admin">管理</RouterLink>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>
