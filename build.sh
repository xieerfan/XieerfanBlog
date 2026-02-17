#!/bin/bash

# --- 1. 配置区 ---
# 请确保你的 SSH Key 已经添加到 GitHub，或者这里的 URL 改成带 Token 的 HTTPS 链接
REPO_URL="git@github.com:xieerfan/XieerfanBlog.git"

# --- 2. 图片处理函数 ---
process_md_files() {
    local dir=$1
    if [ ! -d "$dir" ]; then return; fi
    echo "🔍 正在扫描 $dir 文件夹下的图片引用..."
    mkdir -p "$dir/images"

    find "$dir" -maxdepth 1 -name "*.md" | while read -r md_file; do
        # 匹配 ![alt](local_path)
        grep -oE '!\[.*\]\([^)]+\)' "$md_file" | while read -r img_tag; do
            # 提取括号内的路径
            original_path=$(echo "$img_tag" | sed -E 's/.*(\((.*)\))/\2/')
            
            # 如果是本地路径且文件存在，则搬运
            if [[ "$original_path" != images/* ]] && [[ "$original_path" != http* ]] && [[ -f "$original_path" ]]; then
                file_name=$(basename "$original_path")
                target_path="$dir/images/$file_name"
                echo "🚚 搬运图片: $file_name"
                cp "$original_path" "$target_path"
                # 修正 MD 里的路径
                sed -i "s@$original_path@images/$file_name@g" "$md_file"
            fi
        done
    done
}

# --- 3. 执行图片预处理 ---
process_md_files "blog"
process_md_files "wiki"

# --- 4. 强制推送逻辑 ---
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")

sync_branch() {
    local branch=$1
    local folder=$2
    
    # 检查文件夹是否有变动
    if [[ -n $(git status --porcelain "$folder/") ]]; then
        echo "📝 检测到 $folder 变动，正在强制推送至 $branch..."
        
        # 保存当前分支名，防止切不回来
        local original_branch=$(git rev-parse --abbrev-ref HEAD)

        # 暴力操作：直接把当前目录暂存，然后推送到目标分支
        git add .
        git commit -m "$folder update: $CURRENT_TIME"
        
        # 核心：直接向远程仓库的对应分支强行推送当前 HEAD
        git push "$REPO_URL" HEAD:refs/heads/"$branch" -f
        
        echo "✅ $branch 推送成功！"
    else
        echo "🍃 $folder 无变动，跳过。"
    fi
}

# 执行同步
sync_branch "blog-branch" "blog"
sync_branch "wiki-branch" "wiki"

echo "✨ 全部操作完成！快去 GitHub Actions 页面盯着进度条喵~"