# 珈琲台帳（coffee-ledger） API設計

> テーブル定義と ER 図は書かない（`db-design.md` を参照）。画面レイアウト・部品配置は書かない（`ui-design.md`）。Vue コンポーネント構成は `design.md`。

## 共通事項

- ベース URL: `VITE_API_COFFEE_LEDGER_URL`（フロントの環境変数。開発は `http://localhost:8010`、本番は `.env.production` で設定。詳細は `rules/11-frontend.md`、`design.md`）
- 認証: 認証しない。すべてのエンドポイントを誰でも呼べる（`rules/14-security.md`）。管理パスワードは API では扱わない。
- 形式: 要求・応答とも JSON（UTF-8）。要求本文がある場合は `Content-Type: application/json`。
- 日時: 日本時間の ISO 8601（秒まで、時差付き）。例: `"2026-09-24T14:12:05+09:00"`。日付は `"YYYY-MM-DD"`。
- 金額: 円単位の整数。
- 要求本文の検証:
  - 定義にない項目があれば入力不正とする。
  - 整数の項目は JSON の整数だけを受け付ける（`1.0`、`"1"`、`true` は入力不正）。
  - 文字列の項目は前後の空白を除いてから長さを確かめ、除いた値を保存する。
- パスの `{person_id}` などの ID は整数。整数でなければ入力不正とする。
- トランザクション: 1 要求 = 1 トランザクション。応答が 400 以上の場合は、途中の変更（操作記録を含む）をすべて取り消す。
- CORS: `CORS_ORIGINS` に書いたオリジンだけを許可する。資格情報（Cookie）は許可しない。

### エラー応答

エラーは次の形で返す。`message` は画面にそのまま出せる日本語。

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力が正しくありません。"
  }
}
```

### 共通エラー

| HTTP ステータス | code | message | 状況 |
|------|------|------|------|
| 400 | VALIDATION_ERROR | 入力が正しくありません。 | 入力不正（要求本文・クエリ・パスの形や値が不正） |
| 404 | NOT_FOUND | 対象が見つかりません。 | パスで指定した人・飲用・支払が無い |
| 500 | INTERNAL_ERROR | 処理に失敗しました。 | サーバ内部エラー |

- 入力不正は、参考実装に合わせて 422 ではなく 400 で返す。
- 認証しないため、401 / 403 は使わない。
- 業務上の拒否は 409 で返し、`code` で理由を区別する（各エンドポイントのエラー欄）。
- 定義していないパスへの要求は、FastAPI の既定の 404 応答とする。

### 共通の応答オブジェクト

**Person（人）**

```json
{
  "id": 1,
  "name": "山田",
  "display_order": 1,
  "deactivated": false,
  "deactivated_at": null,
  "unpaid_amount": 300,
  "last_drink": {
    "id": 12,
    "recorded_at": "2026-09-24T09:15:00+09:00",
    "cancelled": false
  }
}
```

| 項目 | 型 | 説明 |
|------|----|------|
| id | integer | 人の ID |
| name | string | 名前 |
| display_order | integer | 表示順 |
| deactivated | boolean | 利用停止していれば true |
| deactivated_at | string \| null | 利用停止した日時 |
| unpaid_amount | integer | 未払い代金（0 以上） |
| last_drink | object \| null | 最後の飲用（取り消し済みを含む、記録日時が最も新しいもの）。無ければ null |

**Drink（飲用）**

```json
{
  "id": 12,
  "person_id": 1,
  "unit_price": 100,
  "recorded_at": "2026-09-24T09:15:00+09:00",
  "cancelled": false,
  "cancelled_at": null
}
```

**Payment（支払）**

```json
{
  "id": 5,
  "person_id": 1,
  "amount": 300,
  "recorded_at": "2026-09-24T12:00:00+09:00",
  "cancelled": false,
  "cancelled_at": null
}
```

## エンドポイント一覧

| メソッド | パス | 認証 | 概要 | 関連要件 |
|----------|------|------|------|----------|
| GET | /people | 不要 | 人の一覧 | REQ-002、REQ-012〜014 |
| POST | /people | 不要 | 人の登録 | REQ-012 |
| PUT | /people/display-order | 不要 | 表示順の変更 | REQ-014 |
| GET | /people/{person_id} | 不要 | 人の取得 | REQ-005、REQ-015 |
| POST | /people/{person_id}/deactivate | 不要 | 人の利用停止 | REQ-013 |
| GET | /people/{person_id}/drinks | 不要 | 飲用記録の一覧 | REQ-015 |
| POST | /people/{person_id}/drinks | 不要 | 飲用の記録 | REQ-003 |
| POST | /people/{person_id}/drinks/{drink_id}/cancel | 不要 | 飲用の取り消し | REQ-004 |
| GET | /people/{person_id}/payments | 不要 | 支払記録の一覧 | REQ-006、REQ-015 |
| POST | /people/{person_id}/payments | 不要 | 支払の記録 | REQ-005 |
| POST | /people/{person_id}/payments/{payment_id}/cancel | 不要 | 支払の取り消し | REQ-006 |
| POST | /people/{person_id}/unpaid-adjustments | 不要 | 未払いの修正 | REQ-016 |
| GET | /cup-price | 不要 | 一杯単価の取得 | REQ-001、REQ-008 |
| PUT | /cup-price | 不要 | 一杯単価の登録・変更 | REQ-008 |
| GET | /collection | 不要 | 徴収状況の取得 | REQ-009 |
| GET | /safe-deposits | 不要 | 金庫収納の履歴 | REQ-010 |
| POST | /safe-deposits | 不要 | 金庫収納 | REQ-010 |
| POST | /vault-operations | 不要 | 金庫操作 | REQ-011 |
| GET | /summary | 不要 | 集計 | REQ-017 |
| GET | /operation-logs | 不要 | 操作記録の一覧 | REQ-018 |

参考実装にある `GET /vault-operations`（金庫操作の一覧）は、使う画面も要件も無いため設けない。

## エンドポイント詳細

### GET /people

- **認証**: 不要
- **要求**（クエリ）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| scope | string | 任意 | `active`（利用中の人だけ。既定）または `all`（利用停止した人を含む全員） |

- **応答（200）**: 表示順の昇順。

```json
{
  "people": [ /* Person の配列 */ ]
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `scope` が `active`・`all` 以外 |

### POST /people

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| name | string | 必須 | 名前。前後の空白を除いて 1〜100 文字 |

- **応答（201）**: 登録した Person（`unpaid_amount` は 0、`last_drink` は null）。表示順は既存の最大値 + 1。
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `name` が無い・文字列でない、空白を除いて空、100 文字超 |
| 409 NAME_DUPLICATE | 同じ名前の人（利用停止した人を含む）がいる。「同じ名前の人が既に登録されています。」 |

### PUT /people/display-order

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| person_ids | integer[] | 必須 | 新しい並びの人 ID。利用停止した人を含む全員を 1 回ずつ並べる。先頭から表示順 1, 2, … になる |

- **応答（200）**: 変更後の全員（`GET /people?scope=all` と同じ形）。

```json
{
  "people": [ /* Person の配列 */ ]
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `person_ids` が無い・空、整数でない要素がある、同じ ID が重複している |
| 409 DISPLAY_ORDER_MISMATCH | `person_ids` の集合が登録済みの全員と一致しない。「表示順の対象が登録済みの人と一致しません。」 |

### GET /people/{person_id}

- **認証**: 不要
- **要求**: パスの `person_id`
- **応答（200）**: Person
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い |

### POST /people/{person_id}/deactivate

- **認証**: 不要
- **要求**: パスの `person_id`。本文なし。
- **応答（200）**: 利用停止後の Person
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い |
| 409 ALREADY_DEACTIVATED | 既に利用停止している。「既に利用停止しています。」 |

### GET /people/{person_id}/drinks

- **認証**: 不要
- **要求**: パスの `person_id`
- **応答（200）**: その人の飲用（取り消し済みを含む）を記録日時の新しい順（同時刻は ID の大きい順）に並べる。

```json
{
  "drinks": [ /* Drink の配列 */ ]
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い |

### POST /people/{person_id}/drinks

- **認証**: 不要
- **要求**: パスの `person_id`。本文なし。
- **応答（201）**: 記録した Drink（`unit_price` はその時点の一杯単価）
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い |
| 409 PERSON_DEACTIVATED | 人が利用停止している。「利用停止した人には飲用を記録できません。」 |
| 409 CUP_PRICE_MISSING | 一杯単価が未登録。「一杯単価が未登録です。」 |

### POST /people/{person_id}/drinks/{drink_id}/cancel

- **認証**: 不要
- **要求**: パスの `person_id`、`drink_id`。本文なし。
- **応答（200）**: 取り消した Drink（`cancelled` は true）
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い、飲用が無い、飲用がその人のものでない |
| 409 ALREADY_CANCELLED | 既に取り消されている。「既に取り消されています。」 |
| 409 DRINK_CANCEL_WOULD_OVERPAY | 取り消すと未払い代金が 0 未満になる。「この飲用を取り消すと支払合計が飲用代金を超えます。」 |

API は最後の飲用以外の取り消しも受け付ける。最後の飲用に限るのは画面側の制約（REQ-004）である。

### GET /people/{person_id}/payments

- **認証**: 不要
- **要求**: パスの `person_id`
- **応答（200）**: その人の支払（取り消し済みを含む）を記録日時の新しい順（同時刻は ID の大きい順）に並べる。

```json
{
  "payments": [ /* Payment の配列 */ ]
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い |

### POST /people/{person_id}/payments

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| amount | integer | 必須 | 支払額。1 以上、その人の未払い代金以下 |

- **応答（201）**: 記録した Payment
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `amount` が無い・整数でない・1 未満 |
| 404 NOT_FOUND | 人が無い |
| 409 PAYMENT_EXCEEDS_UNPAID | 未払い代金が 0、または `amount` が未払い代金を超える。「支払額が未払い代金を超えています。」 |

### POST /people/{person_id}/payments/{payment_id}/cancel

- **認証**: 不要
- **要求**: パスの `person_id`、`payment_id`。本文なし。
- **応答（200）**: 取り消した Payment（`cancelled` は true）
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 404 NOT_FOUND | 人が無い、支払が無い、支払がその人のものでない |
| 409 ALREADY_CANCELLED | 既に取り消されている。「既に取り消されています。」 |

### POST /people/{person_id}/unpaid-adjustments

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| new_amount | integer | 必須 | 修正後の未払い代金。0 以上 |
| reason | string | 必須 | 事由。前後の空白を除いて 1〜200 文字 |

- **応答（201）**: 記録した未払い修正。`previous_amount` はサーバが計算した修正前の未払い代金。

```json
{
  "id": 3,
  "person_id": 1,
  "previous_amount": 300,
  "new_amount": 0,
  "reason": "現金で精算済み",
  "occurred_at": "2026-09-24T15:00:00+09:00"
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `new_amount` が無い・整数でない・0 未満。`reason` が無い・文字列でない、空白を除いて空、200 文字超 |
| 404 NOT_FOUND | 人が無い |
| 409 UNPAID_AMOUNT_UNCHANGED | `new_amount` が現在の未払い代金と同じ。「現在の未払い代金と同じ額には修正できません。」 |

### GET /cup-price

- **認証**: 不要
- **要求**: なし
- **応答（200）**: 未登録なら両方 null。

```json
{
  "amount": 100,
  "updated_at": "2026-09-01T10:00:00+09:00"
}
```

- **エラー**: 共通エラーのみ

### PUT /cup-price

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| amount | integer | 必須 | 一杯単価。1 以上 |

- **応答（200）**: 保存後の一杯単価（`GET /cup-price` と同じ形）。未登録なら登録、登録済みなら変更として操作記録に残す。
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | `amount` が無い・整数でない・1 未満 |

### GET /collection

- **認証**: 不要
- **要求**: なし
- **応答（200）**

```json
{
  "collected_amount": 1200,
  "uncollected_amount": 3400,
  "vault_amount": 15000
}
```

| 項目 | 説明 |
|------|------|
| collected_amount | 徴収済み金額 |
| uncollected_amount | 未徴収金額 |
| vault_amount | 金庫金額 |

- **エラー**: 共通エラーのみ

### GET /safe-deposits

- **認証**: 不要
- **要求**: なし
- **応答（200）**: 収納日時の新しい順（同時刻は ID の大きい順）。

```json
{
  "safe_deposits": [
    { "id": 2, "amount": 1200, "deposited_at": "2026-09-20T18:00:00+09:00" }
  ]
}
```

- **エラー**: 共通エラーのみ

### POST /safe-deposits

- **認証**: 不要
- **要求**: 本文なし。収納額はサーバが計算した徴収済み金額の全額。
- **応答（201）**: 記録した金庫収納（`GET /safe-deposits` の要素と同じ形）
- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 409 COLLECTED_AMOUNT_ZERO | 徴収済み金額が 0。「徴収済み金額が 0 のため金庫収納できません。」 |

### POST /vault-operations

- **認証**: 不要
- **要求**（本文）

| 項目 | 型 | 必須 | 説明 |
|------|----|----|------|
| reason | string | 必須 | 事由。前後の空白を除いて 1〜200 文字 |
| direction | string | 必須 | `deposit`（入金）または `withdrawal`（出金） |
| amount | integer | 必須 | 金額。1 以上。出金なら金庫金額以下 |
| reason_date | string | 必須 | 事由の日付（`YYYY-MM-DD`） |

- **応答（201）**

```json
{
  "id": 4,
  "reason": "コーヒー豆の購入",
  "direction": "withdrawal",
  "amount": 2500,
  "reason_date": "2026-09-24",
  "entered_at": "2026-09-24T15:10:00+09:00"
}
```

- **エラー**

| HTTP ステータス | 条件 |
|------|------|
| 400 VALIDATION_ERROR | いずれかの項目が無い。`reason` が空白を除いて空・200 文字超。`direction` が `deposit`・`withdrawal` 以外。`amount` が整数でない・1 未満。`reason_date` が日付として不正 |
| 409 VAULT_AMOUNT_EXCEEDED | 出金で `amount` が金庫金額を超える。「出金額が金庫金額を超えています。」 |

### GET /summary

- **認証**: 不要
- **要求**: なし
- **応答（200）**: 現在の 3 つの金額と、金額を変えた出来事の一覧（新しい順）。積み上げ方は `design.md`「集計」に従う。

```json
{
  "uncollected_amount": 3400,
  "collected_amount": 1200,
  "vault_amount": 15000,
  "entries": [
    {
      "occurred_at": "2026-09-24T15:10:00+09:00",
      "event_type": "vault_operated",
      "person_id": null,
      "name": null,
      "amount": 2500,
      "direction": "withdrawal",
      "reason": "コーヒー豆の購入",
      "reason_date": "2026-09-24",
      "previous_amount": null,
      "new_amount": null,
      "uncollected_amount": 3400,
      "collected_amount": 1200,
      "vault_amount": 15000
    }
  ]
}
```

`entries` の各項目:

| 項目 | 型 | 説明 |
|------|----|------|
| occurred_at | string | 出来事の日時（飲用・支払は記録日時、取り消しは取り消し日時、金庫収納は収納日時、金庫操作は記録日時、未払い修正は修正日時） |
| event_type | string | `drink_recorded` / `drink_cancelled` / `payment_recorded` / `payment_cancelled` / `safe_deposited` / `vault_operated` / `unpaid_adjusted` |
| person_id | integer \| null | 人の ID（飲用・支払・未払い修正のみ） |
| name | string \| null | 人の現在の名前（飲用・支払・未払い修正のみ） |
| amount | integer \| null | 金額（単価・支払額・収納額・操作額）。未払い修正は null |
| direction | string \| null | 金庫操作のみ。`deposit` / `withdrawal` |
| reason | string \| null | 金庫操作・未払い修正のみ。事由 |
| reason_date | string \| null | 金庫操作のみ。事由の日付 |
| previous_amount | integer \| null | 未払い修正のみ。修正前の額 |
| new_amount | integer \| null | 未払い修正のみ。修正後の額 |
| uncollected_amount | integer | 出来事の直後の未徴収金額 |
| collected_amount | integer | 出来事の直後の徴収済み金額 |
| vault_amount | integer | 出来事の直後の金庫金額 |

- **エラー**: 共通エラーのみ

### GET /operation-logs

- **認証**: 不要
- **要求**: なし
- **応答（200）**: 操作日時の新しい順（同時刻は ID の大きい順）。`operation_type` と `payload` の項目は `db-design.md`「操作の種類と payload の項目」に従う。

```json
{
  "operation_logs": [
    {
      "id": 40,
      "occurred_at": "2026-09-24T15:10:00+09:00",
      "operation_type": "payment_recorded",
      "payload": { "person_id": 1, "name": "山田", "payment_id": 5, "amount": 300 }
    }
  ]
}
```

- **エラー**: 共通エラーのみ

## 承認

現在の状態: 承認済み

| 日時 | 状態 | 変更概要 |
|------|------|----------|
| 2026-09-24 14:27 | 未承認 | 初版 |
| 2026-09-24 14:29 | 承認済み | 初版を承認 |
