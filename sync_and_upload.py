import os
import re
import boto3
import frontmatter
import subprocess
import json
import sys

# --- 环境变量安全获取 ---
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

def get_id_from_json(json_str):
    try:
        data = json.loads(json_str)
        if data and len(data) > 0 and 'results' in data[0] and len(data[0]['results']) > 0:
            return data[0]['results'][0].get('id')
    except: pass
    return None

def run_sql(db, sql):
    env = os.environ.copy()
    env["CLOUDFLARE_ACCOUNT_ID"] = str(CF_ACCOUNT_ID)
    cmd = ["npx", "wrangler", "d1", "execute", db, "--remote", "--json", f"--command={sql}"]
    
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"❌ D1 报错: {res.stderr}")
        # sys.exit(1) # 如果需要严格报错可以取消注释
    return res.stdout

def upload_to_r2(local_path, category):
    if not os.path.exists(local_path): return None
    file_name = os.path.basename(local_path)
    remote_key = f"{category}/images/{file_name}"
    try:
        ext = file_name.lower().split('.')[-1]
        content_type = "image/png" if ext == "png" else "image/jpeg"
        s3.upload_file(local_path, R2_BUCKET, remote_key, ExtraArgs={'ContentType': content_type})
        return f"{PUBLIC_DOMAIN}/{remote_key}"
    except Exception as e:
        print(f"  ❌ R2 上传失败: {e}")
        return None

# --- Blog 同步逻辑 (保持原样) ---
def sync_blog():
    category = "blog"
    base_dir = f"./{category}"
    db_name = f"xieerfan-{category}"
    if not os.path.exists(base_dir): return

    files = [f for f in os.listdir(base_dir) if f.endswith(".md")]
    print(f"🚀 开始同步 Blog，文件数: {len(files)}")

    for filename in files:
        path = os.path.join(base_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # 图片替换
        new_content = re.sub(r'!\[(.*?)\]\((images/.+?)\)', 
            lambda m: f"![{m.group(1)}]({upload_to_r2(os.path.join(base_dir, m.group(2)), category)})", 
            post.content)
            
        title = sql_escape(post.get('title', filename.replace('.md', '')).strip())
        safe_content = sql_escape(new_content.strip())

        sql = f"""
        INSERT OR REPLACE INTO posts (title, category, post_type, language, is_open_source, project_name, content, thumb_url, date)
        VALUES ('{title}', '{sql_escape(post.get('category','thoughts'))}', '{sql_escape(post.get('post_type',''))}', 
        '{sql_escape(post.get('language',''))}', {1 if post.get('is_open_source') else 0}, '{sql_escape(post.get('project_name',''))}', 
        '{safe_content}', '{sql_escape(post.get('thumb', 'backgrounds/wall1.jpg'))}', CURRENT_TIMESTAMP);
        """
        run_sql(db_name, sql)
        print(f"✨ Blog 同步成功: {title}")

# --- Wiki 同步逻辑 (递归层级优化) ---
def sync_wiki():
    category = "wiki"
    base_dir = f"./{category}"
    db_name = f"xieerfan-{category}"
    if not os.path.exists(base_dir): return

    print(f"🚀 开始递归同步 Wiki 结构...")

    for root, dirs, files in os.walk(base_dir):
        # 1. 计算当前文件夹相对于 wiki/ 的路径
        rel_path = os.path.relpath(root, base_dir)
        
        # 获取或创建父节点链
        parent_id = 0
        if rel_path != ".":
            path_parts = rel_path.split(os.sep)
            current_p = 0
            for part in path_parts:
                safe_part = sql_escape(part)
                # 创建文件夹节点 (has_content=0)
                run_sql(db_name, f"INSERT OR IGNORE INTO wiki_nodes (title, parent_id, has_content) VALUES ('{safe_part}', {current_p}, 0);")
                # 获取 ID
                res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title='{safe_part}' AND parent_id={current_p} LIMIT 1;")
                current_p = get_id_from_json(res) or 0
            parent_id = current_p

        # 2. 处理当前文件夹下的 Markdown 文件
        for filename in files:
            if not filename.endswith(".md"): continue
            
            md_path = os.path.join(root, filename)
            with open(md_path, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)

            # 图片处理（基于当前 MD 所在目录寻找 images/）
            new_content = re.sub(r'!\[(.*?)\]\((images/.+?)\)', 
                lambda m: f"![{m.group(1)}]({upload_to_r2(os.path.join(root, m.group(2)), category)})", 
                post.content)

            title = sql_escape(post.get('title', filename.replace('.md', '')).strip())
            safe_content = sql_escape(new_content.strip())

            # 插入或更新文件节点 (has_content=1)
            run_sql(db_name, f"INSERT OR REPLACE INTO wiki_nodes (title, parent_id, has_content) VALUES ('{title}', {parent_id}, 1);")
            
            # 获取刚刚插入的节点 ID 以便更新内容
            node_res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title='{title}' AND parent_id={parent_id} LIMIT 1;")
            node_id = get_id_from_json(node_res)
            
            if node_id:
                run_sql(db_name, f"INSERT OR REPLACE INTO wiki_contents (node_id, content, update_at) VALUES ({node_id}, '{safe_content}', CURRENT_TIMESTAMP);")
                print(f"🌲 Wiki 同步成功: {'/' if not rel_path else rel_path + '/'}{title}")

if __name__ == "__main__":
    sync_blog()
    sync_wiki()