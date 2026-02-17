<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css' 
import Navbar from '../components/Navbar.vue'

const route = useRoute()
const post = ref(null)
const renderedContent = ref('')
const API_BASE = 'GITHUB-SC'

marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
    return hljs.highlightAuto(code).value
  },
  breaks: true 
})

onMounted(async () => {
  try {
    const res = await axios.get(`${API_BASE}/api/posts/${route.params.id}`)
    post.value = res.data
    renderedContent.value = marked(post.value.content)
    post.value.cover = post.value.thumb_url?.startsWith('http') 
      ? post.value.thumb_url 
      : `${API_BASE}/img/${post.value.thumb_url}`
    window.scrollTo(0, 0)
  } catch (err) { console.error('获取文章详情失败:', err) }
})
</script>

<template>
  <div class="detail-page" v-if="post">
    <Navbar />
    <header class="post-hero" :style="{ backgroundImage: `url(${post.cover})` }">
      <div class="hero-mask"></div>
      <div class="hero-content">
        <h1>{{ post.title }}</h1>
        <p class="meta">{{ new Date(post.date).toLocaleDateString() }} · xieerfan</p>
      </div>
      <div class="wave-wrap">
        <svg class="waves" viewBox="0 24 150 28" preserveAspectRatio="none">
          <use xlink:href="#w" x="48" y="7" fill="var(--bg-main)" />
          <defs><path id="w" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" /></defs>
        </svg>
      </div>
    </header>

    <article class="post-article">
      <div class="glass-card article-container">
        <div class="markdown-body" v-html="renderedContent"></div>
        <router-link to="/" class="back-link">← 返回首页</router-link>
      </div>
    </article>
  </div>
</template>

<style scoped>
.detail-page { background: var(--bg-main); min-height: 100vh; }
.post-hero { height: 55vh; background: center/cover; position: relative; display: flex; align-items: center; justify-content: center; color: #fff; }
.hero-mask { position: absolute; inset: 0; background: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(0,0,0,0.1)); }
.hero-content { position: relative; text-align: center; z-index: 2; padding: 0 20px; }
.hero-content h1 { font-size: 2.8rem; margin-bottom: 15px; text-shadow: 0 2px 10px rgba(0,0,0,0.3); }
.meta { opacity: 0.9; font-weight: bold; letter-spacing: 1px; }

.wave-wrap { position: absolute; bottom: -1px; width: 100%; line-height: 0; }
.waves { width: 100%; height: 60px; }

.post-article { max-width: 900px; margin: -60px auto 100px; position: relative; z-index: 5; padding: 0 20px; }
.article-container { padding: 60px; line-height: 1.8; }

.back-link { 
  display: inline-block; margin-top: 50px; color: var(--mtf-pink); 
  text-decoration: none; font-weight: bold; transition: 0.3s;
}
.back-link:hover { transform: translateX(-5px); color: var(--mtf-blue); }

@media (max-width: 768px) {
  .hero-content h1 { font-size: 1.8rem; }
  .article-container { padding: 30px 20px; }
}
</style>

<style>
/* Markdown 渲染全局样式适配 Catppuccin */
.markdown-body { color: var(--text-main); font-size: 1.05rem; }
.markdown-body h1, .markdown-body h2, .markdown-body h3 { 
  color: var(--mtf-lavender); margin: 2rem 0 1rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;
}
.markdown-body p { margin-bottom: 1.2rem; }
.markdown-body strong { color: var(--mtf-pink); }
.markdown-body blockquote { 
  border-left: 4px solid var(--mtf-blue); background: var(--search-bg); 
  padding: 10px 20px; margin: 1.5rem 0; border-radius: 0 8px 8px 0;
}
.markdown-body pre { 
  background: #1e1e2e !important; padding: 1.5rem; border-radius: 15px; 
  overflow-x: auto; border: 1px solid var(--border-color);
}
.markdown-body code { font-family: 'Fira Code', monospace; background: var(--search-bg); padding: 2px 5px; border-radius: 4px; color: var(--mtf-pink); }
.markdown-body img { max-width: 100%; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
</style>