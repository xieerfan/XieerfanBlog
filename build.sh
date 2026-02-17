#!/bin/bash

REPO_URL="git@github.com:xieerfan/XieerfanBlog.git"
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

# --- 图片预处理函数 ---
process_images() {
    local dir=$1
    if [ ! -d "$dir" ]; then return; fi
    mkdir -p "$dir/images"
    find "$dir" -maxdepth 1 -name "*.md" | while read -r md_file; do
        grep -oE '!\[.*\]\([^)]+\)' "$md_file" | while read -r img_tag; do
            original_path=$(echo "$img_tag" | sed -E 's/.*(\((.*)\))/\2/')
            if [[ "$original_path" != images/* ]] && [[ "$original_path" != http* ]] && [[ -f "$original_path" ]]; then
                file_name=$(basename "$original_path")
                cp "$original_path" "$dir/images/$file_name"
                sed -i "s@$original_path@images/$file_name@g" "$md_file"
            fi
        done
    done
}

# 执行预处理
process_images "blog"
process_images "wiki"

# --- 核心：分发同步函数 ---
sync_to_branch() {
    local branch=$1
    local folder=$2
    
    echo "📦 准备同步 $folder 到 $branch..."
    
    # 1. 临时存放当前所有改动
    git add .
    git commit -m "temp commit for sync"
    
    # 2. 创建一个纯净的孤立分支镜像 (或者直接从当前切出)
    # 这一步确保分支里包含：该文件夹 + 同步脚本 + CI配置
    git checkout -b "deploy-$branch"
    
    # 只保留必要文件：对应文件夹、Python脚本、CI配置
    # 先删掉所有不需要的东西（仅在临时分支操作）
    git rm -rf . > /dev/null
    git checkout HEAD -- "$folder/"
    git checkout HEAD -- "sync_and_upload.py"
    git checkout HEAD -- ".github/workflows/sync.yaml"
    
    git add .
    git commit --amend -m "$folder update: $CURRENT_TIME"
    
    # 3. 强行发射！
    git push "$REPO_URL" "deploy-$branch":"$branch" -f
    
    # 4. 切回原分支并清理本地临时分支
    git checkout -
    git branch -D "deploy-$branch"
}

# 只要有文件改动就同步
sync_to_branch "blog-branch" "blog"
sync_to_branch "wiki-branch" "wiki"

echo "✨ 配置文件已同步到各分支，现在 GitHub Actions 应该能看到任务了喵！"