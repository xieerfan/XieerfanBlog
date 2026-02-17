<script setup>
import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'
import Navbar from '../components/Navbar.vue'

const router = useRouter()
const posts = ref([])
const bannerUrl = ref('')
const user = ref({ nickname: '', bio: '', avatar_url: '', signatures: '' })
const searchQuery = ref('')
const API_BASE = 'GITHUB-SC'

const sigList = ref([])
const currentSigIndex = ref(0)
let sigTimer = null

const currentSig = computed(() => sigList.value.length > 0 ? sigList.value[currentSigIndex.value] : '载入中...')
const startSigCycle = () => { if (sigList.value.length > 1) sigTimer = setInterval(() => { currentSigIndex.value = (currentSigIndex.value + 1) % sigList.value.length }, 5000) }

const selectedCategory = ref('all') 
const selectedLanguage = ref('all') 
watch(selectedCategory, () => { selectedLanguage.value = 'all' })

const availableLanguages = computed(() => {
  const langs = posts.value.filter(p => p.category === 'programming' && p.language).map(p => p.language)
  return ['all', ...new Set(langs)]
})

const filteredPosts = computed(() => {
  return posts.value.filter(p => {
    const s = searchQuery.value.toLowerCase()
    const matchSearch = !s || p.title.toLowerCase().includes(s) || (p.summary && p.summary.toLowerCase().includes(s))
    const matchCategory = selectedCategory.value === 'all' || p.category === selectedCategory.value
    const matchLang = selectedCategory.value !== 'programming' || selectedLanguage.value === 'all' || p.language === selectedLanguage.value
    return matchSearch && matchCategory && matchLang
  })
})

onMounted(async () => {
  try {
    const [uRes, pRes, bgRes] = await Promise.all([
      axios.get(`${API_BASE}/api/user`),
      axios.get(`${API_BASE}/api/posts`),
      axios.get(`${API_BASE}/api/random-bg`)
    ])
    user.value = uRes.data
    posts.value = pRes.data
    bannerUrl.value = bgRes.data.url
    if (user.value.signatures) { sigList.value = user.value.signatures.split('|'); startSigCycle() }
  } catch (err) { bannerUrl.value = `${API_BASE}/img/backgrounds/wall1.jpg` }
})

onUnmounted(() => { if (sigTimer) clearInterval(sigTimer) })
const getThumb = (url) => url ? (url.startsWith('http') ? url : `${API_BASE}/img/${url}`) : `${API_BASE}/img/backgrounds/wall1.jpg`
const goDetail = (id) => router.push(`/post/${id}`)
</script>

<template>
  <div class="page-wrapper">
    <Navbar v-model="searchQuery" />

    <header class="hero" :style="{ backgroundImage: `url(${bannerUrl})` }">
      <div class="wave-wrap">
        <svg class="waves" viewBox="0 24 150 28" preserveAspectRatio="none">
          <defs><path id="w" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" /></defs>
          <g class="parallax">
            <use xlink:href="#w" x="48" y="0" fill="var(--wave-top)" />
            <use xlink:href="#w" x="48" y="7" fill="var(--bg-main)" />
          </g>
        </svg>
      </div>
    </header>

    <div class="main-layout">
      <aside class="sidebar">
        <div class="sidebar-sticky">
          <div class="profile-box glass-card">
            <div class="avatar-container">
              <img :src="getThumb(user.avatar_url)" class="avatar">
            </div>
            <h2 class="nickname">{{ user.nickname || '载入中...' }}</h2>
            <p class="bio">{{ user.bio }}</p>
          </div>

          <div class="side-card sig-card glass-card">
            <h3 class="side-title">💬 简讯</h3>
            <div class="sig-content">
              <transition name="slide-fade" mode="out-in">
                <p :key="currentSigIndex" class="sig-text">{{ currentSig }}</p>
              </transition>
            </div>
          </div>

          <div class="side-card glass-card">
            <h3 class="side-title">📂 分类导航</h3>
            <div class="nav-list">
              <button :class="{ active: selectedCategory === 'all' }" @click="selectedCategory = 'all'">全部文章</button>
              <button :class="{ active: selectedCategory === 'programming' }" @click="selectedCategory = 'programming'">💻 开发笔记</button>
              <button :class="{ active: selectedCategory === 'thoughts' }" @click="selectedCategory = 'thoughts'">🍃 碎碎念</button>
            </div>
          </div>

          <div class="side-card glass-card">
            <h3 class="side-title">🔗 社交账号</h3>
            <div class="social-grid">
              <a href="https://space.bilibili.com/522560884" target="_blank" class="s-link">📺 Bilibili</a>
              <a href="https://x.com/xieerfan" target="_blank" class="s-link">🐦 X / Twitter</a>
              <a href="https://github.com/xieerfan" target="_blank" class="s-link">🐱 Github</a>
            </div>
          </div>
        </div>
      </aside>

      <main class="post-area">
        <div v-if="filteredPosts.length === 0" class="empty-state">🐢 这里空空如也喵...</div>
        <div v-for="p in filteredPosts" :key="p.id" class="post-card glass-card" @click="goDetail(p.id)">
          <div class="thumb-box"><img :src="getThumb(p.thumb_url)" class="card-img"></div>
          <div class="post-content">
            <div class="tag-row">
              <span class="category-pill">{{ p.category === 'programming' ? 'Code' : 'Thoughts' }}</span>
              <span class="date-text">{{ new Date(p.date).toLocaleDateString() }}</span>
            </div>
            <h2 class="title">{{ p.title }}</h2>
            <p class="summary">{{ p.summary }}...</p>
            <div class="footer"><span class="read-more">Read More →</span></div>
          </div>
        </div>
        <div class="bottom-padding"></div>
      </main>
    </div>
  </div>
</template>

<style>
/* 全局主题变量 - 适配 Catppuccin Mocha Pink MTF */
:root {
  --bg-main: #fcfcfc;
  --nav-bg: rgba(255, 255, 255, 0.75);
  --text-main: #4c4f69;
  --text-dim: #6c6f85;
  --mtf-pink: #f5c2e7;
  --mtf-blue: #74c7ec;
  --mtf-lavender: #cba6f7;
  --border-color: rgba(0, 0, 0, 0.05);
  --card-bg: rgba(255, 255, 255, 0.8);
  --search-bg: rgba(0, 0, 0, 0.05);
  --tab-active-bg: rgba(245, 194, 231, 0.15);
  --wave-top: rgba(255, 255, 255, 0.7);
}

html.dark {
  --bg-main: #1e1e2e;
  --nav-bg: rgba(30, 30, 46, 0.8);
  --text-main: #cdd6f4;
  --text-dim: #a6adc8;
  --mtf-pink: #f5c2e7;
  --mtf-blue: #89b4fa;
  --mtf-lavender: #cba6f7;
  --border-color: rgba(255, 255, 255, 0.1);
  --card-bg: rgba(49, 50, 68, 0.6);
  --search-bg: rgba(255, 255, 255, 0.1);
  --tab-active-bg: rgba(203, 166, 247, 0.2);
  --wave-top: rgba(30, 30, 46, 0.5);
}

body { background-color: var(--bg-main); color: var(--text-main); transition: 0.3s; }
</style>

<style scoped>
.page-wrapper { min-height: 100vh; }
.hero { height: 40vh; background: center/cover no-repeat; position: relative; }
.wave-wrap { position: absolute; bottom: -1px; width: 100%; line-height: 0; }
.waves { width: 100%; height: 80px; }
.parallax > use { animation: move 20s linear infinite; }
@keyframes move { 0% { transform: translate3d(-90px,0,0); } 100% { transform: translate3d(85px,0,0); } }

.main-layout { display: flex; max-width: 1200px; margin: 0 auto; padding: 0 20px; gap: 30px; }
.sidebar { width: 260px; flex-shrink: 0; }
.sidebar-sticky { position: sticky; top: 80px; z-index: 20; }

.glass-card { 
  background: var(--card-bg); border-radius: 20px; 
  backdrop-filter: blur(10px); border: 1px solid var(--border-color);
  box-shadow: 0 8px 32px rgba(0,0,0,0.05); transition: 0.3s;
}

.profile-box { padding: 0 20px 20px; text-align: center; margin-top: -60px; margin-bottom: 20px; }
.avatar-container { display: inline-block; padding: 5px; background: var(--bg-main); border-radius: 50%; margin-top: -50px; margin-bottom: 10px; }
.avatar { width: 100px; height: 100px; border-radius: 50%; object-fit: cover; border: 3px solid var(--mtf-blue); }
.nickname { font-size: 1.3rem; margin-bottom: 5px; color: var(--text-main); }
.bio { font-size: 0.8rem; color: var(--text-dim); line-height: 1.4; }

.side-card { padding: 20px; margin-bottom: 20px; }
.side-title { font-size: 0.75rem; color: var(--mtf-lavender); font-weight: 800; margin-bottom: 12px; text-transform: uppercase; }

.sig-card { border-left: 4px solid var(--mtf-pink); }
.sig-text { font-size: 0.85rem; color: var(--text-dim); font-style: italic; }

.nav-list { display: flex; flex-direction: column; gap: 8px; }
.nav-list button { text-align: left; padding: 10px 15px; border-radius: 12px; border: none; background: transparent; color: var(--text-dim); cursor: pointer; transition: 0.3s; }
.nav-list button:hover { color: var(--mtf-blue); }
.nav-list button.active { background: var(--mtf-lavender); color: #fff; }

.social-grid { display: flex; flex-direction: column; gap: 10px; }
.s-link { text-decoration: none; color: var(--text-dim); font-size: 0.9rem; transition: 0.2s; }
.s-link:hover { color: var(--mtf-pink); transform: translateX(5px); }

.post-area { flex: 1; padding-top: 40px; }
.post-card { display: flex; overflow: hidden; margin-bottom: 25px; min-height: 180px; cursor: pointer; }
.post-card:hover { transform: translateY(-5px); border-color: var(--mtf-pink); }
.thumb-box { width: 280px; flex-shrink: 0; }
.card-img { width: 100%; height: 100%; object-fit: cover; }
.post-content { flex: 1; padding: 20px; display: flex; flex-direction: column; text-align: left; }
.category-pill { font-size: 0.7rem; color: var(--mtf-blue); font-weight: bold; }
.title { font-size: 1.3rem; color: var(--text-main); margin: 5px 0 10px; }
.summary { font-size: 0.9rem; color: var(--text-dim); line-height: 1.6; flex: 1; }
.read-more { font-size: 0.85rem; color: var(--mtf-lavender); font-weight: bold; }

.bottom-padding { height: 100px; }
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.5s ease; }
.slide-fade-enter-from { opacity: 0; transform: translateY(10px); }
.slide-fade-leave-to { opacity: 0; transform: translateY(-10px); }

@media (max-width: 850px) {
  .main-layout { flex-direction: column; }
  .sidebar { width: 100%; }
  .post-card { flex-direction: column; }
  .thumb-box { width: 100%; height: 180px; }
}
</style>