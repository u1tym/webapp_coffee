#!/bin/bash
# coffee-ledger backend を gunicorn(uvicorn worker) で起動する。
# 使い方: このスクリプトを ase ユーザーで実行する。
#   ./start_gunicorn.sh          フォアグラウンド起動
#   nohup ./start_gunicorn.sh &  バックグラウンド起動
set -e
cd "$(dirname "$0")"
exec ./venv/bin/gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    -b 127.0.0.1:8010 \
    --pid /tmp/coffee-ledger-gunicorn.pid \
    --access-logfile /var/log/coffee-ledger/access.log \
    --error-logfile /var/log/coffee-ledger/error.log
