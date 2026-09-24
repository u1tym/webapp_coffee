export type ApiError = {
  code: string;
  message: string;
};

export type LastDrink = {
  id: number;
  recorded_at: string;
  cancelled: boolean;
};

export type Person = {
  id: number;
  name: string;
  display_order: number;
  deactivated: boolean;
  deactivated_at: string | null;
  unpaid_amount?: number;
  last_drink?: LastDrink | null;
};

export type Drink = {
  id: number;
  person_id: number;
  unit_price: number;
  recorded_at: string;
  cancelled: boolean;
  cancelled_at: string | null;
};

export type Payment = {
  id: number;
  person_id: number;
  amount: number;
  recorded_at: string;
  cancelled: boolean;
  cancelled_at: string | null;
};

export type CupPrice = {
  amount: number | null;
  updated_at: string | null;
};

export type Collection = {
  collected_amount: number;
  uncollected_amount: number;
  vault_amount: number;
};

export type SafeDeposit = {
  id: number;
  amount: number;
  deposited_at: string;
};

export type VaultOperation = {
  id: number;
  reason: string;
  direction: "deposit" | "withdrawal";
  amount: number;
  reason_date: string;
  entered_at: string;
};

export type SummaryEntry = {
  occurred_at: string;
  event_type: string;
  person_id: number | null;
  name: string | null;
  amount: number | null;
  direction: "deposit" | "withdrawal" | null;
  reason: string | null;
  reason_date: string | null;
  previous_amount: number | null;
  new_amount: number | null;
  uncollected_amount: number;
  collected_amount: number;
  vault_amount: number;
};

export type Summary = {
  uncollected_amount: number;
  collected_amount: number;
  vault_amount: number;
  entries: SummaryEntry[];
};

export type UnpaidAdjustment = {
  id: number;
  person_id: number;
  previous_amount: number;
  new_amount: number;
  reason: string;
  occurred_at: string;
};

export type VacuumResult = {
  elapsed_seconds: number;
};

export type OperationLog = {
  id: number;
  occurred_at: string;
  operation_type: string;
  payload: Record<string, unknown>;
};
