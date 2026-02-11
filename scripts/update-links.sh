#!/bin/bash
# 更新所有 Markdown 文件中的連結指向 archive/

echo "=== 開始更新 Markdown 連結 ==="

# 定義連結映射（舊路徑 -> 新路徑）
declare -A LINK_MAP=(
    # Guides
    ["01-guides/cyclonedds-config-guide.md"]="archive/2026-02-11-restructure/guides/cyclonedds-config-guide.md"
    ["01-guides/slam_nav/cyclonedds_guide.md"]="archive/2026-02-11-restructure/guides/cyclonedds_guide.md"
    ["01-guides/Depth Anything V2/"]="archive/2026-02-11-restructure/guides/Depth Anything V2/"
    ["01-guides/Depth%20Anything%20V2/"]="archive/2026-02-11-restructure/guides/Depth%20Anything%20V2/"
    ["01-guides/專案必學知識清單.md"]="archive/2026-02-11-restructure/guides/專案必學知識清單.md"
    ["01-guides/go2_sdk/"]="archive/2026-02-11-restructure/guides/go2_sdk/"
    
    # Overview
    ["00-overview/開發計畫.md"]="archive/2026-02-11-restructure/overview/開發計畫.md"
    ["00-overview/專題目標.md"]="archive/2026-02-11-restructure/overview/專題目標.md"
    ["00-overview/1-7-demo-簡報大綱.md"]="archive/2026-02-11-restructure/overview/1-7-demo-簡報大綱.md"
    ["00-overview/團隊進度追蹤/"]="archive/2026-02-11-restructure/overview/團隊進度追蹤/"
    
    # Testing
    ["03-testing/Demo 影片錄製腳本.md"]="archive/2026-02-11-restructure/testing/Demo 影片錄製腳本.md"
    ["03-testing/slam-phase1_test_results_ROY.md"]="archive/2026-02-11-restructure/testing/slam-phase1_test_results_ROY.md"
    
    # Reports
    ["03-reports/drafts/"]="archive/2026-02-11-restructure/reports/drafts/"
    ["03-reports/背景知識_草稿.md"]="archive/2026-02-11-restructure/reports/背景知識_草稿.md"
    
    # Design
    ["02-design/資料庫設計.md"]="archive/2026-02-11-restructure/design/資料庫設計.md"
)

# 更新單個文件的函數
update_file() {
    local file="$1"
    local updated=0
    
    for old_path in "${!LINK_MAP[@]}"; do
        local new_path="${LINK_MAP[$old_path]}"
        
        # 檢查文件是否包含這個連結
        if grep -q "](${old_path})" "$file" 2>/dev/null || grep -q "](${old_path}#" "$file" 2>/dev/null; then
            # 只替換 Markdown 連結語法 ](path)
            sed -i "s|](${old_path})|](${new_path})|g" "$file"
            # 替換帶錨點的連結 ](path#anchor)
            sed -i "s|](${old_path}#|](${new_path}#|g" "$file"
            updated=1
        fi
    done
    
    if [ $updated -eq 1 ]; then
        echo "  ✓ $file"
    fi
}

# 找到所有需要更新的文件（排除 archive/ 和 .git/）
echo "掃描 Markdown 文件..."
find . -name "*.md" -type f ! -path "./archive/*" ! -path "./.git/*" ! -path "./.sisyphus/*" | while read file; do
    update_file "$file"
done

echo ""
echo "=== 連結更新完成 ==="
echo ""
echo "檢查是否還有殘留的舊路徑引用（排除 archive/ 自身）:"
echo ""

# 檢查殘留
for old_path in "${!LINK_MAP[@]}"; do
    result=$(grep -r "${old_path}" . --include="*.md" 2>/dev/null | grep -v "./archive/" | grep -v "./.git/" | grep -v "./.sisyphus/" | head -3)
    if [ -n "$result" ]; then
        echo "⚠️  發現殘留: ${old_path}"
        echo "$result"
        echo ""
    fi
done

echo "如果上方沒有輸出，表示所有連結都已更新！"
