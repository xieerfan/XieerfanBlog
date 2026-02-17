import os
import re
import boto3
import frontmatter
import subprocess
import sys

# --- 环境变量配置 ---
def get_env(name):
    val = os.getenv(name)
    if not val:
        print(f"❌ 错误: 环境变量 '{name}' 未设置。")
        sys.exit(1)
    return val

CF_ACCOUNT_ID = get_env("CF_ACCOUNT_ID")
R2_ACCESS_KEY = get_env("R2_ACCESS_KEY")
R2_SECRET_KEY = get_env("R2_SECRET_KEY")
API_URL = get_env("API_BASE_URL")

R2_BUCKET = "xieerfan-assets"
PUBLIC_DOMAIN = API_URL.replace("/api", "").rstrip("/") + "/img"

# 初始化 R2
s3 = boto3.client("s3",
    endpoint_url=f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto"
)

def sql_escape(text):
    if not text: return ""
    return str(text).replace("'", "''")

def run_sql(db, sql):
    env = os.environ.copy()
    env["CLOUDFLARE_ACCOUNT_ID"] = str(CF_ACCOUNT_ID)
    
    # 注意：这里去掉了 --json 以便直接观察报错
    cmd = ["npx", "wrangler", "d1", "execute", db, "--remote", f"--command={sql}"]
    
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if res.returncode != 0:
        print(f"❌ D1 执行失败！错误信息如下：\n{res.stderr}\n{res.stdout}")
        # 发现错误直接中断，不要假装成功
        sys.exit(1)
    else:
        print(f"✔️ SQL 执行成功")
    return res.stdout

def upload_to_r2(local_path, category):
    file_name = os.path.basename(local_path)
    remote_key = f"{category}/images/{file_name}"
    try:
        ext = file_name.lower().split('.')[-1]
        content_type = "image/png" if ext == "png" else "image/jpeg"
        s3.upload_file(local_path, R2_BUCKET, remote_key, ExtraArgs={'ContentType': content_type})
        print(f"  🖼️ R2 上传完成: {remote_key}")
        return f"{PUBLIC_DOMAIN}/{remote_key}"
    except Exception as e:
        print(f"  ❌ R2 上传失败: {e}")
        sys.exit(1)

def process_sync(category):
    base_dir = f"./{category}"
    db_name = f"xieerfan-{category}"
    if not os.path.exists(base_dir): return

    files = [f for f in os.listdir(base_dir) if f.endswith(".md")]
    print(f"🚀 开始同步 {category}，文件数: {len(files)}")

    for filename in files:
        path = os.path.join(base_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # 图片处理
        img_pattern = r'!\[(.*?)\]\((images/.+?)\)'
        def replacer(match):
            rel_img_path = match.group(2)
            full_img_path = os.path.join(base_dir, rel_img_path)
            if os.path.exists(full_img_path):
                url = upload_to_r2(full_img_path, category)
                return f"![{match.group(1)}]({url})" if url else match.group(0)
            return match.group(0)

        new_content = re.sub(img_pattern, replacer, post.content)
        title = sql_escape(post.get('title', filename.replace('.md', '')).strip())
        safe_content = sql_escape(new_content.strip())

        if category == "blog":
            # 严格对应你的 D1 表结构：
            # id(自动), title, category, post_type, language, is_open_source, project_name, content, thumb_url, date
            sql = f"""
            INSERT OR REPLACE INTO posts (title, category, post_type, language, is_open_source, project_name, content, thumb_url, date)
            VALUES (
                '{title}', 
                '{sql_escape(post.get('category','thoughts'))}', 
                '{sql_escape(post.get('post_type',''))}', 
                '{sql_escape(post.get('language',''))}', 
                {1 if post.get('is_open_source') else 0}, 
                '{sql_escape(post.get('project_name',''))}', 
                '{safe_content}', 
                '{sql_escape(post.get('thumb', 'backgrounds/wall1.jpg'))}', 
                CURRENT_TIMESTAMP
            );
            """
            run_sql(db_name, sql)
        else:
            # Wiki 逻辑
            parent_title = sql_escape(str(post.get('parent_title', '')).strip())
            # 简单的 Wiki 节点处理
            if parent_title and parent_title != 'None' and parent_title != '':
                run_sql(db_name, f"INSERT OR IGNORE INTO wiki_nodes (title, parent_id) VALUES ('{parent_title}', 0);")
                # 这里暂不处理复杂的层级递归，仅做基础插入
            
            run_sql(db_name, f"INSERT OR REPLACE INTO wiki_nodes (title, parent_id, has_content) VALUES ('{title}', 0, 1);")
            # 更新内容表（假设你的 wiki 表结构有 content 字段）
            # 注意：这里需要根据你真实的 Wiki D1 表结构微调
            run_sql(db_name, f"INSERT OR REPLACE INTO wiki_contents (node_id, content) SELECT id, '{safe_content}' FROM wiki_nodes WHERE title='{title}' LIMIT 1;")
        
        print(f"✨ 同步成功: {title}")

if __name__ == "__main__":
    process_sync("blog")
    process_sync("wiki")