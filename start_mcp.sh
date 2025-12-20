#!/bin/zsh
# 一鍵啟動 MCP 所需的所有服務
# 用法: zsh start_mcp.sh

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 專案路徑
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
CONNECT_IF="${CONNECT_IF:-enp0s1}"

echo -e "${BLUE}🐕 啟動 Go2 MCP 控制系統...${NC}"

# ==========================================
# 🔧 關鍵：清理舊的 ros2 daemon（避免 DDS cache 問題）
# ==========================================
echo -e "${YELLOW}🧹 清理舊的 ros2 daemon...${NC}"
pkill -9 -f "ros2-daemon" 2>/dev/null || true
unset RMW_IMPLEMENTATION
unset CYCLONEDDS_URI
echo -e "${GREEN}✅ DDS 環境已清理${NC}"

# ==========================================
# ROS2 環境載入函數
# ==========================================
load_ros_env() {
    echo -e "${BLUE}🔧 載入 ROS2 環境...${NC}"
    source /opt/ros/humble/setup.zsh
    cd $SCRIPT_DIR
    source ~/ros2_ws/install/setup.zsh
    export CONN_TYPE=webrtc
    export ROBOT_IP="192.168.12.1"
    # 確保使用 ROS2 預設 DDS (FastDDS)
    unset RMW_IMPLEMENTATION
    unset CYCLONEDDS_URI
    echo -e "${GREEN}✅ 環境已載入 (使用 ROS2 預設 DDS)${NC}"
}

# ==========================================
# 網路檢查
# ==========================================
check_network() {
    echo -e "${YELLOW}🔍 檢查網路連通性...${NC}"
    
    if ping -c 1 192.168.12.1 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Go2 機器狗連線正常${NC}"
    else
        echo -e "${RED}❌ 無法連接 Go2 機器狗 (192.168.12.1)${NC}"
        echo -e "${YELLOW}請先執行: zsh phase1_test.sh env${NC}"
        exit 1
    fi
}

# ==========================================
# 檢查 tmux session
# ==========================================
if tmux has-session -t go2_mcp 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Session 'go2_mcp' 已存在！${NC}"
    echo -e "📋 選項："
    echo -e "  1. ${BLUE}tmux attach -t go2_mcp${NC}  （連接到現有 session）"
    echo -e "  2. ${BLUE}tmux kill-session -t go2_mcp${NC}  （刪除後重新啟動）"
    exit 1
fi

# 載入環境並檢查網路
load_ros_env
check_network

# ==========================================
# 使用 tmux 管理多個 Terminal
# ==========================================
# ==========================================
# Pane 佈局 (3列 格局):
#  ┌─────────────┬─────────────┐
#  │ 0:rosbridge │ 1:driver    │
#  ├─────────────┼─────────────┤
#  │ 2:snapshot  │ 3:move_svc  │
#  ├─────────────┴─────────────┤
#  │ 4:測試終端                 │
#  └───────────────────────────┘
# ==========================================
echo -e "${BLUE}📺 建立 tmux session...${NC}"
tmux new-session -d -s go2_mcp -x 180 -y 50

# Step 1: 垂直分割成上中下三列
tmux split-window -v -t go2_mcp:0
tmux split-window -v -t go2_mcp:0

# Step 2: 上方 (pane 0) 水平分割
tmux split-window -h -t go2_mcp:0.0

# Step 3: 中間 (pane 2) 水平分割
tmux split-window -h -t go2_mcp:0.2

# 現在 pane 順序: 0=左上, 1=右上, 2=左中, 3=右中, 4=下

# Pane 0 (左上): rosbridge
tmux send-keys -t go2_mcp:0.0 "pkill -9 -f ros2-daemon 2>/dev/null; \
unset RMW_IMPLEMENTATION; unset CYCLONEDDS_URI; \
source /opt/ros/humble/setup.zsh && \
source $SCRIPT_DIR/install/setup.zsh && \
echo '🌐 啟動 rosbridge (含 go2_interfaces)...' && \
ros2 launch rosbridge_server rosbridge_websocket_launch.xml" C-m

# Pane 1 (右上): driver
tmux send-keys -t go2_mcp:0.1 "sleep 8 && cd $SCRIPT_DIR && \
source /opt/ros/humble/setup.zsh && \
source ~/ros2_ws/install/setup.zsh && \
unset RMW_IMPLEMENTATION && unset CYCLONEDDS_URI && \
echo '🐕 啟動 Go2 Driver...' && \
zsh start_go2_simple.sh" C-m

# Pane 2 (左中): snapshot_service
tmux send-keys -t go2_mcp:0.2 "sleep 10 && cd $SCRIPT_DIR && \
source /opt/ros/humble/setup.zsh && \
source $SCRIPT_DIR/install/setup.zsh && \
unset RMW_IMPLEMENTATION && unset CYCLONEDDS_URI && \
echo '📸 啟動 snapshot_service...' && \
ros2 run go2_robot_sdk snapshot_service" C-m

# Pane 3 (右中): move_service
tmux send-keys -t go2_mcp:0.3 "sleep 12 && cd $SCRIPT_DIR && \
source /opt/ros/humble/setup.zsh && \
source $SCRIPT_DIR/install/setup.zsh && \
unset RMW_IMPLEMENTATION && unset CYCLONEDDS_URI && \
echo '🚀 啟動 move_service...' && \
ros2 run go2_robot_sdk move_service" C-m

# Pane 4 (下): 測試終端
tmux send-keys -t go2_mcp:0.4 "sleep 18 && \
source /opt/ros/humble/setup.zsh && \
source $SCRIPT_DIR/install/setup.zsh && \
unset RMW_IMPLEMENTATION && unset CYCLONEDDS_URI && \
echo '🧪 測試 ROS2 系統...' && echo '' && \
echo '=== Topics ===' && \
ros2 topic list --no-daemon && echo '' && \
echo '=== Services ===' && \
ros2 service list --no-daemon | grep -E 'snapshot|move_for_duration|stop_movement' && echo '' && \
echo '✅ MCP 系統就緒!'" C-m

# 連接到 session
echo -e "${GREEN}✅ 所有服務已啟動中...${NC}"
echo -e "${YELLOW}⏳ 請等待約 18 秒讓系統就緒...${NC}"
echo -e ""
echo -e "📋 使用說明："
echo -e "  切換 pane:      ${BLUE}Ctrl+b o${NC}"
echo -e "  新增 pane:      ${BLUE}Ctrl+b %${NC}"
echo -e "  測試 topics:    ${BLUE}unset RMW_IMPLEMENTATION && ros2 topic list${NC}"
echo -e "  測試 services:  ${BLUE}ros2 service list | grep -E 'snapshot|move'${NC}"
echo -e ""
echo -e "🛑 停止服務: ${BLUE}tmux kill-session -t go2_mcp${NC}"
echo -e ""

tmux attach -t go2_mcp

