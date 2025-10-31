#!/usr/bin/env bash
set -e
export PYTHONPATH=.
mkdir -p workspace data/logs
uvicorn multiai.server.app:app --host 0.0.0.0 --port 8084 --reload
