<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Navbar from '../components/Navbar.vue'

const messages = ref([])
const bannerUrl = ref('')
const loading = ref(true)
const API_BASE = 'GITHUB-SC'

// 控制展开的索引集合
const expandedIndices = ref(new Set())

const toggleExpand = (index) => {
  if (expandedIndices.value.has(index)) {
    expandedIndices.value.delete(index)
  } else {
    expandedIndices.value.add(index)
  }
}

onMounted(async () => {
  try {
    const [mRes, bgRes] = await Promise.all([
      axios.get(`${API_BASE}/api/messages`),
      axios.get(`${API_BASE}/api/random-bg`)
    ])
    messages.value = mRes.data
    bannerUrl.value = bgRes.data.url
  } catch (err) {
    bannerUrl.value = `${API_BASE}/img/backgrounds/wall1.jpg`
  } finally {
    loading.value = false
  }
})

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('zh-CN', { 
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
  })
}
</script>

<template>
  <div class="page-wrapper">
    <Navbar />

    <header class="hero" :style="{ backgroundImage: `url(${bannerUrl})` }">
      <div class="hero-content">
        <h1 class="hero-title">留言板</h1>
        <p class="hero-subtitle">由 Email Workers 驱动的信件流</p>
      </div>
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

    <main class="message-container">
      <div v-if="loading" class="loading">正在开启信箱...</div>
      <div v-else-if="messages.length === 0" class="empty">📭 信箱空空的，发封邮件来看看？</div>

      <div v-for="(msg, index) in messages" :key="index" 
           class="msg-card glass-card" 
           :class="{ expanded: expandedIndices.has(index) }">
        
        <div class="msg-header">
          <div class="msg-meta">
            <span class="msg-date">{{ formatDate(msg.date) }}</span>
            <span class="msg-nickname">From: <b>{{ msg.nickname }}</b></span>
          </div>
          <h3 class="msg-subject">{{ msg.subject }}</h3>
        </div>

        <div class="divider"></div>

        <div class="msg-body">
          <p class="content-text">
            {{ expandedIndices.has(index) ? msg.content : (msg.content.slice(0, 50) + (msg.content.length > 50 ? '...' : '')) }}
          </p>
          <button class="expand-btn" @click="toggleExpand(index)">
            {{ expandedIndices.has(index) ? '收起信件 ↑' : '展开阅读 ↓' }}
          </button>
        </div>
      </div>
      <div class="bottom-padding"></div>
    </main>
  </div>
</template>

<style scoped>
.message-container {
  max-width: 800px;
  margin: -40px auto 0;
  padding: 0 20px;
  position: relative;
  z-index: 10;
}

.hero-content {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: white;
  text-shadow: 0 2px 10px rgba(0,0,0,0.3);
}
.hero-title { font-size: 2.5rem; margin-bottom: 10px; }

.msg-card {
  margin-bottom: 20px;
  padding: 20px;
  text-align: left;
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.msg-card:hover { transform: translateY(-3px); border-color: var(--mtf-pink); }

.msg-header { margin-bottom: 12px; }
.msg-meta { 
  display: flex; 
  justify-content: space-between; 
  font-size: 0.8rem; 
  color: var(--text-dim); 
  margin-bottom: 8px;
}
.msg-nickname b { color: var(--mtf-lavender); }
.msg-subject { font-size: 1.1rem; color: var(--text-main); }

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border-color), transparent);
  margin: 15px 0;
}

.msg-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.content-text {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-dim);
  white-space: pre-wrap; /* 保留邮件换行 */
}

.expand-btn {
  align-self: flex-end;
  background: transparent;
  border: 1px solid var(--mtf-pink);
  color: var(--mtf-pink);
  padding: 4px 12px;
  border-radius: 15px;
  font-size: 0.75rem;
  cursor: pointer;
  transition: 0.3s;
}

.expand-btn:hover {
  background: var(--mtf-pink);
  color: white;
}

.loading, .empty { text-align: center; padding: 50px; color: var(--text-dim); }

/* 复用原有的 hero 动画和 glass-card 样式 */
.hero { height: 45vh; background: center/cover no-repeat; position: relative; }
/* ... (其余动画样式与主页一致) ... */
</style>