import { createRouter, createWebHistory } from 'vue-router'

// 基础页面可以静态导入
import Home from '../views/Home.vue' 

const routes = [
  { 
    path: '/', 
    name: 'Home',
    component: Home 
  },
  { 
    path: '/post/:id', 
    name: 'PostDetail',
    // 懒加载：只有访问到这个页面时才加载对应的 JS
    component: () => import('../views/PostDetail.vue') 
  },
  { 
    path: '/wiki', 
    name: 'Wiki',
    component: () => import('../views/Wiki.vue') 
  },
  { 
    path: '/contact', 
    name: 'Contact',
    component: () => import('../views/Contact.vue') 
  },
  { 
    path: '/messages', // 这是咱们新做的邮件留言板
    name: 'Messages',
    component: () => import('../views/MessageBoard.vue') 
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  // 切换页面时自动回到顶部
  scrollBehavior() {
    return { top: 0 }
  }
})