<template>
  <section class="panel ledger-panel">
    <h2>集計</h2>
    <div class="ledger-totals">
      <p>未徴収 {{ formatYen(uncollectedAmount) }}</p>
      <p>徴収済み {{ formatYen(collectedAmount) }}</p>
      <p>金庫 {{ formatYen(vaultAmount) }}</p>
    </div>
    <p>
      <button type="button" class="primary" :disabled="busy" @click="$emit('export-csv')">CSV 出力</button>
    </p>
    <div v-if="entries.length > 0" class="ledger-scroll">
      <table class="log-table ledger-table">
        <thead>
          <tr>
            <th>日時</th>
            <th>契機</th>
            <th>内容</th>
            <th class="num">未徴収</th>
            <th class="num">徴収済み</th>
            <th class="num">金庫</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(entry, index) in entries" :key="`${entry.occurred_at}-${entry.event_type}-${index}`">
            <td class="nowrap">{{ formatDateTime(entry.occurred_at) }}</td>
            <td class="nowrap">{{ eventLabel(entry) }}</td>
            <td>{{ entryDetail(entry) }}</td>
            <td class="num">{{ formatYen(entry.uncollected_amount) }}</td>
            <td class="num">{{ formatYen(entry.collected_amount) }}</td>
            <td class="num">{{ formatYen(entry.vault_amount) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-else class="muted">変化はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { SummaryEntry } from "../types";

defineProps<{
  uncollectedAmount: number;
  collectedAmount: number;
  vaultAmount: number;
  entries: SummaryEntry[];
  busy: boolean;
}>();

defineEmits<{
  "export-csv": [];
}>();

const eventLabels: Record<string, string> = {
  drink_recorded: "飲む",
  drink_cancelled: "飲用の取り消し",
  payment_recorded: "支払",
  payment_cancelled: "支払の取り消し",
  safe_deposited: "金庫収納",
  vault_operated: "金庫操作",
  unpaid_adjusted: "未払い修正",
};

function eventLabel(entry: SummaryEntry): string {
  if (entry.event_type === "vault_operated") {
    return entry.direction === "withdrawal" ? "金庫操作（出金）" : "金庫操作（入金）";
  }
  return eventLabels[entry.event_type] ?? entry.event_type;
}

function entryDetail(entry: SummaryEntry): string {
  if (entry.event_type === "unpaid_adjusted") {
    const parts: string[] = [];
    if (entry.name) {
      parts.push(entry.name);
    }
    parts.push(`${formatYen(entry.previous_amount ?? 0)} → ${formatYen(entry.new_amount ?? 0)}`);
    if (entry.reason) {
      parts.push(entry.reason);
    }
    return parts.join(" · ");
  }
  const parts: string[] = [];
  if (entry.name) {
    parts.push(entry.name);
  }
  if (entry.reason) {
    parts.push(entry.reason);
  }
  if (entry.reason_date) {
    parts.push(entry.reason_date);
  }
  parts.push(formatYen(entry.amount ?? 0));
  return parts.join(" · ");
}
</script>
