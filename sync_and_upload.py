import os
import re
import boto3
import frontmatter
import subprocess
import json

# --- 环境变量配置 (严格对应你的 GitHub Secrets) ---
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = "xieerfan-assets"
API_URL = os.getenv("API_BASE_URL", "")
# 确保 URL 结尾处理干净
PUBLIC_DOMAIN = API_URL.replace("/api", "").rstrip("/") + "/img"

# 初始化 R2 (注意这里使用 CF_ACCOUNT_ID)
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
    # 显式传递 Account ID 给 wrangler 防止其读取不到环境
    env = os.environ.copy()
    env["CLOUDFLARE_ACCOUNT_ID"] = CF_ACCOUNT_ID
    
    cmd = ["npx", "wrangler", "d1", "execute", db, "--remote", "--json", f"--command={sql}"]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    
    if res.returncode != 0:
        print(f"❌ D1 执行报错: {res.stderr}")
    else:
        print(f"✔️ SQL 执行成功")
    return res.stdout

def get_id_from_json(json_str):
    try:
        data = json.loads(json_str)
        if data and len(data) > 0 and 'results' in data[0] and len(data[0]['results']) > 0:
            return data[0]['results'][0].get('id')
    except: pass
    return None

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
        return None

def process_sync(category):
    base_dir = f"./{category}"
    db_name = f"xieerfan-{category}"
    if not os.path.exists(base_dir): return

    files = [f for f in os.listdir(base_dir) if f.endswith(".md")]
    print(f"🚀 正在处理 {category} 分支，共 {len(files)} 个文件")

    for filename in files:
        path = os.path.join(base_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # 路径替换逻辑
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
            # 完整匹配你的 D1 posts 表结构
            sql = f"""
            INSERT OR REPLACE INTO posts (title, category, post_type, language, is_open_source, project_name, content, thumb_url, date)
            VALUES ('{title}', '{sql_escape(post.get('category','thoughts'))}', '{sql_escape(post.get('post_type',''))}', 
            '{sql_escape(post.get('language',''))}', {1 if post.get('open_source') else 0}, '{sql_escape(post.get('project',''))}', 
            '{safe_content}', '{sql_escape(post.get('thumb', 'backgrounds/wall1.jpg'))}', CURRENT_TIMESTAMP);
            """
            run_sql(db_name, sql)
        else:
            # Wiki 逻辑
            parent_title = sql_escape(str(post.get('parent_title', '')).strip())
            p_id = 0
            if parent_title:
                run_sql(db_name, f"INSERT OR IGNORE INTO wiki_nodes (title, parent_id) VALUES ('{parent_title}', 0)")
                p_res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title = '{parent_title}' LIMIT 1")
                p_id = get_id_from_json(p_res) or 0
            
            run_sql(db_name, f"INSERT OR REPLACE INTO wiki_nodes (title, parent_id, has_content) VALUES ('{title}', {p_id}, 1)")
            curr_res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title = '{title}' AND parent_id = {p_id} LIMIT 1")
            curr_id = get_id_from_json(curr_res)
            if curr_id:
                run_sql(db_name, f"INSERT OR REPLACE INTO wiki_contents (node_id, content) VALUES ({curr_id}, '{safe_content}')")
        
        print(f"✅ 处理完成: {title}")

if __name__ == "__main__":
    process_sync("blog")
    process_sync("wiki")