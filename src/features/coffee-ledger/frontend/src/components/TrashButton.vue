<template>
  <button type="button" class="icon-btn" :disabled="disabled" :aria-label="label" @click="$emit('click')">
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
      <path
        fill="currentColor"
        d="M9 3h6l1 2h4v2H4V5h4l1-2zm1 6h2v10h-2V9zm4 0h2v10h-2V9zM7 8h10l-.8 11.2A2 2 0 0 1 14.2 21H9.8a2 2 0 0 1-2-1.8L7 8z"
      />
    </svg>
  </button>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    disabled?: boolean;
    label?: string;
  }>(),
  {
    disabled: false,
    label: "取り消し",
  },
);

defineEmits<{
  click: [];
}>();
</script>
