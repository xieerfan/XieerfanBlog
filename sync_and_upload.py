import os
import re
import boto3
import frontmatter
import subprocess
import json

# --- 环境配置 ---
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = "xieerfan-assets"  # 修改为你的桶名
API_URL = os.getenv("API_BASE_URL", "")
PUBLIC_DOMAIN = API_URL.replace("/api", "") + "/img"

s3 = boto3.client("s3",
    endpoint_url=f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto"
)

def sql_escape(text):
    return str(text).replace("'", "''")

def run_sql(db, sql):
    cmd = ["wrangler", "d1", "execute", db, "--remote", "--json", f"--command={sql}"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

def get_id_from_json(json_str):
    try:
        data = json.loads(json_str)
        if data and len(data) > 0 and 'results' in data[0] and len(data[0]['results']) > 0:
            return data[0]['results'][0].get('id')
    except: pass
    return None

def upload_to_r2(local_path, category):
    """上传到 R2 并返回路径"""
    file_name = os.path.basename(local_path)
    # 路径格式：blog/images/xxx.png 或 wiki/images/xxx.png
    remote_key = f"{category}/images/{file_name}"
    try:
        content_type = "image/png" if file_name.lower().endswith(".png") else "image/jpeg"
        # 直接覆盖上传，确保图片有更新时也能同步
        s3.upload_file(local_path, R2_BUCKET, remote_key, ExtraArgs={'ContentType': content_type})
        return f"{PUBLIC_DOMAIN}/{remote_key}"
    except Exception as e:
        print(f"  ❌ R2 上传失败: {e}")
        return None

def process_sync(category):
    base_dir = f"./{category}"
    db_name = f"xieerfan-{category}"
    if not os.path.exists(base_dir): return

    for filename in os.listdir(base_dir):
        if not filename.endswith(".md"): continue
        path = os.path.join(base_dir, filename)
        post = frontmatter.load(path)
        
        # 处理内容中的图片引用
        img_pattern = r'!\[(.*?)\]\((images/.+?)\)'
        
        def replacer(match):
            rel_img_path = match.group(2)
            full_img_path = os.path.join(base_dir, rel_img_path)
            if os.path.exists(full_img_path):
                url = upload_to_r2(full_img_path, category)
                return f"![{match.group(1)}]({url})" if url else match.group(0)
            return match.group(0)

        new_content = re.sub(img_pattern, replacer, post.content)
        safe_content = sql_escape(new_content.strip())
        title = sql_escape(post.get('title', filename.replace('.md', '')))

        if category == "blog":
            # 基于 title 的 UNIQUE 索引，INSERT OR REPLACE 会自动更新已有文章
            sql = f"""
            INSERT OR REPLACE INTO posts (title, category, post_type, language, content, thumb_url)
            VALUES ('{title}', '{post.get('category','thoughts')}', '{post.get('post_type','')}', 
            '{post.get('language','')}', '{safe_content}', '{post.get('thumb', 'backgrounds/wall1.jpg')}');
            """
            run_sql(db_name, sql)
        else:
            # Wiki 逻辑
            parent_title = post.get('parent_title')
            p_id = 0
            if parent_title:
                run_sql(db_name, f"INSERT OR IGNORE INTO wiki_nodes (title, parent_id) VALUES ('{sql_escape(parent_title)}', 0)")
                p_res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title = '{sql_escape(parent_title)}' LIMIT 1")
                p_id = get_id_from_json(p_res) or 0
            
            run_sql(db_name, f"INSERT OR REPLACE INTO wiki_nodes (title, parent_id, has_content) VALUES ('{title}', {p_id}, 1)")
            curr_res = run_sql(db_name, f"SELECT id FROM wiki_nodes WHERE title = '{title}' AND parent_id = {p_id} LIMIT 1")
            curr_id = get_id_from_json(curr_res)
            if curr_id:
                run_sql(db_name, f"INSERT OR REPLACE INTO wiki_contents (node_id, content) VALUES ({curr_id}, '{safe_content}')")
        
        print(f"✅ 同步成功: {title}")

if __name__ == "__main__":
    process_sync("blog")
    process_sync("wiki")