#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$PROJECT_DIR/app.pid"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then kill "$PID" && info "✅ 已停止 (PID: $PID)"
    else warn "进程不存在"; fi
    rm -f "$PID_FILE"
else
    PID=$(pgrep -f "python3 app.py" 2>/dev/null | head -1)
    if [ -n "$PID" ]; then kill "$PID" && info "✅ 已停止 (PID: $PID)"
    else warn "没有运行中的服务"; fi
fi
