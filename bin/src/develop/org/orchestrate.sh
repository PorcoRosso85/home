#!/bin/bash
# Orchestrator command - Only I (orchestrator) execute this

case "$1" in
    add)
        # タスク追加
        bash managers/append_instruction.sh "$2" "$3"
        ;;
    status)
        # ステータス確認
        bash managers/monitor_status.sh
        ;;
    notify)
        # 全managerに通知
        for i in 1 2 3; do
            tmux send-keys -t nixos:2.$i "/read instructions.md" Enter
        done
        echo "Notified all managers to check instructions"
        ;;
    *)
        echo "Orchestrator Commands:"
        echo "  ./orchestrate.sh add <x|y|z|all> \"task\""
        echo "  ./orchestrate.sh status"
        echo "  ./orchestrate.sh notify"
        ;;
esac