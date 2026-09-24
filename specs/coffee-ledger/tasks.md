# 珈琲台帳（coffee-ledger） タスク分解

> `design.md` / `ui-design.md` / `db-design.md` / `api-design.md` がすべて承認された後に作成する。
> タスクは 1〜4 時間程度で完了できる粒度にする。

- 実装パスの `<cl>` は `src/features/coffee-ledger` を表す。
- 参考実装 `sample/coffee-ledger` を元にし、設計書と食い違う点は設計書に合わせる（`design.md`「全体構成」の差分表）。
- 各 API タスクでは、`design.md`「ログ」に従うログ出力（入力を INF、成功を INF、業務上の拒否を WRN と理由、想定外の例外を ERR）も合わせて実装する。
- 画面のタスクでは、`rules/15-ui-style.md` の見た目と、`ui-design.md` の状態別の表示に合わせる。参考実装の部品のうち、設計で使わない表示モード（例: 飲用記録・支払記録の部品にある記録ボタンや支払フォーム）は作らない。

## タスク一覧

### バックエンド

| No | タスク | 対応する要件/設計 | 実装パス | 所要時間 | 完了条件 |
|----|--------|--------------------|----------|----------|----------|
| T-001 | バックエンドの土台を作る。`requirements.txt`、`.env`（`specs/templates/backend.env.example` に従う）、`.gitignore`（`venv/`、`log/`、`.env`）、`config.py`、`timeutil.py`、`errors.py`（共通のエラー応答）、`logging_setup.py`、`db.py`（要求ごとの接続とコミット／ロールバック）、`main.py`（CORS は資格情報なし） | REQ-019、REQ-020 / design.md「バックエンド設計」「ログ」、api-design.md「共通事項」 | `<cl>/backend/` | 3h | `backend/venv` で `uvicorn app.main:app --port 8010` が起動する。必須の設定値が無いと起動時にエラーで止まる。入力不正は 400 の `VALIDATION_ERROR`、想定外の例外は 500 の `INTERNAL_ERROR` の形で返る。`backend/log/coffee-ledger.log` に「日時 区分 メッセージ」の形で出力され、`LOG_MAX_BYTES`・`LOG_BACKUP_COUNT` でローテーションする |
| T-002 | 初期構築用 SQL を作る。`sql/migrations/` を空のディレクトリとして用意する | db-design.md 全体、「SQL ファイル」 / design.md「DB の構築」 | `<cl>/backend/sql/` | 2h | 空の `tstdb` に `psql` で `init/001_schema.sql` を実行すると、スキーマ `coffee_ledger` と 8 テーブル・制約・インデックスが db-design.md どおりにできる。2 回続けて実行してもエラーにならない |
| T-003 | 金額計算（`services/balances.py`）と操作記録（`services/operations.py` の追加と一覧）、`GET /operation-logs` を作る | REQ-018 / design.md「業務ロジック（金額の計算）」、api-design.md「GET /operation-logs」 | `<cl>/backend/app/services/`、`<cl>/backend/app/routers/` | 2h | 未払い代金・未徴収金額・徴収済み金額・金庫金額が design.md の式どおりに計算される（0 未満は 0）。金庫用の advisory lock を取る関数がある。`GET /operation-logs` が新しい順で返る |
| T-004 | 一杯単価の API（`GET /cup-price`、`PUT /cup-price`）を作る | REQ-001、REQ-008 / api-design.md「GET /cup-price」「PUT /cup-price」 | `<cl>/backend/app/` | 1h | 未登録のとき `GET` が両方 null を返す。`PUT` で登録と変更ができ、登録は `cup_price_registered`、変更は変更前の額付きで `cup_price_updated` の操作記録が残る。1 未満や整数でない値は 400 |
| T-005 | 人の API（`GET /people`、`POST /people`、`GET /people/{person_id}`、`POST /people/{person_id}/deactivate`、`PUT /people/display-order`）を作る | REQ-002、REQ-012〜014 / design.md「各操作の流れ」、api-design.md 該当節 | `<cl>/backend/app/` | 3h | api-design.md の応答（Person の `unpaid_amount`・`last_drink` を含む）とエラー（`NAME_DUPLICATE`、`ALREADY_DEACTIVATED`、`DISPLAY_ORDER_MISMATCH` など）どおりに動く。登録は表示順の末尾に入る。表示順の変更は 1 から振り直され、一意制約に触れない。各操作の操作記録が残る |
| T-006 | 飲用の API（一覧、記録、取り消し）を作る | REQ-003、REQ-004、REQ-015 / design.md「各操作の流れ」、api-design.md 該当節 | `<cl>/backend/app/` | 2h | 記録した飲用がその時点の単価を持つ。`PERSON_DEACTIVATED`、`CUP_PRICE_MISSING`、`ALREADY_CANCELLED`、`DRINK_CANCEL_WOULD_OVERPAY`、404 が条件どおりに返る。人を行ロックしてから処理する。操作記録が残る |
| T-007 | 支払の API（一覧、記録、取り消し）と未払い修正の API を作る | REQ-005、REQ-006、REQ-015、REQ-016 / design.md「各操作の流れ」、api-design.md 該当節 | `<cl>/backend/app/` | 3h | `PAYMENT_EXCEEDS_UNPAID`、`ALREADY_CANCELLED`、`UNPAID_AMOUNT_UNCHANGED`、400、404 が条件どおりに返る。未払い修正の `previous_amount` はサーバが計算した値になる。人を行ロックしてから処理する。操作記録が残る |
| T-008 | 徴収・金庫の API（`GET /collection`、`GET /safe-deposits`、`POST /safe-deposits`、`POST /vault-operations`）を作る | REQ-009〜011 / design.md「各操作の流れ」、api-design.md 該当節 | `<cl>/backend/app/` | 2h | 金庫収納は徴収済み金額の全額で記録され、その後の徴収済み金額が 0 になる。`COLLECTED_AMOUNT_ZERO`、`VAULT_AMOUNT_EXCEEDED`、400 が条件どおりに返る。金庫用のロックを取ってから計算する。操作記録が残る |
| T-009 | 集計の API（`GET /summary`）を作る | REQ-017 / design.md「業務ロジック（集計）」、api-design.md「GET /summary」 | `<cl>/backend/app/` | 2h | 7 種の出来事が design.md の規則で積み上げられ、新しい順で返る。支払の取り消しは、直前の金庫収納より後の支払のときだけ徴収済みを減らす。各金額は 0 未満にならない。先頭に現在の 3 つの金額が付く |
| T-010 | 本番用の起動スクリプト `start_gunicorn.sh` を作る | design.md「バックエンド設計（起動方法）」 | `<cl>/backend/` | 1h | `backend/venv` の gunicorn（uvicorn ワーカー）で `127.0.0.1:8010` に起動し、アクセスログとエラーログが `backend/log/` に出る |

### テスト

| No | タスク | 対応する要件/設計 | 実装パス | 所要時間 | 完了条件 |
|----|--------|--------------------|----------|----------|----------|
| T-011 | テストの土台を作る。`backend/venv` の pytest で `app` を import し、テストごとに DB 接続を開いて、テーブルを空にしてから実行し、最後にロールバックするフィクスチャを用意する | design.md「テスト」 | `<cl>/tests/` | 2h | `tests/` で pytest を実行でき、テストの後に開発用 DB のデータが残らない（変わらない） |
| T-012 | 人・飲用・支払・未払い修正の業務ロジックのテストを書く | REQ-003〜006、REQ-012〜014、REQ-016、REQ-021 / design.md「各操作の流れ」 | `<cl>/tests/` | 3h | 未払い代金の計算、各操作の拒否条件（重複名、利用停止、単価未登録、取り消し済み、取り消しで未払い代金が 0 未満、支払額の超過、同じ額への修正、表示順の不一致）、表示順の振り直しを確かめるテストがあり、すべて通る |
| T-013 | 金庫・集計・操作記録のテストを書く | REQ-009〜011、REQ-017、REQ-018、REQ-020 / design.md「業務ロジック」 | `<cl>/tests/` | 3h | 徴収済み金額（金庫収納の前後、支払の取り消し）、金庫金額、出金の上限、集計の積み上げ、操作記録の種類と payload を確かめるテストがあり、すべて通る。失敗した操作で記録も操作記録も残らないことを API 経由で確かめる |

### フロントエンド

| No | タスク | 対応する要件/設計 | 実装パス | 所要時間 | 完了条件 |
|----|--------|--------------------|----------|----------|----------|
| T-014 | フロントエンドの土台を作る。`package.json`、`vite.config.ts`（`base: "/portal_coffee_ledger/"`、ポート 5173）、`tsconfig.json`、`index.html`（タイトル「珈琲台帳」）、`.env` / `.env.production`、`env.d.ts`、`main.ts`、`App.vue`、`AppNav.vue`（ヘッダ）、`style.css`、`router.ts`（`createWebHistory(import.meta.env.BASE_URL)`、6 画面の仮の中身） | design.md「フロントエンド設計」 / ui-design.md 冒頭、`rules/15-ui-style.md`、`rules/17-nginx-deploy.md` | `<cl>/frontend/` | 3h | `npm run dev` で起動し、`/portal_coffee_ledger/` でヘッダ（ブランド名、「飲む」「管理」）が出る。`style.css` が `rules/15-ui-style.md` の色・部品の値を持つ。`npm run build` が型エラーなしで通る |
| T-015 | `api.ts`（20 エンドポイント、キャッシュなし、エラーの変換）、`types.ts`、`format.ts`（日時、金額、今日の日付、支払額の 10 円刻み）を作る | REQ-005、REQ-019、REQ-020 / design.md「モジュール構成」、api-design.md 全体 | `<cl>/frontend/src/` | 2h | api-design.md の全エンドポイントに対応する関数と応答の型がある。API のエラーは `code`・`message` で、通信の失敗は「通信に失敗しました。」で投げられる。支払額の増減が REQ-005 の規則どおりになる |
| T-016 | 管理パスワードの入場確認（`adminGate.ts`、ルータの遷移前の確認）と SCR-002 を作る | REQ-007 / ui-design.md「SCR-002」「画面遷移」、design.md「認証 / 認可」 | `<cl>/frontend/src/` | 2h | 未入力で管理機能の画面を開くと SCR-002 に移り、一致すれば入場先へ（履歴を置き換えて）進む。不一致なら「パスワードが正しくありません。」。キャンセルで SCR-001。SCR-001 へ移ると再び入力が必要になる。入場先が管理機能の画面でなければ SCR-003 へ進む |
| T-017 | SCR-001 の上部バーと行一覧、飲用の記録（完了モーダル）と最後の飲用の取り消しを作る | REQ-001〜004 / ui-design.md「SCR-001」 | `<cl>/frontend/src/` | 3h | ui-design.md の部品配置・有効／無効の条件・状態別の表示どおりに動く。人数が増えても 2 列の行一覧が 1 画面に収まり、ページもコンテンツもスクロールしない。完了モーダルを閉じるまで操作できない。モーダルは背景のクリックで閉じない |
| T-018 | SCR-001 の支払モーダル（10 円刻みの金額、支払い確定、直近の支払の取り消し）を作る | REQ-005、REQ-006 / ui-design.md「SCR-001（支払モーダル）」 | `<cl>/frontend/src/` | 2h | 金額の初期値が未払い代金の全額で、−／＋ が REQ-005 の規則どおりに増減する。確定するとモーダルが閉じて一覧が更新される。直近の支払の取り消し後、モーダルは開いたまま内容が読み直される |
| T-019 | SCR-003（一杯単価、徴収状況と金庫収納、金庫操作）を作る | REQ-008〜011 / ui-design.md「SCR-003」 | `<cl>/frontend/src/` | 3h | ui-design.md の部品配置・初期値・有効／無効の条件どおりに動く。金庫収納と金庫操作は確認ダイアログに同意したときだけ実行される。操作の成功後に 3 つの金額と履歴が読み直される |
| T-020 | SCR-004（人の登録・一覧・表示順・利用停止、記録パネル、未払いの修正）を作る | REQ-012〜016 / ui-design.md「SCR-004」 | `<cl>/frontend/src/` | 3h | ui-design.md の部品配置・有効／無効の条件どおりに動く。利用停止した人に「停止」のバッジが付く。名前を押すと記録パネル（未払い代金、未払いの修正、飲用記録、支払記録）が出る。未払いの修正は確認ダイアログに同意したときだけ実行される。操作の成功後に一覧と記録パネルが読み直される |
| T-021 | SCR-005（集計）と SCR-006（操作記録）を作る | REQ-017、REQ-018 / ui-design.md「SCR-005」「SCR-006」 | `<cl>/frontend/src/` | 2h | 表の列と、出来事・操作ごとの「契機／操作」「内容」の表記が ui-design.md の表どおりになる。空のときの文言が出る |

### 総合確認

| No | タスク | 対応する要件/設計 | 実装パス | 所要時間 | 完了条件 |
|----|--------|--------------------|----------|----------|----------|
| T-022 | 開発環境で全画面を通しで確認する | REQ-001〜021 の受け入れ条件 / ui-design.md 全体、`rules/31-web-app-responsive-layout-spec.md`（適用する範囲） | `<cl>/` | 3h | requirements.md の全受け入れ条件を画面から確かめ、結果を記録する。PC とスマートフォン幅の両方で、長い名前・0 件・人数が多い場合・エラー時に表示が崩れない。`npm run build` と pytest がすべて通る |

### 追加機能（REQ-022 DB の整理、REQ-023 CSV 出力）

| No | タスク | 対応する要件/設計 | 実装パス | 所要時間 | 完了条件 |
|----|--------|--------------------|----------|----------|----------|
| T-023 | 金銭の動きの CSV 出力 API（`GET /summary/csv`）を作る。`services/summary_csv.py` で集計の結果を古い順の CSV にする。CORS で `Content-Disposition` を公開する | REQ-023 / design.md「金銭の動きの CSV 出力」、api-design.md「GET /summary/csv」 | `<cl>/backend/app/` | 2h | 応答のヘッダ（`text/csv; charset=utf-8`、`attachment` とファイル名、`no-store`）と本文（BOM、CRLF、12 列の見出し、種類・入出金の表記、日時の形式、区切りなしの金額、引用符の扱い）が api-design.md どおり。積み上げの値が `GET /summary` と一致する。出来事が無いときは見出しの行だけ。要求と成功（行数）がログに出る |
| T-024 | DB の整理 API（`POST /maintenance/vacuum`）を作る。`db.py` に autocommit の接続を作る関数を足し、`services/maintenance.py` で advisory lock を取ってから 8 テーブルに `VACUUM (ANALYZE)` を実行する | REQ-022 / design.md「DB の整理」、api-design.md「POST /maintenance/vacuum」 | `<cl>/backend/app/` | 2h | 実行すると 200 と所要時間が返り、8 テーブルの最終 VACUUM・ANALYZE 日時（`pg_stat_user_tables`）が更新される。別の整理の実行中は 409 `VACUUM_IN_PROGRESS`。台帳のデータと操作記録は変わらない。要求・成功（所要時間）・失敗がログに出る |
| T-025 | CSV 出力と DB の整理のテストを書く | REQ-022、REQ-023 / design.md「テスト」 | `<cl>/tests/` | 2h | CSV の見出し・行の並び・各列の値・積み上げが集計と一致すること・引用符の扱い・BOM と CRLF・ファイル名の形式、DB の整理の成功・実行中の拒否・データが変わらないことを確かめるテストがあり、既存のテストと合わせてすべて通る |
| T-026 | SCR-005 に CSV 出力ボタンを付ける。`api.ts` に CSV を Blob とファイル名で受け取る関数、`download.ts` にダウンロードさせる関数を作る | REQ-023 / ui-design.md「SCR-005」、design.md「モジュール構成」 | `<cl>/frontend/src/` | 2h | 「CSV 出力」を押すと、サーバが決めた名前でブラウザにダウンロードされる（開発時のポート違いでも名前が取れる）。処理中はボタンが無効。失敗時は見出しの下にエラーが出て、ダウンロードされない。`npm run build` が通る |
| T-027 | SCR-003 に DB の整理パネルを付ける | REQ-022 / ui-design.md「SCR-003」 | `<cl>/frontend/src/` | 1h | 確認ダイアログに同意したときだけ実行され、実行中は「整理中…」の表示で画面のボタンが無効になる。成功すると所要時間付きの完了表示が出て、失敗すると見出しの下にエラーが出る。`npm run build` が通る |
| T-028 | 追加機能を画面から通しで確認する | REQ-022、REQ-023 の受け入れ条件 | `<cl>/` | 1h | ブラウザで DB の整理と CSV 出力を行い、受け入れ条件を確かめる。ダウンロードした CSV を Excel で開いて文字化けせず、カンマや改行を含む事由でも列がずれない。pytest と `npm run build` がすべて通る |

## 進め方

- T-001 → T-002 → T-003 を先に行う。T-004〜T-009 は T-003 の後なら順不同。
- T-011 は T-002 の後、T-012・T-013 は対応する API タスクの後に行う。
- T-014 → T-015 → T-016 の後に、T-017〜T-021 を行う（画面は対応する API ができていること）。
- T-022 は全タスクの後に行う。
- 追加機能は T-023 → T-024 → T-025 → T-026・T-027 → T-028 の順に行う（T-022 の画面確認と T-028 はまとめて行ってよい）。
- nginx の設定（`rules/17-nginx-deploy.md`）と本番サーバへの配置は、本タスクの対象外とする。

## 承認

現在の状態: 承認済み

| 日時 | 状態 | 変更概要 |
|------|------|----------|
| 2026-09-24 14:29 | 未承認 | 初版 |
| 2026-09-24 14:31 | 承認済み | 初版を承認 |
| 2026-09-24 15:03 | 未承認 | REQ-022（DB の整理）・REQ-023（CSV 出力）のタスク T-023〜T-028 を追加 |
| 2026-09-24 15:04 | 承認済み | T-023〜T-028 の追加を承認 |
