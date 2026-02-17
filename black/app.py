import os
import random
import psutil
import time
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_cors import CORS 

app = Flask(__name__)
app.secret_key = 'arch_linux_is_the_best_2026' # 别告诉别人
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- 1. 目录与数据库配置 ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'blog.db')
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static/uploads')
app.config['BG_FOLDER'] = os.path.join(basedir, 'static/images')

# 确保文件夹存在
for p in [app.config['UPLOAD_FOLDER'], app.config['BG_FOLDER']]:
    os.makedirs(p, exist_ok=True)

db = SQLAlchemy(app)

# --- 2. 数据库模型 ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    thumbnail = db.Column(db.String(200))
    views = db.Column(db.Integer, default=0) # 单篇文章阅读量
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)

class UserConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), default="魔法使のArch")
    bio = db.Column(db.String(200), default="既然不喜欢渐变，那就让波浪动起来")
    avatar = db.Column(db.String(200), default="default_avatar.png")
    total_views = db.Column(db.Integer, default=0) # 站点总访问量

# 初始化数据库
with app.app_context():
    db.create_all()
    if not UserConfig.query.first():
        db.session.add(UserConfig())
        db.session.commit()

# --- 3. 权限装饰器 ---
def login_required(f):
    @wraps(f)
    def dec(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dec

# --- 4. 前端 Vue 使用的 API 接口 ---

@app.route('/api/user')
def api_user():
    u = UserConfig.query.first()
    return jsonify({
        'nickname': u.nickname,
        'bio': u.bio,
        'avatar_url': f"http://127.0.0.1:5000/static/uploads/{u.avatar}",
        'total_views': u.total_views
    })

@app.route('/api/posts')
def api_posts():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return jsonify([{
        'id': p.id,
        'title': p.title,
        'content': p.content[:100],
        'thumb_url': f"http://127.0.0.1:5000/static/uploads/{p.thumbnail}" if p.thumbnail else None,
        'views': p.views,
        'date': p.date_posted.strftime('%Y-%m-%d')
    } for p in posts])

@app.route('/api/posts/<int:post_id>')
def api_post_detail(post_id):
    p = Post.query.get_or_404(post_id)
    u = UserConfig.query.first()
    # 增加阅读计数
    p.views += 1
    u.total_views += 1
    db.session.commit()
    return jsonify({
        'id': p.id,
        'title': p.title,
        'content': p.content,
        'cover': f"http://127.0.0.1:5000/static/uploads/{p.thumbnail}" if p.thumbnail else None,
        'date': p.date_posted.strftime('%Y-%m-%d'),
        'author': u.nickname,
        'views': p.views
    })

@app.route('/api/random-bg')
def api_random_bg():
    imgs = [f for f in os.listdir(app.config['BG_FOLDER']) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    url = f"http://127.0.0.1:5000/static/images/{random.choice(imgs)}" if imgs else ""
    return jsonify({"url": url})

# --- 5. 后台系统监控 API (仅限登录用户) ---

@app.route('/api/sys_stats')
@login_required
def api_sys_stats():
    return jsonify({
        'cpu': psutil.cpu_percent(interval=None),
        'ram': psutil.virtual_memory().percent,
        'disk': psutil.disk_usage('/').percent,
        'net_sent': psutil.net_io_counters().bytes_sent,
        'net_recv': psutil.net_io_counters().bytes_recv,
        'timestamp': time.time()
    })

# --- 6. 后台管理页面 (4个 Tab 分离) ---

# Tab 1: 文章管理列表
@app.route('/admin')
@login_required
def admin_index():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('admin/index.html', posts=posts)

# Tab 2: 背景图管理
@app.route('/admin/backgrounds')
@login_required
def admin_backgrounds():
    bgs = [f for f in os.listdir(app.config['BG_FOLDER']) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    return render_template('admin/backgrounds.html', bgs=bgs)

# Tab 3: 个人信息设置
@app.route('/admin/info')
@login_required
def admin_info():
    user = UserConfig.query.first()
    return render_template('admin/info.html', user=user)

# Tab 4: 系统监控面板
@app.route('/admin/monitor')
@login_required
def admin_monitor():
    return render_template('admin/monitor.html')

# --- 7. 后台功能处理路由 ---

# 写文章/编辑文章页面
@app.route('/admin/write', defaults={'post_id': None})
@app.route('/admin/edit/<int:post_id>')
@login_required
def admin_write(post_id):
    post = Post.query.get(post_id) if post_id else None
    return render_template('admin/write.html', post=post)

# 保存文章
@app.route('/admin/save_post', methods=['POST'])
@login_required
def save_post():
    pid = request.form.get('post_id')
    post = Post.query.get(pid) if pid else Post()
    if not pid:
        db.session.add(post)
    post.title = request.form.get('title')
    post.content = request.form.get('content')
    f = request.files.get('cover')
    if f and f.filename:
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        post.thumbnail = f.filename
    db.session.commit()
    return redirect(url_for('admin_index'))

# 删除文章
@app.route('/admin/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('admin_index'))

# 上传背景图
@app.route('/admin/bg/upload', methods=['POST'])
@login_required
def upload_bg():
    f = request.files.get('bg_file')
    if f and f.filename:
        f.save(os.path.join(app.config['BG_FOLDER'], f.filename))
    return redirect(url_for('admin_backgrounds'))

# 删除背景图
@app.route('/admin/bg/delete/<filename>')
@login_required
def delete_bg(filename):
    p = os.path.join(app.config['BG_FOLDER'], filename)
    if os.path.exists(p):
        os.remove(p)
    return redirect(url_for('admin_backgrounds'))

# 保存个人信息
@app.route('/admin/info/save', methods=['POST'])
@login_required
def save_info():
    u = UserConfig.query.first()
    u.nickname = request.form.get('nickname')
    u.bio = request.form.get('bio')
    f = request.files.get('avatar_file')
    if f and f.filename:
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))
        u.avatar = f.filename
    db.session.commit()
    return redirect(url_for('admin_info'))

# --- 8. 登录逻辑 ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 别忘了改你的默认密码
        if request.form.get('username') == "admin" and request.form.get('password') == "123456":
            session['logged_in'] = True
            return redirect(url_for('admin_index'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    # Arch 开发者模式开启
    app.run(debug=True, port=5000)