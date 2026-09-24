<template>
  <section class="panel">
    <h2>操作記録</h2>
    <table class="log-table">
      <thead>
        <tr>
          <th>日時</th>
          <th>操作</th>
          <th>内容</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in logs" :key="item.id">
          <td>{{ formatDateTime(item.occurred_at) }}</td>
          <td>{{ labelOf(item.operation_type) }}</td>
          <td>{{ detailOf(item) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="logs.length === 0" class="muted">操作記録はまだありません。</p>
  </section>
</template>

<script setup lang="ts">
import { formatDateTime, formatYen } from "../format";
import type { OperationLog } from "../types";

defineProps<{
  logs: OperationLog[];
}>();

const labels: Record<string, string> = {
  person_registered: "人の登録",
  person_deactivated: "人の利用停止",
  display_order_changed: "表示順の変更",
  cup_price_registered: "一杯単価の登録",
  cup_price_updated: "一杯単価の変更",
  drink_recorded: "飲用の記録",
  drink_cancelled: "飲用の取り消し",
  payment_recorded: "支払の記録",
  payment_cancelled: "支払の取り消し",
  safe_deposited: "金庫収納",
  vault_operated: "金庫操作",
  unpaid_adjusted: "未払い修正",
};

function labelOf(type: string): string {
  return labels[type] ?? type;
}

function detailOf(item: OperationLog): string {
  const payload = item.payload;
  switch (item.operation_type) {
    case "person_registered":
    case "person_deactivated":
      return String(payload.name ?? "");
    case "display_order_changed":
      return `人ID: ${Array.isArray(payload.person_ids) ? payload.person_ids.join(", ") : ""}`;
    case "cup_price_registered":
      return formatYen(Number(payload.amount ?? 0));
    case "cup_price_updated":
      return `${formatYen(Number(payload.previous_amount ?? 0))} → ${formatYen(Number(payload.amount ?? 0))}`;
    case "drink_recorded":
    case "drink_cancelled":
      return `${String(payload.name ?? "")} · ${formatYen(Number(payload.unit_price ?? 0))}`;
    case "payment_recorded":
    case "payment_cancelled":
      return `${String(payload.name ?? "")} · ${formatYen(Number(payload.amount ?? 0))}`;
    case "safe_deposited":
      return formatYen(Number(payload.amount ?? 0));
    case "vault_operated":
      return `${payload.direction === "withdrawal" ? "出金" : "入金"} · ${formatYen(Number(payload.amount ?? 0))} · ${String(payload.reason ?? "")}`;
    case "unpaid_adjusted":
      return `${String(payload.name ?? "")} · ${formatYen(Number(payload.previous_amount ?? 0))} → ${formatYen(Number(payload.new_amount ?? 0))} · ${String(payload.reason ?? "")}`;
    default:
      return JSON.stringify(payload);
  }
}
</script>
