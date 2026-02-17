<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const posts = ref([])
const bannerUrl = ref('')
const user = ref({ nickname: '', bio: '', avatar_url: '' })

onMounted(async () => {
  const [uRes, pRes, bgRes] = await Promise.all([
    axios.get('http://127.0.0.1:5000/api/user'),
    axios.get('http://127.0.0.1:5000/api/posts'),
    axios.get('http://127.0.0.1:5000/api/random-bg')
  ])
  user.value = uRes.data
  posts.value = pRes.data
  bannerUrl.value = bgRes.data.url
})

const goDetail = (id) => router.push(`/post/${id}`)
</script>

<template>
  <div class="page">
    <header class="hero" :style="{ backgroundImage: `url(${bannerUrl})` }">
      <div class="wave-wrap">
        <svg class="waves" viewBox="0 24 150 28" preserveAspectRatio="none">
          <defs><path id="w" d="M-160 44c30 0 58-18 88-18s 58 18 88 18 58-18 88-18 58 18 88 18 v44h-352z" /></defs>
          <g class="parallax">
            <use xlink:href="#w" x="48" y="0" fill="rgba(255,255,255,0.7)" />
            <use xlink:href="#w" x="48" y="7" fill="#fff" />
          </g>
        </svg>
      </div>
    </header>

    <section class="profile">
      <img :src="user.avatar_url" class="avatar">
      <h1>{{ user.nickname }}</h1>
      <p>{{ user.bio }}</p>
    </section>

    <main class="list">
      <div v-for="p in posts" :key="p.id" class="card" @click="goDetail(p.id)">
        <img :src="p.thumb_url" class="thumb">
        <div class="info">
          <h2>{{ p.title }}</h2>
          <p>{{ p.content }}</p>
          <div class="meta"><span>📅 {{ p.date }}</span> <button>阅读全文</button></div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.hero { height: 45vh; background: center/cover; position: relative; }
.wave-wrap { position: absolute; bottom: 0; width: 100%; line-height: 0; }
.waves { width: 100%; height: 10vh; }
.parallax > use { animation: move 20s linear infinite; }
@keyframes move { 0% { transform: translate3d(-90px,0,0); } 100% { transform: translate3d(85px,0,0); } }
.profile { text-align: center; margin-top: -60px; position: relative; z-index: 2; }
.avatar { width: 120px; height: 120px; border-radius: 50%; border: 5px solid #fff; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
.list { max-width: 800px; margin: 40px auto; padding: 0 20px; }
.card { display: flex; background: #fff; border-radius: 15px; overflow: hidden; margin-bottom: 25px; cursor: pointer; border: 1px solid #eee; transition: 0.3s; }
.card:hover { transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
.thumb { width: 280px; height: 180px; object-fit: cover; }
.info { padding: 20px; flex: 1; display: flex; flex-direction: column; }
.info h2 { color: #a29bfe; margin-bottom: 10px; }
.info p { color: #666; font-size: 0.9rem; flex: 1; }
.meta { display: flex; justify-content: space-between; align-items: center; margin-top: 15px; color: #bbb; font-size: 0.8rem; }
button { background: #a29bfe; color: #fff; border: none; padding: 6px 15px; border-radius: 20px; }
</style>