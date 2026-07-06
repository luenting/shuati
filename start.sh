#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_NAME="shuati"
PORT=5588
LOG_FILE="$PROJECT_DIR/app.log"
PID_FILE="$PROJECT_DIR/app.pid"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERROR]${NC} $1"; }

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then warn "服务已在运行 (PID: $PID)"; return; fi
        rm -f "$PID_FILE"
    fi
    cd "$PROJECT_DIR"
    nohup python3 app.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo ""; info "✅ 刷题系统启动成功！"
        info "   本地访问: http://localhost:$PORT"
        info "   日志文件: $LOG_FILE"
        info "   停止服务: bash stop.sh"; echo ""
    else
        err "❌ 启动失败"; tail -5 "$LOG_FILE"
    fi
}

case "${1:-start}" in
    start) start ;;
    *) echo "用法: bash start.sh"; start ;;
esac
