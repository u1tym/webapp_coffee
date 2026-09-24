import type {
  ApiError,
  Collection,
  CupPrice,
  Drink,
  OperationLog,
  Payment,
  Person,
  SafeDeposit,
  Summary,
  UnpaidAdjustment,
  VaultOperation,
} from "./types";

const apiBase = import.meta.env.VITE_API_COFFEE_LEDGER_URL;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${apiBase}${path}`, { cache: "no-store", ...init, headers });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const error = (body as { error?: ApiError } | null)?.error;
    throw (error ?? {
      code: "INTERNAL_ERROR",
      message: "通信に失敗しました。",
    }) satisfies ApiError;
  }
  return body as T;
}

export function listPeople(scope: "active" | "all" = "active"): Promise<{ people: Person[] }> {
  return request(`/people?scope=${scope}`);
}

export function createPerson(name: string): Promise<Person> {
  return request("/people", { method: "POST", body: JSON.stringify({ name }) });
}

export function getPerson(personId: number): Promise<Person> {
  return request(`/people/${personId}`);
}

export function deactivatePerson(personId: number): Promise<Person> {
  return request(`/people/${personId}/deactivate`, { method: "POST" });
}

export function updateDisplayOrder(personIds: number[]): Promise<{ people: Person[] }> {
  return request("/people/display-order", {
    method: "PUT",
    body: JSON.stringify({ person_ids: personIds }),
  });
}

export function listDrinks(personId: number): Promise<{ drinks: Drink[] }> {
  return request(`/people/${personId}/drinks`);
}

export function recordDrink(personId: number): Promise<Drink> {
  return request(`/people/${personId}/drinks`, { method: "POST" });
}

export function cancelDrink(personId: number, drinkId: number): Promise<Drink> {
  return request(`/people/${personId}/drinks/${drinkId}/cancel`, { method: "POST" });
}

export function listPayments(personId: number): Promise<{ payments: Payment[] }> {
  return request(`/people/${personId}/payments`);
}

export function recordPayment(personId: number, amount: number): Promise<Payment> {
  return request(`/people/${personId}/payments`, {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export function cancelPayment(personId: number, paymentId: number): Promise<Payment> {
  return request(`/people/${personId}/payments/${paymentId}/cancel`, { method: "POST" });
}

export function getCupPrice(): Promise<CupPrice> {
  return request("/cup-price");
}

export function setCupPrice(amount: number): Promise<CupPrice> {
  return request("/cup-price", { method: "PUT", body: JSON.stringify({ amount }) });
}

export function getCollection(): Promise<Collection> {
  return request("/collection");
}

export function listSafeDeposits(): Promise<{ safe_deposits: SafeDeposit[] }> {
  return request("/safe-deposits");
}

export function createSafeDeposit(): Promise<SafeDeposit> {
  return request("/safe-deposits", { method: "POST" });
}

export function createVaultOperation(body: {
  reason: string;
  direction: "deposit" | "withdrawal";
  amount: number;
  reason_date: string;
}): Promise<VaultOperation> {
  return request("/vault-operations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function createUnpaidAdjustment(
  personId: number,
  newAmount: number,
  reason: string,
): Promise<UnpaidAdjustment> {
  return request(`/people/${personId}/unpaid-adjustments`, {
    method: "POST",
    body: JSON.stringify({ new_amount: newAmount, reason }),
  });
}

export function getSummary(): Promise<Summary> {
  return request("/summary");
}

export function listOperationLogs(): Promise<{ operation_logs: OperationLog[] }> {
  return request("/operation-logs");
}
