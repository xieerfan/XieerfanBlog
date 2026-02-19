<script setup>
import { ref, onMounted } from 'vue'
const props = defineProps(['modelValue', 'isWiki'])
const emit = defineEmits(['update:modelValue', 'search'])

const isDark = ref(localStorage.getItem('theme') === 'dark')

const toggleTheme = () => {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', theme)
}

onMounted(() => {
  if (isDark.value) document.documentElement.classList.add('dark')
})

const handleInput = (e) => {
  emit('update:modelValue', e.target.value)
  emit('search')
}
</script>

<template>
  <nav class="navbar">
    <div class="nav-container">
      <div class="tabs">
        <router-link to="/" class="tab-item" active-class="active">主页</router-link>
        <router-link to="/wiki" class="tab-item" active-class="active">Wiki</router-link>
        <router-link to="/contact" class="tab-item" active-class="active">骚扰作者</router-link>
        <router-link to="/messages" class="tab-item" active-class="active">留言板</router-link>
      </div>
      
      <div class="search-wrapper">
        <button class="theme-toggle" @click="toggleTheme">
          {{ isDark ? '🌙' : '☀️' }}
        </button>

        <div class="search-bar">
          <input 
            type="text" 
            :value="modelValue" 
            @input="handleInput"
            :placeholder="isWiki ? '搜索 Wiki...' : '搜索博文...'"
          />
          <span class="search-icon">🔍</span>
        </div>
        <slot name="search-dropdown"></slot>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed; top: 0; left: 0; right: 0; height: 60px;
  background: var(--nav-bg); backdrop-filter: blur(15px);
  z-index: 1000; border-bottom: 1px solid var(--border-color);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); display: flex; align-items: center;
  transition: background 0.3s;
}
.nav-container { max-width: 1200px; width: 100%; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; }
.tabs { display: flex; gap: 10px; }
.tab-item { text-decoration: none; color: var(--text-dim); font-weight: bold; padding: 6px 12px; border-radius: 8px; transition: 0.3s; font-size: 0.95rem; }
.tab-item.active { color: var(--mtf-pink); background: var(--tab-active-bg); }

.search-wrapper { position: relative; display: flex; align-items: center; gap: 12px; }
.theme-toggle { background: transparent; border: none; font-size: 1.2rem; cursor: pointer; padding: 5px; border-radius: 50%; transition: 0.3s; }
.theme-toggle:hover { background: var(--border-color); }

.search-bar { background: var(--search-bg); padding: 5px 15px; border-radius: 20px; display: flex; align-items: center; border: 1px solid transparent; transition: 0.3s; }
.search-bar:focus-within { border-color: var(--mtf-blue); }
.search-bar input { border: none; background: transparent; outline: none; width: 140px; color: var(--text-main); font-size: 0.9rem; }
.search-icon { font-size: 0.9rem; opacity: 0.6; }

@media (max-width: 600px) { .search-bar input { width: 80px; } }
</style>