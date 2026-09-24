<template>
  <main class="home-screen">
    <header class="home-bar">
      <CupPriceBanner :amount="cupPrice" />
      <CurrentDateTime />
      <p v-if="error" class="error compact">{{ error }}</p>
    </header>

    <div class="names-wrap">
      <PersonNameList
        :people="people"
        :can-drink="cupPrice !== null"
        :disabled="busy || drinkDialog"
        @pay="openPay"
        @drink="onDrink"
        @cancel-drink="onCancelDrink"
      />
    </div>

    <ModalDialog v-if="drinkDialog">
      <p class="modal-message">飲みました。</p>
      <button type="button" class="primary" @click="closeDrinkDialog">OK</button>
    </ModalDialog>

    <ModalDialog v-if="payPerson">
      <p class="modal-title">{{ payPerson.name }} の支払</p>
      <p>未払い {{ formatYen(payPerson.unpaid_amount ?? 0) }}</p>
      <form class="pay-form" @submit.prevent="confirmPay">
        <label>
          金額
          <span class="pay-stepper">
            <button
              type="button"
              :disabled="busy || !canDecreasePay"
              @click="adjustPay(-1)"
            >
              −
            </button>
            <input :value="payAmount" type="text" readonly :disabled="busy || (payPerson.unpaid_amount ?? 0) === 0" />
            <button
              type="button"
              :disabled="busy || !canIncreasePay"
              @click="adjustPay(1)"
            >
              ＋
            </button>
          </span>
        </label>
        <div class="modal-actions">
          <button type="submit" class="primary" :disabled="busy || !canConfirmPay">支払い確定</button>
          <button type="button" @click="closePay">閉じる</button>
        </div>
      </form>
      <p v-if="latestPayment && !latestPayment.cancelled" class="latest-pay">
        直近の支払 {{ formatDateTime(latestPayment.recorded_at) }} {{ formatYen(latestPayment.amount) }}
        <TrashButton :disabled="busy" label="直近の支払を取り消す" @click="onCancelPayment(latestPayment.id)" />
      </p>
    </ModalDialog>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  cancelDrink,
  cancelPayment,
  getCupPrice,
  getPerson,
  listPayments,
  listPeople,
  recordDrink,
  recordPayment,
} from "../api";
import { formatDateTime, formatYen, stepPayAmount } from "../format";
import type { ApiError, Payment, Person } from "../types";
import CupPriceBanner from "../components/CupPriceBanner.vue";
import CurrentDateTime from "../components/CurrentDateTime.vue";
import ModalDialog from "../components/ModalDialog.vue";
import PersonNameList from "../components/PersonNameList.vue";
import TrashButton from "../components/TrashButton.vue";

const people = ref<Person[]>([]);
const cupPrice = ref<number | null>(null);
const error = ref("");
const busy = ref(false);
const drinkDialog = ref(false);
const payPerson = ref<Person | null>(null);
const payments = ref<Payment[]>([]);
const payAmount = ref(0);

const latestPayment = computed(() => payments.value[0] ?? null);

const canConfirmPay = computed(() => {
  const unpaid = payPerson.value?.unpaid_amount ?? 0;
  const value = Number(payAmount.value);
  return unpaid > 0 && Number.isInteger(value) && value >= 1 && value <= unpaid;
});

const canDecreasePay = computed(() => {
  const unpaid = payPerson.value?.unpaid_amount ?? 0;
  if (unpaid < 10) {
    return false;
  }
  return payAmount.value > 10;
});

const canIncreasePay = computed(() => {
  const unpaid = payPerson.value?.unpaid_amount ?? 0;
  return unpaid > 0 && payAmount.value < unpaid;
});

function adjustPay(delta: -1 | 1): void {
  const unpaid = payPerson.value?.unpaid_amount ?? 0;
  payAmount.value = stepPayAmount(payAmount.value, unpaid, delta);
}

async function loadList(): Promise<void> {
  const [peopleRes, priceRes] = await Promise.all([listPeople("active"), getCupPrice()]);
  people.value = peopleRes.people;
  cupPrice.value = priceRes.amount;
}

onMounted(() => {
  void loadList().catch((err: ApiError) => {
    error.value = err.message;
  });
});

async function refreshPayPerson(personId: number): Promise<void> {
  const [personRes, paymentsRes] = await Promise.all([
    getPerson(personId),
    listPayments(personId),
  ]);
  payPerson.value = personRes;
  payments.value = paymentsRes.payments;
  payAmount.value = personRes.unpaid_amount ?? 0;
}

async function onDrink(personId: number): Promise<void> {
  if (busy.value || drinkDialog.value) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await recordDrink(personId);
    await loadList();
    drinkDialog.value = true;
  } catch (err) {
    error.value = (err as ApiError).message;
    busy.value = false;
  }
}

function closeDrinkDialog(): void {
  drinkDialog.value = false;
  busy.value = false;
}

async function openPay(personId: number): Promise<void> {
  error.value = "";
  try {
    await refreshPayPerson(personId);
  } catch (err) {
    error.value = (err as ApiError).message;
  }
}

function closePay(): void {
  payPerson.value = null;
  payments.value = [];
}

async function confirmPay(): Promise<void> {
  const current = payPerson.value;
  if (!current || !canConfirmPay.value || busy.value) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await recordPayment(current.id, Number(payAmount.value));
    await loadList();
    payPerson.value = null;
    payments.value = [];
  } catch (err) {
    error.value = (err as ApiError).message;
  } finally {
    busy.value = false;
  }
}

async function onCancelDrink(personId: number, drinkId: number): Promise<void> {
  if (busy.value || drinkId === 0) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await cancelDrink(personId, drinkId);
    await loadList();
  } catch (err) {
    error.value = (err as ApiError).message;
  } finally {
    busy.value = false;
  }
}

async function onCancelPayment(paymentId: number): Promise<void> {
  const current = payPerson.value;
  if (!current || busy.value) {
    return;
  }
  busy.value = true;
  error.value = "";
  try {
    await cancelPayment(current.id, paymentId);
    await loadList();
    await refreshPayPerson(current.id);
  } catch (err) {
    error.value = (err as ApiError).message;
  } finally {
    busy.value = false;
  }
}
</script>
