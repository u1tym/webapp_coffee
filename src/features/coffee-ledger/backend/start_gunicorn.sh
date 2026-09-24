#!/bin/bash
# coffee-ledger backend を gunicorn（uvicorn ワーカー）で起動する（本番用）。
#   ./start_gunicorn.sh          フォアグラウンド起動
#   nohup ./start_gunicorn.sh &  バックグラウンド起動
# アクセスログとエラーログは backend/log/ に出す（業務ログは app が backend/log/coffee-ledger.log に出す）。
set -e
cd "$(dirname "$0")"
mkdir -p log
exec ./venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    -b 127.0.0.1:8010 \
    --pid log/gunicorn.pid \
    --access-logfile log/access.log \
    --error-logfile log/error.log
