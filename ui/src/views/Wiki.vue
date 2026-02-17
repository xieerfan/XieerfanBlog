<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { marked } from 'marked'
import Navbar from '../components/Navbar.vue'

const API_BASE = 'GITHUB-SC'
const structuredTree = ref([]) 
const currentContent = ref('')
const toc = ref([])
const activeNodeId = ref(null)
const searchQuery = ref('')
const searchResults = ref([])

const fetchTree = async () => {
  const res = await axios.get(`${API_BASE}/api/wiki/tree`)
  structuredTree.value = buildTree(res.data, 0)
}
const buildTree = (nodes, parentId) => nodes.filter(n => n.parent_id === parentId).map(n => ({ ...n, children: buildTree(nodes, n.id) }))

const handleSearch = async () => {
  if (!searchQuery.value) { searchResults.value = []; return }
  const res = await axios.get(`${API_BASE}/api/wiki/search?q=${searchQuery.value}`)
  searchResults.value = res.data
}

const loadContent = async (node) => {
  activeNodeId.value = node.id
  searchResults.value = []
  searchQuery.value = ''
  const res = await axios.get(`${API_BASE}/api/wiki/content/${node.id}`)
  currentContent.value = res.data.content
  await nextTick(); generateTOC()
}

const generateTOC = () => {
  const headings = document.querySelector('.wiki-render').querySelectorAll('h1, h2, h3, h4')
  toc.value = Array.from(headings).map((h, i) => { 
    h.id = `toc-${i}`; 
    return { id: `toc-${i}`, text: h.innerText, level: parseInt(h.tagName[1]) } 
  })
}

const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
onMounted(() => fetchTree())
</script>

<template>
  <div class="wiki-page">
    <Navbar v-model="searchQuery" :isWiki="true" @search="handleSearch">
      <template #search-dropdown>
        <div v-if="searchResults.length" class="search-dropdown glass-card">
          <div v-for="res in searchResults" :key="res.id" class="search-res-item" @click="loadContent(res)">
            <div class="res-title">{{ res.title }}</div>
            <div class="res-snippet">{{ res.snippet }}...</div>
          </div>
        </div>
      </template>
    </Navbar>

    <div class="wiki-layout">
      <aside class="wiki-aside-left">
        <div class="tree-container">
          <div v-for="node in structuredTree" :key="node.id" class="node-group">
            <div class="node-item level-1" @click="loadContent(node)">📂 {{ node.title }}</div>
            <div v-for="child in node.children" :key="child.id" 
                 :class="['node-item level-2', { active: activeNodeId === child.id }]" 
                 @click="loadContent(child)">
              {{ child.children.length > 0 ? '📁' : '📝' }} {{ child.title }}
            </div>
          </div>
        </div>
      </aside>

      <main class="wiki-main">
        <div class="glass-paper">
          <div v-if="currentContent" class="wiki-render markdown-body" v-html="marked(currentContent)"></div>
          <div v-else class="wiki-empty">
            <div class="empty-icon">🎐</div>
            <p>挑选一个知识点开始探索吧喵~</p>
          </div>
        </div>
      </main>

      <aside class="wiki-aside-right">
        <div class="toc-sticky">
          <div class="toc-title">ON THIS PAGE</div>
          <div v-for="item in toc" :key="item.id" 
               :class="['toc-item', `l${item.level}`]" 
               @click="scrollTo(item.id)">
            {{ item.text }}
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.wiki-page { background: var(--bg-main); transition: 0.3s; }
.wiki-layout { display: grid; grid-template-columns: 280px 1fr 240px; height: 100vh; padding-top: 60px; }

/* 搜索下拉适配 */
.search-dropdown { position: absolute; top: 45px; right: 0; width: 320px; max-height: 400px; overflow-y: auto; z-index: 1100; padding: 10px; }
.search-res-item { padding: 12px; border-radius: 10px; cursor: pointer; transition: 0.2s; }
.search-res-item:hover { background: var(--tab-active-bg); }
.res-title { font-weight: bold; color: var(--mtf-pink); font-size: 0.9rem; }
.res-snippet { font-size: 0.75rem; color: var(--text-dim); }

/* 左侧树 */
.wiki-aside-left { background: var(--bg-main); border-right: 1px solid var(--border-color); padding: 30px 20px; overflow-y: auto; }
.node-item { padding: 10px 15px; cursor: pointer; border-radius: 10px; font-size: 0.9rem; color: var(--text-dim); transition: 0.3s; margin-bottom: 4px; }
.node-item:hover { color: var(--mtf-blue); background: var(--search-bg); }
.node-item.active { background: var(--tab-active-bg); color: var(--mtf-pink); font-weight: bold; }
.level-1 { font-weight: bold; color: var(--text-main); }
.level-2 { margin-left: 18px; }

/* 中间内容 */
.wiki-main { overflow-y: auto; padding: 40px; scroll-behavior: smooth; }
.glass-paper { max-width: 850px; margin: 0 auto; background: var(--card-bg); padding: 50px; border-radius: 25px; border: 1px solid var(--border-color); box-shadow: 0 10px 30px rgba(0,0,0,0.02); }
.wiki-empty { text-align: center; margin-top: 150px; color: var(--text-dim); }
.empty-icon { font-size: 4rem; margin-bottom: 20px; opacity: 0.5; }

/* 右侧目录 */
.wiki-aside-right { padding: 40px 20px; border-left: 1px solid var(--border-color); }
.toc-sticky { position: sticky; top: 100px; }
.toc-title { font-size: 0.7rem; color: var(--mtf-lavender); font-weight: 900; letter-spacing: 1.5px; margin-bottom: 20px; }
.toc-item { font-size: 0.85rem; color: var(--text-dim); cursor: pointer; padding: 6px 0; transition: 0.2s; border-left: 2px solid transparent; padding-left: 15px; }
.toc-item:hover { color: var(--mtf-blue); }
.l1, .l2 { font-weight: 600; }
.l3 { padding-left: 25px; font-size: 0.8rem; }

@media (max-width: 1100px) {
  .wiki-layout { grid-template-columns: 240px 1fr; }
  .wiki-aside-right { display: none; }
}
@media (max-width: 768px) {
  .wiki-layout { display: block; }
  .wiki-aside-left { display: none; }
}
</style>