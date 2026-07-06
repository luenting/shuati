#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "[INFO] 重启刷题系统..."
bash "$PROJECT_DIR/stop.sh"
sleep 1
bash "$PROJECT_DIR/start.sh"
