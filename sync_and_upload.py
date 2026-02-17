import os
import re
import boto3
import frontmatter
import subprocess
import json
import sys

# --- 从环境变量读取配置 (GitHub Secrets) ---
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY") 
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET = "xieerfan-blog"
PUBLIC_DOMAIN = os.getenv("API_BASE_URL").replace("/api", "") + "/img" # 自动推导图片代理地址

# 初始化 R2 (S3 兼容)
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

def upload_to_r2(local_path, folder_prefix):
    """上传并返回 R2 URL"""
    file_name = os.path.basename(local_path)
    remote_key = f"{folder_prefix}/{file_name}"
    try:
        # 简单判断 ContentType
        content_type = "image/png" if file_name.endswith(".png") else "image/jpeg"
        s3.upload_file(local_path, R2_BUCKET, remote_key, ExtraArgs={'ContentType': content_type})
        print(f"  ✅ Uploaded: {remote_key}")
        return f"{PUBLIC_DOMAIN}/{remote_key}"
    except Exception as e:
        print(f"  ❌ Upload Failed {file_name}: {e}")
        return None

def process_and_sync(content_type):
    """处理 blog 或 wiki 文件夹"""
    base_dir = f"./{content_type}"
    db_name = f"xieerfan-{content_type}"
    if not os.path.exists(base_dir): return

    for filename in os.listdir(base_dir):
        if not filename.endswith(".md"): continue
        path = os.path.join(base_dir, filename)
        post = frontmatter.load(path)
        content = post.content

        # 1. 查找并替换本地图片路径 (例如 images/xxx.png)
        # 匹配 ![alt](images/xxx.png)
        img_pattern = r'!\[(.*?)\]\((images/.+?)\)'
        
        def img_replacer(match):
            alt_text = match.group(1)
            rel_img_path = match.group(2)
            full_img_path = os.path.join(base_dir, rel_img_path)
            
            if os.path.exists(full_img_path):
                remote_url = upload_to_r2(full_img_path, content_type)
                return f"![{alt_text}]({remote_url})" if remote_url else match.group(0)
            return match.group(0)

        new_content = re.sub(img_pattern, img_replacer, content)
        safe_content = sql_escape(new_content.strip())
        title = sql_escape(post.get('title', filename.replace('.md', '')))

        # 2. 执行数据库入库
        if content_type == "blog":
            sql = f"""
            INSERT OR REPLACE INTO posts (title, category, post_type, language, content, thumb_url, date)
            VALUES ('{title}', '{post.get('category','')}', '{post.get('post_type','')}', 
            '{post.get('language','')}', '{safe_content}', '{post.get('thumb', 'backgrounds/wall1.jpg')}', CURRENT_TIMESTAMP);
            """
            run_sql(db_name, sql)
        else:
            # Wiki 逻辑：处理父子节点
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
        
        print(f"✨ {content_type.upper()} Synced: {title}")

if __name__ == "__main__":
    process_and_sync("blog")
    process_and_sync("wiki")