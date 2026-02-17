import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import PostDetail from '../views/PostDetail.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/post/:id', name: 'Detail', component: PostDetail }
]

export const router = createRouter({
  history: createWebHistory(),
  routes
})