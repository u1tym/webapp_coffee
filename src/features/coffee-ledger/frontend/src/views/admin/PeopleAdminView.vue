<template>
  <main class="page">
    <p><RouterLink to="/admin">← 管理トップ</RouterLink></p>
    <h1>人の管理</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <PersonAdminList
      :people="people"
      :busy="busy"
      @register="onRegister"
      @select="onSelect"
      @deactivate="onDeactivate"
      @move="onMove"
    />
    <section v-if="selected" class="panel">
      <h2>{{ selected.name }} の記録</h2>
      <p>未払い {{ formatYen(selected.unpaid_amount ?? 0) }}</p>
      <UnpaidAdjustmentForm
        :person-name="selected.name"
        :current-amount="selected.unpaid_amount ?? 0"
        :busy="busy"
        @adjust="onAdjust"
      />
      <DrinkPanel :drinks="drinks" title="飲用記録" />
      <PaymentPanel :payments="payments" title="支払記録" />
    </section>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import {
  createPerson,
  createUnpaidAdjustment,
  deactivatePerson,
  getPerson,
  listDrinks,
  listPayments,
  listPeople,
  updateDisplayOrder,
} from "../../api";
import { formatYen } from "../../format";
import type { ApiError, Drink, Payment, Person } from "../../types";
import DrinkPanel from "../../components/DrinkPanel.vue";
import PaymentPanel from "../../components/PaymentPanel.vue";
import PersonAdminList from "../../components/PersonAdminList.vue";
import UnpaidAdjustmentForm from "../../components/UnpaidAdjustmentForm.vue";

const people = ref<Person[]>([]);
const selected = ref<Person | null>(null);
const drinks = ref<Drink[]>([]);
const payments = ref<Payment[]>([]);
const error = ref("");
const busy = ref(false);

async function loadPeople(): Promise<void> {
  const res = await listPeople("all");
  people.value = res.people;
}

onMounted(() => {
  void loadPeople().catch((err: ApiError) => {
    error.value = err.message;
  });
});

async function loadSelected(personId: number): Promise<void> {
  const [personRes, drinksRes, paymentsRes] = await Promise.all([
    getPerson(personId),
    listDrinks(personId),
    listPayments(personId),
  ]);
  selected.value = personRes;
  drinks.value = drinksRes.drinks;
  payments.value = paymentsRes.payments;
}

async function run(action: () => Promise<void>): Promise<void> {
  if (busy.value) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await action();
    await loadPeople();
    if (selected.value) {
      await loadSelected(selected.value.id);
    }
  } catch (err) {
    error.value = (err as ApiError).message;
  } finally {
    busy.value = false;
  }
}

function onRegister(name: string): void {
  void run(async () => {
    await createPerson(name);
  });
}

function onSelect(personId: number): void {
  void run(async () => {
    await loadSelected(personId);
  });
}

function onDeactivate(personId: number): void {
  void run(async () => {
    await deactivatePerson(personId);
  });
}

function onAdjust(payload: { new_amount: number; reason: string }): void {
  const personId = selected.value?.id;
  if (personId === undefined) {
    return;
  }
  void run(async () => {
    await createUnpaidAdjustment(personId, payload.new_amount, payload.reason);
  });
}

function onMove(personId: number, delta: number): void {
  const ids = people.value.map((person) => person.id);
  const index = ids.indexOf(personId);
  const next = index + delta;
  if (index < 0 || next < 0 || next >= ids.length) {
    return;
  }
  const swapped = [...ids];
  const current = swapped[index];
  const neighbor = swapped[next];
  if (current === undefined || neighbor === undefined) {
    return;
  }
  swapped[index] = neighbor;
  swapped[next] = current;
  void run(async () => {
    await updateDisplayOrder(swapped);
  });
}
</script>
