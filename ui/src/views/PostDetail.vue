<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const post = ref(null)

onMounted(async () => {
  const res = await axios.get(`http://127.0.0.1:5000/api/posts/${route.params.id}`)
  post.value = res.data
  window.scrollTo(0, 0)
})
</script>

<template>
  <div class="detail-page" v-if="post">
    <header class="post-hero" :style="{ backgroundImage: `url(${post.cover})` }">
      <div class="hero-content">
        <h1>{{ post.title }}</h1>
        <p>{{ post.date }} · {{ post.author }}</p>
      </div>
      <div class="wave-wrap">
        <svg class="waves" viewBox="0 24 150 28" preserveAspectRatio="none">
          <use xlink:href="#w" x="48" y="7" fill="#fff" />
        </svg>
      </div>
    </header>

    <article class="post-article">
      <div class="glass-card">
        <div class="content" v-html="post.content"></div>
        <router-link to="/" class="back">← 回到魔法首页</router-link>
      </div>
    </article>
  </div>
</template>

<style scoped>
.post-hero { height: 50vh; background: center/cover; position: relative; display: flex; align-items: center; justify-content: center; color: #fff; }
.hero-content { text-align: center; background: rgba(0,0,0,0.2); padding: 40px; border-radius: 20px; backdrop-filter: blur(5px); }
.hero-content h1 { font-size: 2.5rem; margin-bottom: 10px; }
.wave-wrap { position: absolute; bottom: 0; width: 100%; line-height: 0; }
.waves { width: 100%; height: 50px; }
.post-article { max-width: 900px; margin: -50px auto 100px; position: relative; padding: 0 20px; }
.glass-card { background: #fff; padding: 50px; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.05); line-height: 2; font-size: 1.1rem; }
.content { white-space: pre-wrap; color: #333; }
.back { display: inline-block; margin-top: 40px; color: #a29bfe; text-decoration: none; font-weight: bold; }
</style>