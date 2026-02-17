import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue' 
import PostDetail from '../views/PostDetail.vue'
import Wiki from '../views/Wiki.vue'
import Contact from '../views/Contact.vue' // 新增

const routes = [
  { path: '/', component: Home },
  { path: '/post/:id', component: PostDetail },
  { path: '/wiki', component: Wiki },
  { path: '/contact', component: Contact } // 新增
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})